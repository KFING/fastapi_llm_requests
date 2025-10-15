import ast
import logging
import re
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


def wrap_excluded_words(text: str, exclude: list[str]) -> str:
    exclude_sorted = sorted(exclude, key=len, reverse=True)
    pattern = re.compile(r"\b(" + "|".join(map(re.escape, exclude_sorted)) + r")\b")

    def replacer(match: re.Match) -> str:
        original = match.group(0)
        return f"<keep>{original}</keep>"

    return pattern.sub(replacer, text)


def unwrap_kept_words(text: str) -> str:
    return re.sub(r"</?keep>", "", text)


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
        anthropic_api_key=settings.CLAUDE_API_KEY.get_secret_value(),
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
            response = await rds.hgetall(cache_key)  # type: ignore
            logger.debug(
                f"create_query :: cache_key is exist. response from db: {type(response)} prompt_id: {prompt_id} -- {datetime.now()}",
                extra=log_extra,
            )
            return ResponseLLMApiMdl(
                prompt_id=response[b"prompt_id"].decode("utf-8"),
                translations=ast.literal_eval(
                    response[b"translations"].decode("utf-8")
                ),
                error=response[b"error"].decode("utf-8"),
                provider=response[b"provider"].decode("utf-8"),
                created_at=response[b"created_at"].decode("utf-8"),
            )

    if not await rds.exists(str(prompt_id)):
        response = ResponseLLMApiMdl(
            prompt_id=prompt_id,
            translations=[],
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
    prompt_template = await rds.hget(f"{prompt_id}", prompt_version)  # type: ignore
    if prompt_template is None:
        return ResponseLLMApiMdl(
            prompt_id=0,
            translations=[],
            error="incorrect prompt_template",
            provider=provider,
            created_at=datetime.now(),
        )
    prompt = Prompt(
        prompt_id=prompt_id, version=prompt_version, prompt_template=prompt_template
    ).get_prompt(
        wrap_excluded_words(
            llm_query_params.text, llm_query_params.exclude.exceptions_list
        ),
        llm_query_params.context,
        llm_query_params.exclude.exception,
        lang_abbr,
    )
    logger.debug(
        f"create_query :: prompt was initialization. prompt: {type(prompt)} prompt_id: {prompt_id} -- {datetime.now()}",
        extra=log_extra,
    )

    match provider:
        case Provider.deepseek:
            llm = await _deepseek_llm(llm_query_params.temperature)
        # case Provider.claude:
        # llm = await _claude_llm(llm_query_params.temperature)  # type: ignore
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
            translations.append(unwrap_kept_words(str(llm_response.content)))
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
        await rds.hset(  # type: ignore
            cache_key,
            mapping={
                "prompt_id": response.prompt_id,
                "translations": str(response.translations),
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
    await rds.hset(  # type: ignore
        str(prompt_parameters.prompt_id),
        mapping={prompt_version: prompt_parameters.prompt_template},
    )
    logger.debug(
        f"create_prompt :: success created prompt id: {prompt_parameters.prompt_id} version: {prompt_version} -- {datetime.now()}",
        extra=log_extra,
    )


async def get_prompt(
    prompt_id: int, rds: Redis, *, log_extra: dict[str, str]
) -> AsyncIterator[ResponsePromptApiMdl]:
    async for key, value in rds.hscan_iter(f"{prompt_id}"):
        yield ResponsePromptApiMdl(prompt_version=key, prompt_template=value)


async def modify_prompt(
    modify_parameters: ModifiedPromptParametersApiMdl,
    rds: Redis,
    *,
    log_extra: dict[str, str],
) -> None:
    prompt_version = f"{modify_parameters.prompt_id}v-1"
    async for key in rds.hscan_iter(f"{modify_parameters.prompt_id}", no_values=True):
        prompt_id_k, version_id_k = key.decode("utf-8").split("v")
        prompt_id, version_id = prompt_version.split("v")
        prompt_version = (
            key.decode("utf-8") if version_id_k > version_id else prompt_version
        )
    prompt_id, version_id = prompt_version.split("v")

    prompt_version = f"{prompt_id}v{int(version_id) + 1}"
    await rds.hset(  # type: ignore
        f"{modify_parameters.prompt_id}",
        mapping={prompt_version: modify_parameters.prompt_template},
    )
    logger.debug(
        f"create_prompt :: success created prompt_id: {modify_parameters.prompt_id} version: {prompt_version} -- {datetime.now()}",
        extra=log_extra,
    )
