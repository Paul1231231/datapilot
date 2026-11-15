from crewai import LLM

from datapilot.config.settings import get_settings


def get_crewai_llm() -> LLM:
    settings = get_settings()

    return LLM(
        model=f"ollama/{settings.ollama_model}",
        base_url=settings.ollama_base_url,
        temperature=0,
    )