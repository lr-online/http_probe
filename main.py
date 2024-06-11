import os
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, Response
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
    path = request.url.path
    headers = dict(request.headers)
    headers["host"] = TARGET_URL.replace("http://", "").replace("https://", "")

    body = await request.body()

    # version 1: works
    # response = await client.request(
    #     method=method,
    #     url=TARGET_URL + path,
    #     headers=headers,
    #     content=body,
    # )
    # return Response(
    #     content=response.content,
    #     status_code=response.status_code,
    #     headers=response.headers,
    # )

    # version 2: works
    # async with client.stream(
    #         method=method,
    #         url=TARGET_URL + path,
    #         headers=headers,
    #         content=body,
    # ) as response:
    #     response_content = ""
    #     async for chunk in response.aiter_text():
    #         response_content += chunk
    #
    #     return StreamingResponse(
    #         content=response_content,
    #         status_code=response.status_code,
    #         headers=response.headers,
    #     )

    # version 3: not working
    async with client.stream(
            method=method,
            url=TARGET_URL + path,
            headers=headers,
            content=body,
    ) as response:
        return StreamingResponse(
            content=response.aiter_text(),
            status_code=response.status_code,
            headers=response.headers,
        )

        # # Cache the response headers and status code
        # duration = round((time.monotonic() - start_time) * 1000, 2)
        #
        # log_data = {
        #     "timestamp": datetime.now().isoformat(),
        #     "method": method,
        #     "url": path,
        #     "request_headers": headers,
        #     "request_body": body.decode() if body else "",
        #     "response_headers": response_headers,
        #     "response_body": "[streaming content]",
        #     "duration_ms": duration,
        # }
        #
        # # Log asynchronously
        # log_executor.submit(logger.info, log_data)


@app.on_event("shutdown")
async def shutdown_event():
    await client.aclose()
    log_executor.shutdown()
