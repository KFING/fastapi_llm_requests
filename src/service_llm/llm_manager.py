import logging
from datetime import datetime
from typing import AsyncIterator

from redis.asyncio import Redis

from src.app_api.models.request_models.request_info import LLMRequestParametersApiMdl, ModifiedPromptParametersApiMdl, \
    PromptRequestApiMdl
from src.app_api.models.response_models.response_info import ResponseLLMApiMdl, ResponsePromptApiMdl
from src.dto.llm_info import Provider

logger = logging.getLogger(__name__)

"""
template for prompt version: {id_prompt}v{prompt version, for example 1, 2, 3, ... }"""

async def create_query(llm_query_params: LLMRequestParametersApiMdl, provider: Provider, cache_key: str, lang_abbr: str,  log_extra: dict[str, str]) -> ResponseLLMApiMdl:
    rds = Redis(host="redis", port=6379)
    pass

async def create_prompt(prompt_parameters: PromptRequestApiMdl,  log_extra: dict[str, str]) -> None:
    rds = Redis(host="redis", port=6379)
    prompt_version = f"{prompt_parameters.prompt_id}v0"
    await rds.hset(f"{prompt_parameters.prompt_id}", prompt_version, prompt_parameters.prompt_template)
    logger.debug(f"create_prompt :: success created prompt id: {prompt_parameters.prompt_id} version: {prompt_version} -- {datetime.now()}", extra=log_extra)

async def get_prompt(prompt_id: int,  log_extra: dict[str, str]) -> AsyncIterator[ResponsePromptApiMdl]:
    rds = Redis(host="redis", port=6379)
    async for key in rds.hscan_iter(f'{prompt_id}', no_values=True):
        yield ResponsePromptApiMdl(prompt_version=key, prompt_template=rds.hget(f'{prompt_id}', key))

async def modify_prompt(modify_parameters: ModifiedPromptParametersApiMdl,  log_extra: dict[str, str]) -> None:
    rds = Redis(host="redis", port=6379)
    prompt_version = f"{modify_parameters.prompt_id}v-1"
    async for key in rds.hscan_iter(f'{modify_parameters.prompt_id}', no_values=True):
        prompt_version = key
    prompt_id, version_id = prompt_version.split("v")
    prompt_version = f"{prompt_id}v{version_id + 1}"
    await rds.hset(f"{modify_parameters.prompt_id}", prompt_version, modify_parameters.prompt_template)
    logger.debug(
        f"create_prompt :: success created prompt_id: {modify_parameters.prompt_id} version: {prompt_version} -- {datetime.now()}",
        extra=log_extra)

