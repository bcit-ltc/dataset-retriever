import json
import os
import requests
import zipfile
from django.conf import settings
from celery import shared_task
from celery.utils.log import get_task_logger
from smbclient import open_file, register_session, stat, remove
from smbclient.shutil import copyfileobj
from django.core.cache import cache

loggercelery = get_task_logger(__name__)

def register_network_session():
    try:
        # loggercelery.info(f"Registering session with server: {settings.NETWORK_DRIVE_SERVER}, username: {settings.NETWORK_DRIVE_USERNAME}")
        register_session(
            settings.NETWORK_DRIVE_SERVER,
            username=settings.NETWORK_DRIVE_USERNAME,
            password=settings.NETWORK_DRIVE_PASSWORD
        )
    except ConnectionError as e:
        loggercelery.error(f"Failed to connect: {e}")
        raise

def fetch_datahub_data(headers):
    try:
        datahub_response = requests.get(settings.BDS_API_URL, headers=headers)
        datahub_response.raise_for_status()
        # loggercelery.info(f"Successfully fetched data from {settings.BDS_API_URL}")
        return datahub_response.json()
    except requests.exceptions.RequestException as e:
        loggercelery.error(f"Request to {settings.BDS_API_URL} failed: {e}")
        return None
    except json.JSONDecodeError:
        loggercelery.error(f"Error decoding JSON from the response from {settings.BDS_API_URL}")
        return None

def filter_objects(datahub_data, filter_names, object_type):
    return [obj for obj in datahub_data['Objects'] if obj[object_type]['Name'] in filter_names]

def process_datasets(filtered_objects, object_type):
    datasets = []
    for obj in filtered_objects:
        name = obj[object_type]['Name'].replace(" ", "")
        extracts_link = obj[object_type]['ExtractsLink']
        datasets.append({'Name': name, 'ExtractsLink': extracts_link})
    return datasets

def save_zip_file(url, headers, remote_path):
    try:
        with requests.get(url, headers=headers, stream=True) as r:
            r.raise_for_status()
            with open_file(remote_path, mode="wb") as remote_file:
                for chunk in r.iter_content(chunk_size=8192):
                    remote_file.write(chunk)
        loggercelery.info(f"Successfully uploaded to {remote_path}")
    except requests.exceptions.HTTPError as http_err:
        if http_err.response.status_code == 403:
            loggercelery.error(f"Failed to save zip file to {remote_path}: 403 Forbidden - {http_err}")
            raise Exception(f"403 Forbidden error while saving remote file to {remote_path}")
        else:
            loggercelery.error(f"HTTP error occurred: {http_err}")
            raise
    except Exception as e:
        loggercelery.error(f"Failed to save zip file to {remote_path}: {e}")
        raise

def extract_and_save_csv(zip_path, csv_path):
    try:
        with open_file(zip_path, mode="rb") as remote_file:
            with zipfile.ZipFile(remote_file) as zip_ref:
                for file_info in zip_ref.infolist():
                    if file_info.filename.endswith('.csv'):
                        with zip_ref.open(file_info.filename) as csv_file:
                            with open_file(csv_path, mode="wb") as remote_csv_file:
                                copyfileobj(csv_file, remote_csv_file)
                        loggercelery.info(f"Successfully extracted and uploaded {csv_path}")
    except Exception as e:
        loggercelery.error(f"Failed to extract and save CSV from {zip_path} to {csv_path}: {e}")

def remove_file(path):
    try:
        remove(path)
        loggercelery.info(f"Successfully removed: {path}")
    except PermissionError:
        loggercelery.error(f"Permission denied: {path}")
    except FileNotFoundError:
        loggercelery.error(f"File not found: {path}")
    except Exception as e:
        loggercelery.error(f"Error removing file {path}: {e}")

def download_and_extract_files(datasets, headers):
    results = []
    for dataset in datasets:
        try:
            extracts_link_response = requests.get(dataset['ExtractsLink'], headers=headers)
            extracts_link_response.raise_for_status()
            extracts_link_data = extracts_link_response.json()
            for item in extracts_link_data['Objects']:
                results.append({'Name': dataset['Name'], 'BdsType': item['BdsType'], 'CreatedDate': item['CreatedDate'], 'DownloadLink': item['DownloadLink']})
                if item['BdsType'] == "Full":
                    break
        except requests.exceptions.RequestException as e:
            loggercelery.error(f"Request to {dataset['ExtractsLink']} failed: {e}")
        except json.JSONDecodeError:
            loggercelery.error(f"Error decoding JSON from the response from {dataset['ExtractsLink']}")
    
    for result in results:
        try:
            loggercelery.info(f"Processing {result['Name']} from {result['DownloadLink']}")
            date = result['CreatedDate'].replace(":", "-").replace("T", "_").split(".")[0]
            zip_file_name = f"{result['Name']}__{date}.zip"
            csv_file_name = f"{result['Name']}__{date}.csv"

            zip_upload_path = os.path.join(settings.NETWORK_DRIVE_PATH, zip_file_name)
            csv_upload_path = os.path.join(settings.NETWORK_DRIVE_PATH, csv_file_name)

            save_zip_file(result['DownloadLink'], headers, zip_upload_path)
            extract_and_save_csv(zip_upload_path, csv_upload_path)
            remove_file(zip_upload_path)
        except Exception as e:
            loggercelery.error(f"Failed to process {result['Name']} from {result['DownloadLink']}: {e}")


@shared_task(name='task1')
def retriever(arg, object_type='Full'):
    loggercelery.info(f"task1 ran arg: {arg}")

    try:
        register_network_session()
    except ConnectionError as e:
        loggercelery.error(f"Failed to connect: {e}")
        return None

    auth_token = "your_auth_token"

    headers = {
        'Authorization': f'Bearer {auth_token}'
    }
    
    datahub_data = fetch_datahub_data(headers)
    if not datahub_data:
        return None
    
    filter_names = [
        "Role Details",
        "Users",
        "Organizational Units",
        "Enrollments and Withdrawals",
    ]
    if object_type == "Differential":
        filter_names = [name + " Differential" for name in filter_names]
    
    filtered_objects = filter_objects(datahub_data, filter_names, object_type)
    if not filtered_objects:
        return None
    
    datasets = process_datasets(filtered_objects, object_type)
    if not datasets:
        return None
    
    download_and_extract_files(datasets, headers)
    
    return None