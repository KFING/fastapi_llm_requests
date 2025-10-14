from enum import Enum, StrEnum, unique

from pydantic import BaseModel


@unique
class Source(Enum):
    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"
    TELEGRAM = "telegram"


@unique
class Lang(Enum):
    EN = "en"
    RU = "ru"


class Provider(StrEnum):
    openai = "openai"
    deepseek = "deepseek"
    gemini = "gemini"
    claude = "claude"


class MediaFormat(StrEnum):
    MP3 = "mp3"
    MP4 = "mp4"
    WEBM = "webm"
    JPG = "jpg"
    JPEG = "jpeg"
    PNG = "png"
    DOCX = "docx"
    TXT = "txt"
    PDF = "pdf"
    DOC = "doc"
    OTHER_FORMAT = "other_format"


class MediaResolution(StrEnum):
    AUDIO_ONLY = "audio only"
    OTHER_RESOLUTION = "other_format"


class Exclude(BaseModel):
    exception: str
    exceptions_list: list[str]
    # ["some workds 1:1 as in text", "yet onother"]


class Prompt(BaseModel):
    prompt_id: int
    version: str
    prompt_template: str

    def get_prompt(self, text: str, context: str, exclude: str, lang_abbr: str) -> str:
        return f"{self.prompt_template.format(lang_abbr=lang_abbr, text=text, context=context, exclude=exclude)}"
