from src.app_api.models.request_models.request_info import LLMRequestParametersApiMdl, ModifiedPromptParametersApiMdl
from src.app_api.models.response_models.response_info import ResponseLLMApiMdl


async def create_query(llm_query_params: LLMRequestParametersApiMdl, log_extra: dict[str, str]) -> ResponseLLMApiMdl:
    pass

async def modify_prompt(modify_parameters: ModifiedPromptParametersApiMdl) -> None:
    pass

