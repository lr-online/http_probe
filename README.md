# HTTP Probe

HTTP Probe is a FastAPI-based application designed to act as a proxy server, logging HTTP request and response details asynchronously without blocking the main processing thread. This project leverages FastAPI for high-performance HTTP handling and Loguru for efficient logging.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
  - [Running Locally](#running-locally)
  - [Running with Docker](#running-with-docker)
- [Environment Variables](#environment-variables)
- [Logging](#logging)
- [License](#license)

## Features

- Asynchronous request and response logging using Loguru.
- Supports streaming responses from target URLs.
- Dockerized for easy deployment.
- Configurable using environment variables.
- Efficient logging to avoid blocking main thread execution.

## Requirements

- Python 3.12 or later
- Docker (optional, for containerized deployment)

## Installation

### Running Locally

1. **Clone the repository:**

   ```bash
   git clone https://github.com/lr-online/http_probe
   cd http_probe
   ```

2. **Create a virtual environment and activate it:**

   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install the required dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up the environment variables:**

   Create a `.env` file in the project root and add your environment variables. For example:

   ```env
   TARGET_URL=http://example.com
   ```

5. **Run the application:**

   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8005
   ```

### Running with Docker

1. **Build the Docker image:**

   ```bash
   docker build -t http_probe .
   ```

2. **Run the Docker container:**

   ```bash
   docker run -d --name http_probe -p 8005:8005 --env-file .env -v $(pwd)/logs:/app/logs http_probe
   ```

Alternatively, you can use Docker Compose for easier management:

1. **Build and run with Docker Compose:**

   ```bash
   docker-compose up --build
   ```

### Running with Shell Script

1. **Use the provided `run.sh` script to pull the latest changes, build, and run the Docker container:**

   ```bash
   ./run.sh
   ```

   This script will:
   - Pull the latest changes from the repository
   - Build and run the Docker container using Docker Compose
   - Prune unused Docker objects to free up space
   - Tail the logs of the running containers

## Environment Variables

The following environment variables can be configured:

- `TARGET_URL`: The target URL to which the proxy will forward requests.

## Logging

Logs are stored in the `logs` directory with a rotation policy of 100 MB per log file and retention of 10 days. Log entries include details such as timestamps, HTTP methods, request and response headers, bodies, and the duration of each request in milliseconds.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

---

Feel free to contribute to this project by opening issues or submitting pull requests on GitHub. If you have any questions or need further assistance, please contact [liangrui.online@gmail.com](mailto:liangrui.online@gmail.com).