import io
import json
import os
import zipfile
from celery import shared_task
from celery.utils.log import get_task_logger
from dotenv import load_dotenv
from smbclient import link, open_file, register_session
from smbclient.shutil import copyfile, copyfileobj

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
    local_zip_file = 'app/test/Grade Results Differential.zip'
    csv_filename_in_zip = "grade-results-differential__2024-11-15_07-06-16.csv"
    remote_csv_path = smb_path + r"\grade-results-differential__2024-11-15_07-06-19.csv"

    try:
        # Unzip the file and get the CSV file-like object
        with zipfile.ZipFile(local_zip_file, 'r') as zip_ref:
            for file_info in zip_ref.infolist():
                if file_info.filename.endswith('.csv'):
                    with zip_ref.open(file_info.filename) as csv_file:
                        # Write the CSV file-like object to the remote file
                        with open_file(remote_csv_path, mode="wb") as remote_file:
                            copyfileobj(csv_file, remote_file)
                    break  # Exit the loop after processing the first CSV file

        loggercelery.info(f"Successfully uploaded {csv_filename_in_zip} to {remote_csv_path}")
    except Exception as e:
        loggercelery.error(f"Failed to upload file: {e}")
        print(f"Failed to upload file: {e}")
    return None
    
    
    
    # try:
    #     # Copy the local CSV file to the remote path
    #     copyfile(local_csv_path, remote_csv_path)
    #     loggercelery.info(f"Successfully uploaded {local_csv_path} to {remote_csv_path}")
    # except Exception as e:
    #     loggercelery.error(f"Failed to upload file: {e}")
    #     print(f"Failed to upload file: {e}")
    # return None

    # try:
    #     with open_file(smb_path + r"\kyle-was-here.md", username=username, password=password) as f:
    #         loggercelery.info(f.read())
    #         print(f.read())
    # except Exception as e:
    #     loggercelery.error(f"Failed to read file: {e}")
    #     print(f"Failed to read file: {e}")
    # loggercelery.info(f"task2 completed with arg: {arg}")
    # return None


    # try:
    #     with open_file(smb_path + r"\kyle-was-here.md", mode="rb") as f:
    #         loggercelery.info(f.read())
    #         print(f.read())
    # except Exception as e:
    #     loggercelery.error(f"Failed to read file: {e}")
    #     print(f"Failed to read file: {e}")
    # loggercelery.info(f"task2 completed with arg: {arg}")
    # return None

@shared_task(name='task2')
def task2(arg):

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

    fileLocation3 = 'app/test/Grade Results Differential.zip'
    for result in results:

        try:
            date = result['CreatedDate'].replace(":", "-").replace("T", "_").split(".")[0]
            file_name = f"{differential['Name']}__{date}.csv"

            # TODO: Fetch the zip file from result['DownloadLink']
            # zip_response = requests.get(result['DownloadLink'])

            # zip_file = zipfile.ZipFile(io.BytesIO(zip_response.content))
            # csv_file_name = zip_file.namelist()[0]
            # file_content = zip_file.read(csv_file_name)

            # Open the zip file from the file path
            with open(fileLocation3, 'rb') as f:
                zip_file = zipfile.ZipFile(io.BytesIO(f.read()))
                csv_file_name = zip_file.namelist()[0]
                file_content = zip_file.read(csv_file_name)

                # Save file content to 'app/test' directory
                with open(f"app/test/{file_name}", "wb") as f_out:
                    f_out.write(file_content)
                    loggercelery.info(f"File saved: {file_name}")

            # upload_response = requests.post(
            #     "https://your-shared-folder-upload-url",
            #     files={"file": (file_name, file_content)},
            #     headers={"Content-Disposition": f'attachment; filename="{file_name}"'}
            # )

            # if upload_response.status_code != 200:
            #     raise Exception("Failed to upload file")

            
        except Exception as e:
            loggercelery.error(f"Failed to process {differential['Name']} from {differential['ExtractsLink']}: {e}")
            results.append({**differential, 'error': "Failed to process latest extract"})
    
    
    # """Fetch data from an external endpoint and process it."""
    # endpoint = "https://animechan.io/api/v1/quotes/random"
    # headers = {
    #     "Authorization": "Bearer YOUR_ACCESS_TOKEN",  # If needed
    #     "Content-Type": "application/json",
    # }

    # try:
    #     # Perform the GET request
    #     response = requests.get(endpoint, headers=headers, timeout=10)

    #     # Check if the request was successful
    #     if response.status_code == 200:
    #         data = response.json()  # Parse the JSON response
    #         print("Data fetched successfully:", data)
    #         loggercelery.info(f"Data fetched successfully: {data}")
    #         # Process the data (e.g., store it in the database)
    #         return data
    #     else:
    #         print(f"Failed to fetch data. Status code: {response.status_code}")
    #         print(f"Error: {response.text}")
    #         loggercelery.info(f"Failed to fetch data. Status code: {response.status_code}")
    #         loggercelery.info(f"Error: {response.text}")
    #         return None
    # except requests.exceptions.RequestException as e:
    #     print(f"An error occurred: {e}")
    #     loggercelery.info(f"An error occurred: {e}")
        # return None
