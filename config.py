from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database Configuration
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = ""
    db_user: str = ""
    db_password: str = ""

    # LLM Configuration (Transformers)
    llm_model: str = "google/gemma-2-2b-it"
    llm_device: str = "auto"  # auto, cpu, cuda
    llm_max_length: int = 2048
    llm_temperature: float = 0.7

    # Application Configuration
    debug: bool = False
    top_k: int = 5
    dialect: str = "postgresql"

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
