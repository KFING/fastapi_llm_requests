from datetime import datetime

from pydantic import BaseModel

from src.dto.feed_rec_info import FeedRecPostFull, TmpListFeedRecPostShort


class Provider(BaseModel):
    openai = "openai"
    deepseek = "deepseek"
    gemini = "gemini"
    claude = "claude"


class ResponseLLMApiMdl(BaseModel):
    translations: list[str]
    error: str
    provider: Provider
    created_at: datetime

