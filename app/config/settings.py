import logging
import os
from datetime import timedelta
from functools import lru_cache
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv(dotenv_path="./.env")


def setup_logging():
    """Configure la journalisation de base pour l'application."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )


class LLMSettings(BaseModel):
    """Paramètres de base pour les configurations de modèles de langage."""

    temperature: float = 0.0
    max_tokens: Optional[int] = None
    max_retries: int = 3


class OpenAISettings(LLMSettings):
    """Paramètres spécifiques à OpenAI étendant LLMSettings."""

    api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    default_model: str = Field(default="gpt-4o")
    embedding_model: str = Field(default="text-embedding-3-small")


class AzureOpenAISettings(LLMSettings):
    """Paramètres spécifiques à Azure OpenAI étendant LLMSettings."""

    api_key: str = Field(default_factory=lambda: os.getenv("AZURE_OPENAI_KEY"))
    api_version: str = Field(default_factory=lambda: os.getenv("AZURE_OPENAI_VERSION", "2024-02-01"))
    azure_endpoint: str = Field(default_factory=lambda: os.getenv("AZURE_OPENAI_ENDPOINT"))
    default_model: str = Field(default_factory=lambda: os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4"))
    embedding_model: str = Field(default_factory=lambda: os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small"))


class DatabaseSettings(BaseModel):
    """Paramètres de connexion à la base de données."""

    service_url: str = Field(default_factory=lambda: os.getenv("TIMESCALE_SERVICE_URL"))


class VectorStoreSettings(BaseModel):
    """Paramètres pour le magasin de vecteurs."""

    table_name: str = "embeddings"
    embedding_dimensions: int = 3072
    time_partition_interval: timedelta = timedelta(days=7)


class Settings(BaseModel):
    """Classe principale de paramètres combinant tous les sous-paramètres."""

    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    azure_openai: AzureOpenAISettings = Field(default_factory=AzureOpenAISettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    vector_store: VectorStoreSettings = Field(default_factory=VectorStoreSettings)


@lru_cache()
def get_settings() -> Settings:
    """Crée et retourne une instance mise en cache des paramètres."""
    settings = Settings()
    setup_logging()
    return settings
