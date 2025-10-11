import logging
from datetime import datetime
from typing import AsyncIterator

from redis.asyncio import Redis

from src.app_api.models.request_models.request_info import LLMRequestParametersApiMdl, ModifiedPromptParametersApiMdl, \
    PromptRequestApiMdl
from src.app_api.models.response_models.response_info import ResponseLLMApiMdl, ResponsePromptApiMdl
from src.dto.llm_info import Provider, Prompt

from langchain.chains import RetrievalQA
from langchain.embeddings import CacheBackedEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.chat_models import ChatOpenAI
from langchain_community.document_loaders import JSONLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.storage import RedisStore
from langchain_community.vectorstores import Qdrant
from langchain import OpenAI

from src.env import settings

logger = logging.getLogger(__name__)

"""
template for prompt version: {id_prompt}v{version_id, for example 1, 2, 3, ... }
class ResponseLLMApiMdl(BaseModel):
    translations: list[str]
    error: str
    provider: Provider
    created_at: datetime

"""

async def deepseek_llm(prompt: str, temperature: float, provider: Provider) -> ResponseLLMApiMdl:
    llm = ChatOpenAI(
        api_key=settings.DEEPSEEK_API_KEY.get_secret_value(),
        base_url="https://api.deepseek.com/v1",
        model="deepseek-chat",
        temperature=temperature,
        max_tokens=1024,
    )
    translations = [""]
    created_at = datetime.now()
    return ResponseLLMApiMdl(
        translations=translations,
        error="",
        provider=provider,
        created_at=created_at)

async def openai_llm(prompt: str, temperature: float, provider: Provider) -> ResponseLLMApiMdl:
    llm = OpenAI(openai_api_key=settings.OPENAI_CLIENT_ID.get_secret_value(), temperature=temperature)
    translations = [""]
    created_at = datetime.now()
    return ResponseLLMApiMdl(
        translations=translations,
        error="",
        provider=provider,
        created_at=created_at)

async def create_query(prompt_id: int, llm_query_params: LLMRequestParametersApiMdl, provider: Provider, cache_key: str, lang_abbr: str,  log_extra: dict[str, str]) -> ResponseLLMApiMdl:
    rds = Redis(host="redis", port=6379)
    if cache_key:
        pass
    prompt_version = f"{prompt_id}v{llm_query_params.prompt_version_id}"
    prompt_template = await rds.hget(f"{prompt_id}", prompt_version)
    prompt = Prompt(prompt_id=prompt_id, version=prompt_version, prompt_template=prompt_template).get_prompt(llm_query_params.text, llm_query_params.context, llm_query_params.exclude)
    match provider:
        case Provider.deepseek:
            return await deepseek_llm(prompt, llm_query_params.temperature, provider)
        case _:
            return await openai_llm(prompt, llm_query_params.temperature, provider)

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

