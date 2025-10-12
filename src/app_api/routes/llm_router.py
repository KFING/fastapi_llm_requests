import logging

from fastapi import APIRouter, Depends

from src.app_api.middlewares import get_log_extra
from src.app_api.models.request_models.request_info import (
    LLMRequestParametersApiMdl,
)
from src.app_api.models.response_models.response_info import ResponseLLMApiMdl
from src.dto.llm_info import Provider
from src.service_llm import llm_manager

logger = logging.getLogger(__name__)


llm_router = APIRouter(
    tags=["llm router"],
)


@llm_router.post("/create_query/{prompt_id}/{lang_abbr}")
async def create_query(
    prompt_id: int,
    lang_abbr: str,
    provider: Provider,
    llm_query_params: LLMRequestParametersApiMdl,
    cache_key: str = "",
    log_extra: dict[str, str] = Depends(get_log_extra),
) -> ResponseLLMApiMdl:
    return await llm_manager.create_query(
        prompt_id, llm_query_params, provider, cache_key, lang_abbr, log_extra=log_extra
    )


"""@parser_router.get("/progress_parser")
async def get_progress(info_parsing_parameters: LLMParametersApiMdl, log_extra: dict[str, str] = Depends(get_log_extra)) -> None:
    await scrapy_manager.get_progress_parsing(info_parsing_parameters, log_extra=log_extra)


@parser_router.patch("/change_parser")
async def change_params_parser(parsing_parameters: LLMParametersApiMdl) -> None:
    await scrapy_manager.change_params_parsing(parsing_parameters)"""
