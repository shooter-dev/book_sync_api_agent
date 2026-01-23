"""
Tests pour le module de configuration.

Ces tests vérifient que les paramètres sont correctement chargés.
"""

import pytest
import os
from unittest.mock import patch

from app.config.settings import (
    Settings,
    OpenAISettings,
    AzureOpenAISettings,
    DatabaseSettings,
    VectorStoreSettings,
    get_settings
)


class TestOpenAISettings:
    """Tests pour les paramètres OpenAI."""

    def test_default_model(self):
        """Test que le modèle par défaut est correct."""
        settings = OpenAISettings()
        assert settings.default_model == "gpt-4o"

    def test_default_embedding_model(self):
        """Test que le modèle d'embedding par défaut est correct."""
        settings = OpenAISettings()
        assert settings.embedding_model == "text-embedding-3-small"

    def test_default_temperature(self):
        """Test que la température par défaut est 0."""
        settings = OpenAISettings()
        assert settings.temperature == 0.0


class TestAzureOpenAISettings:
    """Tests pour les paramètres Azure OpenAI."""

    def test_api_version_from_env(self):
        """Test que la version API est lue depuis l'environnement."""
        os.environ["AZURE_OPENAI_VERSION"] = "2024-02-01"
        settings = AzureOpenAISettings()
        assert settings.api_version == "2024-02-01"

    def test_default_max_retries(self):
        """Test que le nombre de retries par défaut est 3."""
        settings = AzureOpenAISettings()
        assert settings.max_retries == 3


class TestDatabaseSettings:
    """Tests pour les paramètres de base de données."""

    def test_service_url_from_env(self):
        """Test que l'URL est lue depuis l'environnement."""
        os.environ["TIMESCALE_SERVICE_URL"] = "postgresql://test:test@localhost/db"
        settings = DatabaseSettings()
        assert "postgresql" in settings.service_url


class TestVectorStoreSettings:
    """Tests pour les paramètres du vector store."""

    def test_default_table_name(self):
        """Test que le nom de table par défaut est 'embeddings'."""
        settings = VectorStoreSettings()
        assert settings.table_name == "embeddings"

    def test_default_dimensions(self):
        """Test que les dimensions par défaut sont 3072."""
        settings = VectorStoreSettings()
        assert settings.embedding_dimensions == 3072

    def test_time_partition_interval(self):
        """Test que l'intervalle de partition est de 7 jours."""
        settings = VectorStoreSettings()
        assert settings.time_partition_interval.days == 7


class TestSettings:
    """Tests pour la classe Settings principale."""

    def test_settings_has_all_subsettings(self):
        """Test que Settings contient tous les sous-paramètres."""
        settings = Settings()
        assert hasattr(settings, "openai")
        assert hasattr(settings, "azure_openai")
        assert hasattr(settings, "database")
        assert hasattr(settings, "vector_store")

    def test_settings_openai_type(self):
        """Test que openai est du bon type."""
        settings = Settings()
        assert isinstance(settings.openai, OpenAISettings)

    def test_settings_azure_type(self):
        """Test que azure_openai est du bon type."""
        settings = Settings()
        assert isinstance(settings.azure_openai, AzureOpenAISettings)


class TestGetSettings:
    """Tests pour la fonction get_settings."""

    def test_get_settings_returns_settings(self):
        """Test que get_settings retourne une instance Settings."""
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_get_settings_cached(self):
        """Test que get_settings utilise le cache."""
        settings1 = get_settings()
        settings2 = get_settings()
        # Les deux appels doivent retourner la même instance (cache)
        assert settings1 is settings2
