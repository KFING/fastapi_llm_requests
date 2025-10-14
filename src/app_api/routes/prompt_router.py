import logging

from fastapi import APIRouter, Depends
from redis.asyncio import Redis

from src.app_api.dependencies import get_redis_db_main
from src.app_api.middlewares import get_log_extra
from src.app_api.models.request_models.request_info import (
    ModifiedPromptParametersApiMdl,
    PromptRequestApiMdl,
)
from src.app_api.models.response_models.response_info import (
    ResponsePromptApiMdl,
)
from src.service_llm import llm_manager

logger = logging.getLogger(__name__)


prompt_router = APIRouter(
    tags=["prompt router"],
)


@prompt_router.post("/create_prompt/{prompt_id}")
async def create_prompt(
    prompt_parameters: PromptRequestApiMdl,
    redis: Redis = Depends(get_redis_db_main),
    log_extra: dict[str, str] = Depends(get_log_extra),
) -> None:
    await llm_manager.create_prompt(prompt_parameters, redis, log_extra=log_extra)


@prompt_router.get("/get_prompt/{prompt_id}")
async def get_prompt(
    prompt_id: int,
    redis: Redis = Depends(get_redis_db_main),
    log_extra: dict[str, str] = Depends(get_log_extra),
) -> list[ResponsePromptApiMdl]:
    return [
        i async for i in llm_manager.get_prompt(prompt_id, redis, log_extra=log_extra)
    ]


@prompt_router.patch("/modify_prompt/{prompt_id}")
async def modify_prompt(
    modify_parameters: ModifiedPromptParametersApiMdl,
    redis: Redis = Depends(get_redis_db_main),
    log_extra: dict[str, str] = Depends(get_log_extra),
) -> None:
    await llm_manager.modify_prompt(modify_parameters, redis, log_extra=log_extra)


"""@parser_router.get("/progress_parser")
async def get_progress(info_parsing_parameters: LLMParametersApiMdl, log_extra: dict[str, str] = Depends(get_log_extra)) -> None:
    await scrapy_manager.get_progress_parsing(info_parsing_parameters, log_extra=log_extra)


@parser_router.patch("/change_parser")
async def change_params_parser(parsing_parameters: LLMParametersApiMdl) -> None:
    await scrapy_manager.change_params_parsing(parsing_parameters)"""
