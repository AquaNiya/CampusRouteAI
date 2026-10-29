import logging
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response

from .exception_handlers import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from .routes.campus import router as campus_router
from .routes.deliveries import router as deliveries_router
from .routes.routing import router as routing_router
from .routes.tracking import router as tracking_router
from .settings import settings

logger = logging.getLogger("campusroute.api")

app = FastAPI(title="CampusRoute AI", version="1.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_exception_handler(Exception, unhandled_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)


@app.middleware("http")
async def request_logging_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    response = await call_next(request)
    logger.info(
        "api_request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
        },
    )
    return response

app.include_router(campus_router)
app.include_router(routing_router)
app.include_router(deliveries_router)
app.include_router(tracking_router)
