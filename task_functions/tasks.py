import json
import os
import requests
import zipfile
from django.conf import settings
from celery import shared_task, chain
from celery.utils.log import get_task_logger
from smbclient import open_file, register_session, stat, remove
from smbclient.shutil import copyfileobj
from django.core.cache import cache
import logging
logger = logging.getLogger(__name__)

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

@shared_task(name='fetch_datahub_data_task')
def fetch_datahub_data_task(arg):
    try:
        access_token = cache.get('ACCESS_TOKEN')
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
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

@shared_task(name='filter_objects_task')
def filter_objects_task(datahub_data, filter_names, object_type):
    return [obj for obj in datahub_data['Objects'] if obj[object_type]['Name'] in filter_names]

@shared_task(name='process_datasets_task')
def process_datasets_task(filtered_objects, object_type):
    datasets = []
    for obj in filtered_objects:
        name = obj[object_type]['Name'].replace(" ", "")
        extracts_link = obj[object_type]['ExtractsLink']
        datasets.append({'Name': name, 'ExtractsLink': extracts_link})
    return datasets

def save_zip_file(url, headers, remote_path):
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(remote_path), exist_ok=True)
        
        with requests.get(url, headers=headers, stream=True) as r:
            r.raise_for_status()
            # with open_file(remote_path, mode="wb") as remote_file:
            with open(remote_path, mode="wb") as remote_file:  # Save to local file
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
        # with open_file(zip_path, mode="rb") as remote_file:
        with open(zip_path, mode="rb") as remote_file:  # Open local file
            with zipfile.ZipFile(remote_file) as zip_ref:
                for file_info in zip_ref.infolist():
                    if file_info.filename.endswith('.csv'):
                        with zip_ref.open(file_info.filename) as csv_file:
                            # with open_file(csv_path, mode="wb") as remote_csv_file:
                            with open(csv_path, mode="wb") as remote_csv_file:  # Save to local file
                                copyfileobj(csv_file, remote_csv_file)
                        loggercelery.info(f"Successfully extracted and uploaded {csv_path}")
    except Exception as e:
        loggercelery.error(f"Failed to extract and save CSV from {zip_path} to {csv_path}: {e}")

def remove_file(path):
    try:
        # remove(path)
        os.remove(path)  # Remove local file
        loggercelery.info(f"Successfully removed: {path}")
    except PermissionError:
        loggercelery.error(f"Permission denied: {path}")
    except FileNotFoundError:
        loggercelery.error(f"File not found: {path}")
    except Exception as e:
        loggercelery.error(f"Error removing file {path}: {e}")

@shared_task(name='download_and_extract_files_task')
def download_and_extract_files_task(datasets):
    results = []
    access_token = cache.get('ACCESS_TOKEN')
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
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

            # zip_upload_path = os.path.join(settings.NETWORK_DRIVE_PATH, zip_file_name)
            # csv_upload_path = os.path.join(settings.NETWORK_DRIVE_PATH, csv_file_name)
            zip_upload_path = os.path.join(settings.BASE_DIR, 'Input', zip_file_name)
            csv_upload_path = os.path.join(settings.BASE_DIR, 'Input', csv_file_name)

            save_zip_file(result['DownloadLink'], headers, zip_upload_path)
            extract_and_save_csv(zip_upload_path, csv_upload_path)
            remove_file(zip_upload_path)
        except Exception as e:
            loggercelery.error(f"Failed to process {result['Name']} from {result['DownloadLink']}: {e}")

    return None


# @shared_task(name='task1')
# def retriever(arg, object_type='Full'):
#     loggercelery.info(f"task1 ran arg: {arg}")

    # try:
    #     register_network_session()
    # except ConnectionError as e:
    #     loggercelery.error(f"Failed to connect: {e}")
    #     return None
    
    # access_token = cache.get('ACCESS_TOKEN')

    # headers = {
    #     'Authorization': f'Bearer {access_token}'
    # }
    
    # datahub_data = fetch_datahub_data(headers)
    # if not datahub_data:
    #     return None
    
    # filter_names = [
    #     "Role Details",
    #     "Users",
    #     "Organizational Units",
    #     "Enrollments and Withdrawals",
    # ]
    # if object_type == "Differential":
    #     filter_names = [name + " Differential" for name in filter_names]
    
    # filtered_objects = filter_objects(datahub_data, filter_names, object_type)
    # if not filtered_objects:
    #     return None
    
    # datasets = process_datasets(filtered_objects, object_type)
    # if not datasets:
    #     return None
    
    # download_and_extract_files(datasets, headers)
    
    # return None




@shared_task(name='renew_token')
def renew_token(arg):
    loggercelery.info(f"taska ran arg: {arg}")

    url = settings.OAUTH2_PROVIDER_TOKEN_URL
    data = {
        "refresh_token": cache.get('REFRESH_TOKEN'),
        "client_id": settings.OAUTH2_CLIENT_ID,
        "client_secret": settings.OAUTH2_CLIENT_SECRET,
        "grant_type": "refresh_token",
    }
    
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()  # Raises an error for HTTP error responses (4xx, 5xx)
        token_data = response.json()
        cache.set('ACCESS_TOKEN', token_data['access_token'])
        cache.set('REFRESH_TOKEN', token_data['refresh_token'])
        loggercelery.info(f"Successfully refreshed token")
        # loggercelery.info(f"Access token: {token_data['access_token']}")
        # loggercelery.info(f"Refresh token: {token_data['refresh_token']}")
        return None
    except requests.exceptions.RequestException as e:
        loggercelery.error(f"Failed to refresh token: {e}")
        return {"error": str(e)}


# @shared_task(name='register_network_session2')
# def register_network_session2(arg):
#     loggercelery.info(f"register_network_session2 ran arg: {arg}")
#     raise Exception("register_network_session2 failed")
    # return "taskb return"

# @shared_task(name='taskc')
# def taskc(arg):
#     loggercelery.info(f"taskc ran arg: {arg}")
#     return "taskc return"

# @shared_task(name='taskd')
# def taskd(arg):
#     loggercelery.info(f"taskd ran: {arg}")
#     return "taskd return"

@shared_task(name='execute_sequential_tasks')
def execute_sequential_tasks(arg):
    loggercelery.info(f"execute_sequential_tasks ran arg: {arg}")
    
    
    filter_names = [
        "Role Details",
        "Users",
        "Organizational Units",
        "Enrollments and Withdrawals",
    ]
    
    chain_tasks = chain(
        renew_token.s(arg),
        fetch_datahub_data_task.s(),
        filter_objects_task.s(filter_names, 'Full'),
        process_datasets_task.s('Full'),
        download_and_extract_files_task.s()
    )
    
    chain_tasks.apply_async(link_error=handle_task_failure.s())
    return None

@shared_task(name='handle_task_failure')
def handle_task_failure(task_id):
    loggercelery.error(f"Task failed: {task_id}")
    return None