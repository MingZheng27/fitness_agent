import os
import yaml
from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache

CONFIG_FILE = Path(__file__).parent.parent / "config.yaml"


def load_yaml_config() -> dict:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            return yaml.safe_load(f) or {}
    return {}


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
    llm_api_key: str = os.getenv("MINIMAX_API_KEY", "")
    llm_model: str = "MiniMax-M2.7"
    llm_temperature: float = 0.2

    # Agent
    short_term_memory_size: int = 10

    @property
    def mysql_url(self) -> str:
        return f"mysql://{self.mysql_user}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Override from YAML config
        config = load_yaml_config()
        if "mysql" in config:
            self.mysql_host = config["mysql"].get("host", self.mysql_host)
            self.mysql_port = config["mysql"].get("port", self.mysql_port)
            self.mysql_user = config["mysql"].get("user", self.mysql_user)
            self.mysql_password = config["mysql"].get("password", self.mysql_password)
            self.mysql_database = config["mysql"].get("database", self.mysql_database)
        if "chroma" in config:
            self.chroma_path = config["chroma"].get("path", self.chroma_path)
        if "llm" in config:
            self.llm_base_url = config["llm"].get("base_url", self.llm_base_url)
            api_key = config["llm"].get("api_key", "")
            if api_key:
                self.llm_api_key = api_key
            self.llm_model = config["llm"].get("model", self.llm_model)
            self.llm_temperature = config["llm"].get("temperature", self.llm_temperature)
        if "agent" in config:
            self.short_term_memory_size = config["agent"].get("short_term_memory_size", self.short_term_memory_size)


@lru_cache()
def get_settings() -> Settings:
    return Settings()