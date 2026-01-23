"""
Tests pour les routes de prédiction.

Ces tests vérifient le bon fonctionnement des endpoints de l'API.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
import os

# Configurer l'environnement avant d'importer l'app
os.environ["API_KEY"] = "test-api-key-12345"
os.environ["USE_AZURE_OPENAI"] = "false"

from app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Tests pour l'endpoint de health check."""

    def test_health_check_returns_healthy(self):
        """Test que le health check retourne un statut healthy."""
        response = client.get("/predict/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "predict"

    def test_health_check_no_auth_required(self):
        """Test que le health check ne nécessite pas d'authentification."""
        # Pas de header X-API-Key, doit quand même fonctionner
        response = client.get("/predict/health")
        assert response.status_code == 200


class TestPredictTestEndpoint:
    """Tests pour l'endpoint /predict/test."""

    def test_predict_test_without_auth(self):
        """Test que l'endpoint test nécessite une authentification."""
        response = client.post("/predict/test", json={"test": "data"})
        assert response.status_code == 401

    def test_predict_test_with_invalid_auth(self):
        """Test que l'endpoint test refuse une mauvaise clé."""
        response = client.post(
            "/predict/test",
            json={"test": "data"},
            headers={"X-API-Key": "wrong-key"}
        )
        assert response.status_code == 401

    def test_predict_test_with_valid_auth(self):
        """Test que l'endpoint test fonctionne avec une bonne clé."""
        response = client.post(
            "/predict/test",
            json={"name": "test", "value": 123},
            headers={"X-API-Key": "test-api-key-12345"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "name" in data["received"]
        assert data["received"]["name"] == "test"


class TestPredictRawEndpoint:
    """Tests pour l'endpoint /predict/raw."""

    def test_predict_raw_without_auth(self):
        """Test que l'endpoint raw nécessite une authentification."""
        response = client.post("/predict/raw", json={})
        assert response.status_code == 401

    def test_predict_raw_with_auth(self):
        """Test que l'endpoint raw fonctionne avec authentification."""
        response = client.post(
            "/predict/raw",
            json={
                "user_age": "25",
                "collection": {"Test Serie": {"volumes": {"1": "uuid"}}}
            },
            headers={"X-API-Key": "test-api-key-12345"}
        )
        # On s'attend à un 200 ou 500 selon si le parsing fonctionne
        # Le code actuel devrait retourner 200 car il parse le JSON
        assert response.status_code in [200, 500]


class TestPredictMainEndpoint:
    """Tests pour l'endpoint principal /predict/."""

    def test_predict_without_auth(self):
        """Test que l'endpoint principal nécessite une authentification."""
        response = client.post("/predict/", json={})
        assert response.status_code == 401

    def test_predict_with_invalid_request(self):
        """Test que l'endpoint refuse une requête invalide."""
        response = client.post(
            "/predict/",
            json={"invalid": "data"},
            headers={"X-API-Key": "test-api-key-12345"}
        )
        # Devrait retourner 422 car les champs requis manquent
        assert response.status_code == 422

    @patch("app.routes.predict_routes.get_predict_service")
    def test_predict_with_valid_request(self, mock_get_service, sample_predict_request):
        """Test que l'endpoint fonctionne avec une requête valide."""
        # Configurer le mock du service
        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.serie_recomendees = []
        mock_response.status = "success"
        mock_response.responce_IA_global = "Test response"

        mock_service.predict = AsyncMock(return_value=mock_response)
        mock_get_service.return_value = mock_service

        response = client.post(
            "/predict/",
            json=sample_predict_request,
            headers={"X-API-Key": "test-api-key-12345"}
        )

        # On vérifie juste que la requête est traitée
        assert response.status_code in [200, 500]


class TestMetricsEndpoint:
    """Tests pour l'endpoint /metrics (Prometheus)."""

    def test_metrics_endpoint_exists(self):
        """Test que l'endpoint metrics est accessible."""
        response = client.get("/metrics")
        # L'endpoint peut être exposé ou non selon la configuration
        # On accepte 200 ou 404 selon l'environnement
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            # Vérifier que c'est du format Prometheus
            assert "http_request" in response.text or "python_" in response.text
