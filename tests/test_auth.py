"""
Tests pour le module d'authentification API Key.

Ces tests vérifient que l'authentification fonctionne correctement.
"""

import pytest
import os
from unittest.mock import patch
from fastapi import HTTPException

from app.middleware.auth import verify_api_key, get_api_key


class TestGetApiKey:
    """Tests pour la fonction get_api_key."""

    def test_get_api_key_returns_env_value(self):
        """Test que get_api_key retourne la valeur de la variable d'environnement."""
        os.environ["API_KEY"] = "my-test-key"
        result = get_api_key()
        assert result == "my-test-key"

    def test_get_api_key_returns_none_when_not_set(self):
        """Test que get_api_key retourne None si la variable n'est pas définie."""
        if "API_KEY" in os.environ:
            del os.environ["API_KEY"]
        result = get_api_key()
        assert result is None


class TestVerifyApiKey:
    """Tests pour la fonction verify_api_key."""

    @pytest.mark.asyncio
    async def test_verify_api_key_success(self, api_key):
        """Test qu'une clé valide passe la vérification."""
        os.environ["API_KEY"] = api_key
        result = await verify_api_key(api_key)
        assert result == api_key

    @pytest.mark.asyncio
    async def test_verify_api_key_missing_key(self, api_key):
        """Test qu'une clé manquante retourne une erreur 401."""
        os.environ["API_KEY"] = api_key
        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key(None)
        assert exc_info.value.status_code == 401
        assert "manquante" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_api_key_invalid_key(self, api_key):
        """Test qu'une clé invalide retourne une erreur 401."""
        os.environ["API_KEY"] = api_key
        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key("wrong-key")
        assert exc_info.value.status_code == 401
        assert "invalide" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_api_key_no_server_key_configured(self):
        """Test qu'une erreur 500 est retournée si aucune clé n'est configurée."""
        if "API_KEY" in os.environ:
            del os.environ["API_KEY"]
        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key("some-key")
        assert exc_info.value.status_code == 500
        assert "non configurée" in exc_info.value.detail
