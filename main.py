import os
import queue
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from httpx import AsyncClient, Timeout, HTTPStatusError
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

if not TARGET_URL:
    raise ValueError("TARGET_URL environment variable is not set")

# Create a thread pool for logging to avoid blocking the main thread
log_executor = ThreadPoolExecutor(max_workers=1)

client: AsyncClient | None = None


@app.on_event("startup")
async def startup_event():
    global client
    client = AsyncClient(timeout=Timeout(30), verify=False)


@app.on_event("shutdown")
async def shutdown_event():
    await client.aclose()
    log_executor.shutdown()


def write_logs(
    request: Request,
    request_headers: dict,
    request_body: bytes,
    response_headers: dict,
    response_chunk_queue: queue.Queue,
    duration: float,
):
    response_body = response_chunk_queue.get()

    log_data = {
        "timestamp": datetime.now().isoformat(),
        "method": request.method,
        "url": request.url.path,
        "request_headers": request_headers,
        "request_body": request_body.decode() if request_body else "",
        "response_headers": response_headers,
        "response_body": response_body,
        "duration_ms": duration,
    }
    logger.info(log_data)


async def aiter_response_generator(
    method: str, url: str, headers: dict, content: bytes, chunk_queue: queue.Queue
):
    try:
        async with client.stream(
            method=method,
            url=url,
            headers=headers,
            content=content,
        ) as response:
            yield response.headers, response.status_code
            response_body_chunks = []
            async for chunk in response.aiter_text():
                yield chunk
                response_body_chunks.append(chunk)
            chunk_queue.put("".join(response_body_chunks))
    except HTTPStatusError as e:
        logger.error(f"HTTP error occurred: {e}")
        chunk_queue.put("")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        chunk_queue.put("")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.monotonic()

    request_headers = dict(request.headers)
    request_headers["host"] = TARGET_URL.replace("http://", "").replace("https://", "")

    request_body = await request.body()
    chunk_queue = queue.Queue()

    generator = aiter_response_generator(
        method=request.method,
        url=TARGET_URL + request.url.path,
        headers=request_headers,
        content=request_body,
        chunk_queue=chunk_queue,
    )

    response_headers, status_code = await anext(generator)
    duration = round((time.monotonic() - start_time) * 1000, 2)

    # Log asynchronously
    log_executor.submit(
        write_logs,
        request,
        request_headers,
        request_body,
        response_headers,
        chunk_queue,
        duration,
    )

    stream_response = StreamingResponse(
        generator, headers=response_headers, status_code=int(status_code)
    )
    return stream_response
