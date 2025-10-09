from datetime import datetime

from pydantic import BaseModel

from src.dto.feed_rec_info import Source

class Exclude(BaseModel):
    exception: str
    exception_list: list[str]
    # ["some workds 1:1 as in text", "yet onother"]

class LLMRequestParametersApiMdl(BaseModel):
    prompt_id: int
    text: str
    context: str
    exclude: Exclude
    variants: int

class ModifiedPromptParametersApiMdl(BaseModel):
    prompt_id: int
    text: str
    context: str