import json
import os
import requests
import zipfile
from django.conf import settings
from celery import shared_task
from celery.utils.log import get_task_logger
from smbclient import open_file, register_session, stat, remove
from smbclient.shutil import copyfileobj

loggercelery = get_task_logger(__name__)

def register_network_session():
    register_session(settings.NETWORK_DRIVE_SERVER, username=settings.NETWORK_DRIVE_USERNAME, password=settings.NETWORK_DRIVE_PASSWORD)

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

def download_and_extract_files(datasets, headers):
    results = []
    for dataset in datasets:
        # loggercelery.info(f"Processing {dataset['Name']} from {dataset['ExtractsLink']}")
        try:
            extracts_link_response = requests.get(dataset['ExtractsLink'], headers=headers)
            extracts_link_response.raise_for_status()
            extracts_link_data = extracts_link_response.json()
            for item in extracts_link_data['Objects']:
                # loggercelery.info(f"Processing item: {item}")
                results.append({'Name': dataset['Name'], 'BdsType': item['BdsType'], 'CreatedDate': item['CreatedDate'], 'DownloadLink': item['DownloadLink']})
                if item['BdsType'] == "Full":
                    # only process the first item for Full datasets
                    break
        except requests.exceptions.RequestException as e:
            loggercelery.error(f"Request to {dataset['ExtractsLink']} failed: {e}")
        except json.JSONDecodeError:
            loggercelery.error(f"Error decoding JSON from the response from {dataset['ExtractsLink']}")
    # loggercelery.info(f"Results: {results}")

    for result in results:
        try:
            loggercelery.info(f"Processing {result['Name']} from {result['DownloadLink']}")
            date = result['CreatedDate'].replace(":", "-").replace("T", "_").split(".")[0]
            zip_file_name = f"{result['Name']}__{date}.zip"
            csv_file_name = f"{result['Name']}__{date}.csv"

            zip_upload_path = os.path.join(settings.NETWORK_DRIVE_PATH, zip_file_name)

            response = requests.get(result['DownloadLink'], headers=headers, allow_redirects=True)
            response.raise_for_status()
            direct_url = response.url

            with requests.get(direct_url, stream=True) as r:
                r.raise_for_status()
                with open_file(zip_upload_path, mode="wb") as remote_file:
                    for chunk in r.iter_content(chunk_size=8192):
                        remote_file.write(chunk)
                loggercelery.info(f"Successfully uploaded {zip_file_name} to {zip_upload_path}")

            with open_file(zip_upload_path, mode="rb") as remote_file:
                with zipfile.ZipFile(remote_file) as zip_ref:
                    for file_info in zip_ref.infolist():
                        if file_info.filename.endswith('.csv'):
                            with zip_ref.open(file_info.filename) as csv_file:
                                csv_upload_path = os.path.join(settings.NETWORK_DRIVE_PATH, csv_file_name)
                                with open_file(csv_upload_path, mode="wb") as remote_csv_file:
                                    copyfileobj(csv_file, remote_csv_file)
                                loggercelery.info(f"Successfully extracted and uploaded {csv_file_name} to {csv_upload_path}")                              

            try:
                remove(zip_upload_path)
                loggercelery.info(f"Successfully removed: {zip_upload_path}")
            except PermissionError:
                loggercelery.error(f"Permission denied: {zip_upload_path}")
            except FileNotFoundError:
                loggercelery.error(f"File not found: {zip_upload_path}")
            except Exception as e:
                loggercelery.error(f"Error removing file {zip_upload_path}: {e}")

        except Exception as e:
            loggercelery.error(f"Failed to process {result['Name']} from {result['DownloadLink']}: {e}")

@shared_task(name='task1')
def retriever(arg, object_type='Full'):
    register_network_session()
    loggercelery.info(f"task1 ran arg: {arg}")

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

    # Use filter_names in your code
    filtered_objects = filter_objects(datahub_data, filter_names, object_type)
    datasets = process_datasets(filtered_objects, object_type)
    download_and_extract_files(datasets, headers)

    return None