import os
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    data_store_url: str = os.getenv("DATA_STORE_URL", "http://localhost:8001")

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
