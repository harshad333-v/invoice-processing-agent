from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    max_extraction_retries: int = 2
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
