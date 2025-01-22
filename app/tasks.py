import io
import json
import os
import zipfile
from celery import shared_task
from celery.utils.log import get_task_logger
from dotenv import load_dotenv
from smbclient import open_file, register_session
from smbclient.shutil import copyfileobj

load_dotenv()

loggercelery = get_task_logger(__name__)
username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")
smb_server = os.getenv("SMB_SERVER")
smb_path = os.getenv("SMB_PATH")
@shared_task(name='task1')
def cleanup(arg):
    register_session(smb_server, username=username, password=password)
    loggercelery.info(f"task1 ran arg: {arg}")
    fileLocation = 'app/test/response.json'
    try:
        with open(fileLocation, 'r') as f:
            datahub_response = json.load(f)
            # loggercelery.info(f"Datahub response: {datahub_response}")
            # print("Datahub response:", datahub_response)
    except FileNotFoundError:
        print("File not found: {fileLocation}")
    except json.JSONDecodeError:
        print("Error decoding JSON from the file")

    # loggercelery.info(f"Datahub response: {datahub_response}")
    # print("Datahub response:", datahub_response)
    
    filter_names = [
        "Grade Results Differential",
        # "Enrollments and Withdrawals Differential",
        # "Another Dataset Name Differential"
    ]

    filtered_objects = [obj for obj in datahub_response['Objects'] if obj['Differential']['Name'] in filter_names]

    differentials = []
    for obj in filtered_objects:
        name = obj['Differential']['Name'].replace(" ", "-").lower()
        extracts_link = obj['Differential']['ExtractsLink']
        differentials.append({'Name': name, 'ExtractsLink': extracts_link})
    # loggercelery.info(f"differentials: {differentials}")
    # print("differentials:", differentials)
    
    results = []
    fileLocation2 = 'app/test/extracts.json'
    try:
        with open(fileLocation2, 'r') as f:
            datahub_response2 = json.load(f)
            # loggercelery.info(f"Datahub response: {datahub_response}")
            # print("Datahub response:", datahub_response)
    except FileNotFoundError:
        print("File not found: {fileLocation}")
    except json.JSONDecodeError:
        print("Error decoding JSON from the file")
    for differential in differentials:

        # TODO: Fetch the JSON from differential['ExtractsLink']
        # response = requests.get(differential['ExtractsLink'])
        # loggercelery.info(f"Datahub response2: {datahub_response2}")
        response = datahub_response2
        for item in response['Objects']:
            results.append({'name': differential['Name'], 'CreatedDate': item['CreatedDate'], 'DownloadLink': item['DownloadLink']})

    # loggercelery.info(f"results: {results}")

    for result in results:

        try:
            date = result['CreatedDate'].replace(":", "-").replace("T", "_").split(".")[0]
            

            # TODO: Fetch the zip file from result['DownloadLink']
            # zip_response = requests.get(result['DownloadLink'])

            # zip_file = zipfile.ZipFile(io.BytesIO(zip_response.content))
            # csv_file_name = zip_file.namelist()[0]
            # file_content = zip_file.read(csv_file_name)

            zip_file = 'app/test/Grade Results Differential.zip'

            try:
                # Unzip the file and get the CSV file-like object
                with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                    file_list = zip_ref.infolist()
                    num_files = len(file_list)
                    for index, file_info in enumerate(file_list):
                        if file_info.filename.endswith('.csv'):
                            with zip_ref.open(file_info.filename) as csv_file:
                                # Determine the upload path. The zip file is supposed to contain only one CSV file, but just in case there are more, we'll add an index to the file name
                                if num_files > 1:
                                    file_name = f"{differential['Name']}__{date}__{index}.csv"
                                else:
                                    file_name = f"{differential['Name']}__{date}.csv"
                                # Write the CSV file-like object to the remote file
                                upload_path = os.path.join(smb_path, file_name)
                                with open_file(upload_path, mode="wb") as remote_file:
                                    copyfileobj(csv_file, remote_file)
                            loggercelery.info(f"Successfully uploaded {file_info.filename} to {upload_path}")

            except Exception as e:
                loggercelery.error(f"Failed to upload file: {e}")
                print(f"Failed to upload file: {e}")


        except Exception as e:
            loggercelery.error(f"Failed to process {differential['Name']} from {differential['ExtractsLink']}: {e}")
            results.append({**differential, 'error': "Failed to process latest extract"})
    
    return None
    

@shared_task(name='task2')
def task2(arg):
    loggercelery.info(f"task2 ran arg: {arg}")
    return None