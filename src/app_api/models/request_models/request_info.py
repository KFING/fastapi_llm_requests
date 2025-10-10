from datetime import datetime

from pydantic import BaseModel

from src.dto.llm_info import Source, Exclude


class LLMRequestParametersApiMdl(BaseModel):
    prompt_id: int
    text: str
    context: str
    exclude: Exclude
    variants: int


class PromptRequestApiMdl(BaseModel):
    prompt_id: int
    prompt_template: str


class ModifiedPromptParametersApiMdl(BaseModel):
    prompt_id: int
    prompt_template: str