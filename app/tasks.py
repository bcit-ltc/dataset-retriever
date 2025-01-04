from celery import shared_task
from celery.utils.log import get_task_logger
import requests

loggercelery = get_task_logger(__name__)

@shared_task(name='task1')
def cleanup(arg):
    loggercelery.info(f"task1 ran arg: {arg}")
    return None

@shared_task(name='task2')
def task2(arg):
    """Fetch data from an external endpoint and process it."""
    endpoint = "https://animechan.io/api/v1/quotes/random"
    headers = {
        "Authorization": "Bearer YOUR_ACCESS_TOKEN",  # If needed
        "Content-Type": "application/json",
    }

    try:
        # Perform the GET request
        response = requests.get(endpoint, headers=headers, timeout=10)

        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()  # Parse the JSON response
            print("Data fetched successfully:", data)
            loggercelery.info(f"Data fetched successfully: {data}")
            # Process the data (e.g., store it in the database)
            return data
        else:
            print(f"Failed to fetch data. Status code: {response.status_code}")
            print(f"Error: {response.text}")
            loggercelery.info(f"Failed to fetch data. Status code: {response.status_code}")
            loggercelery.info(f"Error: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        loggercelery.info(f"An error occurred: {e}")
        return None

