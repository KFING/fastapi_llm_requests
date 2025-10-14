import logging
from datetime import datetime
from typing import AsyncIterator

from redis.asyncio import Redis

from src.app_api.models.request_models.request_info import (
    LLMRequestParametersApiMdl,
    ModifiedPromptParametersApiMdl,
    PromptRequestApiMdl,
)
from src.app_api.models.response_models.response_info import (
    ResponseLLMApiMdl,
    ResponsePromptApiMdl,
)
from src.dto.llm_info import Provider, Prompt

from langchain_community.chat_models import ChatOpenAI

from langchain_community.llms import OpenAI

from src.env import settings
from src.errors import fmt_err

logger = logging.getLogger(__name__)

"""
template for prompt version: {id_prompt}v{version_id, for example 1, 2, 3, ... }
class ResponseLLMApiMdl(BaseModel):
    translations: list[str]
    error: str
    provider: Provider
    created_at: datetime

"""


async def _deepseek_llm(temperature: float) -> ChatOpenAI:
    return ChatOpenAI(
        api_key=settings.DEEPSEEK_API_KEY.get_secret_value(),
        base_url="https://api.deepseek.com/v1",
        model="deepseek-chat",
        temperature=temperature,
        max_tokens=1024,
    )


async def _openai_llm(temperature: float) -> OpenAI:
    return OpenAI(
        openai_api_key=settings.OPENAI_API_KEY.get_secret_value(),
        temperature=temperature,
    )


"""async def _claude_llm(temperature: float) -> ChatAnthropic:
    return ChatAnthropic(
        model_name="claude-3-5-sonnet-20241022",
        temperature=temperature,
        timeout=0.5,
        api_key=settings.DEEPSEEK_API_KEY.get_secret_value(),
    )"""


async def create_query(
    prompt_id: int,
    llm_query_params: LLMRequestParametersApiMdl,
    provider: Provider,
    cache_key: str,
    lang_abbr: str,
    rds: Redis,
    log_extra: dict[str, str],
) -> ResponseLLMApiMdl:
    if len(cache_key) > 0:
        logger.debug(
            f"create_query :: cache_key is not none. prompt_id: {prompt_id} -- {datetime.now()}",
            extra=log_extra,
        )
        if await rds.exists(cache_key):
            response = await rds.hgetall(cache_key)
            logger.debug(
                f"create_query :: cache_key is exist. response from db: {type(response)} prompt_id: {prompt_id} -- {datetime.now()}",
                extra=log_extra,
            )
            return ResponseLLMApiMdl(
                prompt_id=response["prompt_id"],
                translations=response["translations"],
                error=response["error"],
                provider=response["provider"],
                created_at=response["created_at"],
            )
    if not await rds.exists(str(prompt_id)):
        response = ResponseLLMApiMdl(
            prompt_id=prompt_id,
            translations=[""],
            error=f"prompt does not exist with id: {prompt_id}",
            provider=provider,
            created_at=datetime.now(),
        )
        logger.warn(
            f"create_query :: prompt with id: {prompt_id} does not exist -- {datetime.now()}",
            extra=log_extra,
        )
        return response

    prompt_version = f"{prompt_id}v{llm_query_params.prompt_version_id}"
    prompt_template = await rds.hget(f"{prompt_id}", prompt_version)
    prompt = Prompt(
        prompt_id=prompt_id, version=prompt_version, prompt_template=prompt_template
    ).get_prompt(
        llm_query_params.text,
        llm_query_params.context,
        llm_query_params.exclude,
        lang_abbr,
    )
    logger.debug(
        f"create_query :: prompt was initialization. prompt: {type(prompt)} prompt_id: {prompt_id} -- {datetime.now()}",
        extra=log_extra,
    )

    match provider:
        case Provider.deepseek:
            llm = await _deepseek_llm(llm_query_params.temperature)
        #        case Provider.claude:
        #            llm = await _claude_llm(llm_query_params.temperature)
        case _:
            llm = await _openai_llm(llm_query_params.temperature)

    logger.debug(
        f"create_query :: LLM was initialization. LLM: {type(llm)} prompt_id: {prompt_id} -- {datetime.now()}",
        extra=log_extra,
    )

    translations: list[str] = []
    error: str = ""
    created_at = datetime.now()

    try:
        for i in range(0, llm_query_params.variants):
            llm_response = llm.invoke(prompt)
            translations.append(str(llm_response.content))
            logger.debug(
                f"create_query :: LLM sent response for variant: {i} and translit text. prompt_id: {prompt_id} -- {datetime.now()}",
                extra=log_extra,
            )
    except Exception as e:
        error = fmt_err(e)

    response = ResponseLLMApiMdl(
        prompt_id=prompt_id,
        translations=translations,
        error=error,
        provider=provider,
        created_at=created_at,
    )

    if len(cache_key) > 0:
        await rds.hset(
            cache_key,
            mapping={
                "prompt_id": response.prompt_id,
                "translation": str(response.translations),
                "error": response.error,
                "provider": response.provider.value,
                "created_at": str(response.created_at),
            },
        )
    return response


async def create_prompt(
    prompt_parameters: PromptRequestApiMdl, rds: Redis, *, log_extra: dict[str, str]
) -> None:
    if await rds.exists(str(prompt_parameters.prompt_id)):
        return
    prompt_version = f"{prompt_parameters.prompt_id}v0"
    await rds.hset(
        str(prompt_parameters.prompt_id),
        mapping={prompt_version: prompt_parameters.prompt_template},
    )
    logger.debug(
        f"create_prompt :: success created prompt id: {prompt_parameters.prompt_id} version: {prompt_version} -- {datetime.now()}",
        extra=log_extra,
    )


async def get_prompt(
    prompt_id: int, rds: Redis, *, log_extra: dict[str, str]
) -> AsyncIterator[ResponsePromptApiMdl]:  # dont forget about yield
    async for key, value in rds.hscan_iter(f"{prompt_id}"):
        yield ResponsePromptApiMdl(prompt_version=key, prompt_template=value)


async def modify_prompt(
    modify_parameters: ModifiedPromptParametersApiMdl, rds: Redis, *, log_extra: dict[str, str]
) -> None:
    prompt_version = f"{modify_parameters.prompt_id}v-1"
    async for key in rds.hscan_iter(f"{modify_parameters.prompt_id}", no_values=True):
        prompt_version = key
    prompt_id, version_id = prompt_version.split("v")
    prompt_version = f"{prompt_id}v{int(version_id) + 1}"
    await rds.hset(
        f"{modify_parameters.prompt_id}",
        mapping={prompt_version: modify_parameters.prompt_template},
    )
    logger.debug(
        f"create_prompt :: success created prompt_id: {modify_parameters.prompt_id} version: {prompt_version} -- {datetime.now()}",
        extra=log_extra,
    )
