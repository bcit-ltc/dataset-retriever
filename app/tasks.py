from celery import shared_task
from celery.utils.log import get_task_logger
import requests
import json
import io
import zipfile

loggercelery = get_task_logger(__name__)

@shared_task(name='task1')
def cleanup(arg):
    loggercelery.info(f"task1 ran arg: {arg}")
    return None

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
