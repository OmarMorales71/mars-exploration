import os
from crewai import LLM

_llm_instance: LLM | None = None

def get_llm() -> LLM:
    global _llm_instance

    if _llm_instance is None:
        provider = os.getenv("LLM_PROVIDER", "ollama")
        model = os.getenv("LLM_MODEL", "llama3.1")
        base_url = os.getenv("LLM_BASE_URL", "http://localhost:11434")

        _llm_instance = LLM(
            model=f"{provider}/{model}",
            base_url=base_url,
        )

    return _llm_instance

