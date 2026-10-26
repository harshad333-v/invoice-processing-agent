import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    max_extraction_retries: int = 2
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

def load_settings() -> Settings:
    values = {}
    # Streamlit Community Cloud secrets are available via st.secrets, not automatically
    # as OS environment variables. Keep this optional so FastAPI/local runs work too.
    try:
        import streamlit as st
        for key in ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL", "MAX_EXTRACTION_RETRIES"):
            if key in st.secrets and not os.getenv(key):
                values[key.lower()] = st.secrets[key]
    except Exception:
        pass
    return Settings(**values)

settings = load_settings()
