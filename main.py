import os
import time

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import Response
from httpx import AsyncClient, Timeout
from loguru import logger

load_dotenv()

# logger.remove()
logger.add(
    "logs/record.log",
    format="{message}",
    enqueue=True,
    rotation="100 MB",
    retention="10 days",
)

app = FastAPI()
TARGET_URL = os.getenv("TARGET_URL")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    method = request.method
    headers = dict(request.headers)
    body = await request.body()

    async with AsyncClient(timeout=Timeout(300)) as client:
        response = await client.request(
            method=method,
            url=TARGET_URL + request.url.path,
            headers=headers,
            content=body,
        )

        log_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
            "method": method,
            "url": request.url.path,
            "request_headers": headers,
            "request_body": body.decode() if body else "",
            "response_headers": dict(response.headers),
            "response_body": response.text,
            "duration_ms": round((time.time() - start_time) * 1000, 2),
        }
        logger.info(log_data)

        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=response.headers,
        )
