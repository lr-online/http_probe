import os
import time

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import Response
from httpx import AsyncClient, Timeout, HTTPError, ReadTimeout
from loguru import logger

load_dotenv()

record_logger = logger.bind()

record_logger.remove()
record_logger.add(
    "logs/record.log",
    format="{message}",
    enqueue=True,
    rotation="100 MB",
    retention="10 days",
)

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    client = AsyncClient(timeout=Timeout(300.0))
    app.state.client = client


@app.middleware("http")
async def log_requests(request: Request, call_next):
    target_url = os.getenv("TARGET_URL", "https://httpbin.org")
    start_time = time.time()

    method = request.method
    headers = dict(request.headers)
    body = await request.body()

    try:
        response = await app.state.client.request(
            method=method,
            url=target_url + request.url.path,
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
        record_logger.info(log_data)

        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=response.headers,
        )
    except ReadTimeout as e:
        logger.error(f"ReadTimeout: {e}")
        return Response(content="ReadTimeout", status_code=504)
    except HTTPError as e:
        logger.error(f"HTTPError: {e}")
        return Response(content="HTTPError", status_code=500)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return Response(content="Unexpected error", status_code=500)
