from datetime import datetime

from pydantic import BaseModel

from src.dto.llm_info import Source, Exclude


class LLMRequestParametersApiMdl(BaseModel):
    prompt_version_id: str = 0
    text: str
    context: str
    exclude: Exclude
    variants: int
    temperature: int


class PromptRequestApiMdl(BaseModel):
    prompt_id: int
    prompt_template: str


class ModifiedPromptParametersApiMdl(BaseModel):
    prompt_id: int
    prompt_template: str