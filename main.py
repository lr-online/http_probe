import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
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

    headers = dict(request.headers)
    headers["host"] = TARGET_URL.replace("http://", "").replace("https://", "")

    body = await request.body()

    async def aiter_text_generator(method, url, headers, content):
        async with client.stream(
            method=method,
            url=url,
            headers=headers,
            content=content,
        ) as response:
            yield response.headers, response.status_code
            async for chunk in response.aiter_raw():
                yield chunk

    generator = aiter_text_generator(
        method=request.method,
        url=TARGET_URL + request.url.path,
        headers=headers,
        content=body,
    )

    response_headers, status_code = await anext(generator)
    duration = round((time.monotonic() - start_time) * 1000, 2)

    log_data = {
        "timestamp": datetime.now().isoformat(),
        "method": request.method,
        "url": request.url.path,
        "request_headers": headers,
        "request_body": body.decode() if body else "",
        "response_headers": response_headers,
        # "response_body": "[streaming content]",
        "duration_ms": duration,
    }

    # Log asynchronously
    log_executor.submit(logger.info, log_data)

    stream_response = StreamingResponse(
        generator, headers=response_headers, status_code=int(status_code)
    )
    return stream_response


@app.on_event("shutdown")
async def shutdown_event():
    await client.aclose()
    log_executor.shutdown()
