# global middleware
import time
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import Request, Response
from loguru import logger


csv_header = [
    "Request ID", "Datetime", "Endpoint Triggered", "Client IP Address",
    "Response Time", "Status Code", "Successful"
]

async def monitor_service(
    req: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    request_id = uuid4().hex
    request_datetime = datetime.now(timezone.utc).isoformat()
    start_time = time.perf_counter()
    response: Response = await call_next(req)
    response_time = round(time.perf_counter() - start_time, 4)
    response.headers["X-Response-Time"] = str(response_time)
    response.headers["X-API-Request-ID"] = request_id
    logger.info(
        "Request info: "
        f"Request id: {request_id}, "
        f"Request datetime: {request_datetime}, "
        f"Endpoint triggered: {req.url}, "
        f"Client IP Address: {req.client.host if req.client else 'Unknown'}, "
        f"Response time: {response_time}, "
        f"Status code: {response.status_code}, "
        f"Successful: {response.status_code < 400}"
    )
    logger.info("--------------------------------")
    return response