import logging

from fastapi import FastAPI

from src.app_api.routes.llm_router import llm_router
from src.app_api.routes.prompt_router import prompt_router
from src.app_api.middlewares import log_extra_middleware

logger = logging.getLogger(__name__)


def get_app() -> FastAPI:
    # init
    app = FastAPI()

    # routes
    app.include_router(llm_router)
    app.include_router(prompt_router)

    # middlewares
    app.middleware("http")(log_extra_middleware)

    # exception handlers
    """app.add_exception_handler(
        exc_class_or_status_code=ApiError, handler=api_error_handler
    )"""

    # other

    return app
