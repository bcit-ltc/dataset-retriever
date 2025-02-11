# Dataset Retriever
[![Course Production Pipeline CI](https://github.com/BCIT-LTC/dataset-retriever/actions/workflows/cp-pipeline-ci.yml/badge.svg?branch=main)](https://github.com/BCIT-LTC/dataset-retriever/actions/workflows/cp-pipeline-ci.yml)
[![Testing](https://github.com/BCIT-LTC/dataset-retriever/actions/workflows/testing.yml/badge.svg)](https://github.com/BCIT-LTC/dataset-retriever/actions/workflows/testing.yml)

Dataset Retriever is a Django-based application designed to fetch Brightspace dataset API and save the csv files into a shared directory. It leverages OAuth2 for authentication, Celery for task scheduling, and Redis for caching.

## Features
- OAuth2 authentication for secure access to data sources.
- Scheduled tasks using Celery to fetch and process datasets.
- Integration with SMB for storing processed datasets.
- Dockerized for easy deployment.


## Getting Started

### Prerequisites

- Docker
- Docker Compose

### Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/dataset-retriever.git
    cd dataset-retriever
    ```

2. Build and run the Docker containers:
    ```sh
    docker-compose up --build
    ```

3. Access the application at [http://localhost:9000](http://localhost:9000).

### Environment Variables

Set the following environment variables directly in the Docker Compose file:
- DEBUG
- OAUTH2_PROVIDER_AUTHORIZATION_URL
- OAUTH2_PROVIDER_TOKEN_URL
- OAUTH2_CLIENT_ID
- OAUTH2_CLIENT_SECRET
- OAUTH2_REDIRECT_URI
- OAUTH2_SCOPE
- BDS_API_URL
- NETWORK_DRIVE_USERNAME
- NETWORK_DRIVE_PASSWORD
- NETWORK_DRIVE_SERVER
- NETWORK_DRIVE_PATH
