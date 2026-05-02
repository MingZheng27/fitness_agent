import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # MySQL
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = ""
    mysql_database: str = "fitness_agent"

    # ChromaDB
    chroma_path: str = "./chroma_data"

    # LLM
    llm_base_url: str = "https://api.minimax.chat/v1"
    llm_api_key: str = os.getenv("MINIMAX_API_KEY", "your_key")
    llm_model: str = "MiniMax-M2.7"
    llm_temperature: float = 0.2

    # Agent
    short_term_memory_size: int = 10

    @property
    def mysql_url(self) -> str:
        return f"mysql://{self.mysql_user}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"


@lru_cache()
def get_settings() -> Settings:
    return Settings()