import logging

from fastapi import APIRouter, Depends

from src.app_api.middlewares import get_log_extra
from src.app_api.models.request_models.request_info import LLMRequestParametersApiMdl, ModifiedPromptParametersApiMdl
from src.app_api.models.response_models.response_info import ResponseLLMApiMdl
from src.service_llm import llm_manager

logger = logging.getLogger(__name__)


parser_router = APIRouter(
    tags=["parser router"],
)


@parser_router.post("/create_query/{prompt_id}/{lang_abbr}")
async def create_query(llm_query_params: LLMRequestParametersApiMdl, log_extra: dict[str, str] = Depends(get_log_extra)) ->  ResponseLLMApiMdl:
    return await llm_manager.create_query(llm_query_params, log_extra=log_extra)


@parser_router.patch("/modify_query")
async def modify_query(modify_parameters: ModifiedPromptParametersApiMdl) -> None:
    await llm_manager.modify_prompt(modify_parameters)


"""@parser_router.get("/progress_parser")
async def get_progress(info_parsing_parameters: LLMParametersApiMdl, log_extra: dict[str, str] = Depends(get_log_extra)) -> None:
    await scrapy_manager.get_progress_parsing(info_parsing_parameters, log_extra=log_extra)


@parser_router.patch("/change_parser")
async def change_params_parser(parsing_parameters: LLMParametersApiMdl) -> None:
    await scrapy_manager.change_params_parsing(parsing_parameters)"""
