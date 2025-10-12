from datetime import datetime

from pydantic import BaseModel

from src.dto.llm_info import Provider


class ResponseLLMApiMdl(BaseModel):
    prompt_id: int
    translations: list[str]
    error: str
    provider: Provider
    created_at: datetime


class ResponsePromptApiMdl(BaseModel):
    prompt_template: str
    prompt_version: str
