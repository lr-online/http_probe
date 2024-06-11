import os
import time

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import Response
from httpx import AsyncClient, Timeout, ReadTimeout
from loguru import logger

load_dotenv()

# 创建一个新的logger实例
record_logger = logger.bind()

# 为这个logger实例配置一个handler，将日志信息写入到指定的文件中
record_logger.remove()
record_logger.add("logs/record.log", format="{message}", enqueue=True, rotation="1 week", retention="10 days")


app = FastAPI()


@app.on_event("startup")
async def startup_event():
    client = AsyncClient(timeout=Timeout(300.0))
    app.state.client = client


@app.middleware("http")
async def log_requests(request: Request, call_next):
    target_url = os.getenv("TARGET_URL")
    start_time = time.time()

    # 复制请求
    method = request.method
    headers = dict(request.headers)
    body = await request.body()

    # 使用 httpx 转发请求
    try:
        response = await app.state.client.request(
            method=method,
            url=target_url + request.url.path,
            headers=headers,
            content=body,
        )

        # 记录响应
        log_data = {
            "method": method,
            "url": request.url.path,
            "request_headers": headers,
            "request_body": body.decode() if body else "",
            "response_headers": dict(response.headers),
            "response_body": response.text,
            "duration": time.time() - start_time,
        }
        record_logger.info(log_data)

        # 返回响应
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=response.headers,
        )
    except ReadTimeout as e:
        logger.error(f"ReadTimeout: {e}")
        return Response(content="ReadTimeout", status_code=504)
