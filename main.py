import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import Response
from httpx import AsyncClient, Timeout
from loguru import logger

load_dotenv()

# Setup logger
logger.remove()
logger.add(
    "logs/record.log",
    format="{message}",
    enqueue=True,
    rotation="100 MB",
    retention="10 days",
)

# Create FastAPI instance
app = FastAPI()
TARGET_URL = os.getenv("TARGET_URL")

# Create a thread pool for logging to avoid blocking the main thread
log_executor = ThreadPoolExecutor(max_workers=1)

# Reuse AsyncClient instance
client = AsyncClient(timeout=Timeout(30), verify=False)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.monotonic()

    method = request.method
    headers = dict(request.headers)
    headers["host"] = TARGET_URL.replace("http://", "").replace("https://", "")

    body = await request.body()

    response = await client.request(
        method=method,
        url=TARGET_URL + request.url.path,
        headers=headers,
        content=body,
    )

    log_data = {
        "timestamp": datetime.now().isoformat(),
        "method": method,
        "url": request.url.path,
        "request_headers": headers,
        "request_body": body.decode() if body else "",
        "response_headers": dict(response.headers),
        "response_body": response.text,
        "duration_ms": round((time.monotonic() - start_time) * 1000, 2),
    }

    # Log asynchronously
    log_executor.submit(logger.info, log_data)

    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers),
    )


@app.on_event("shutdown")
async def shutdown_event():
    await client.aclose()
    log_executor.shutdown()
