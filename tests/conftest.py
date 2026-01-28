"""
Configuration des fixtures pytest pour les tests.

Ce module définit les fixtures partagées entre tous les tests.
"""

import pytest
import os
from unittest.mock import MagicMock, patch


# Définir les variables d'environnement pour les tests
@pytest.fixture(autouse=True)
def setup_test_env():
    """Configure les variables d'environnement pour les tests."""
    os.environ["API_KEY"] = "test-api-key-12345"
    os.environ["USE_AZURE_OPENAI"] = "false"
    os.environ["OPENAI_API_KEY"] = "test-openai-key"
    os.environ["TIMESCALE_SERVICE_URL"] = "postgresql://test:test@localhost:5432/test"
    yield
    # Nettoyage optionnel après les tests


@pytest.fixture
def api_key():
    """Retourne la clé API de test."""
    return "test-api-key-12345"


@pytest.fixture
def invalid_api_key():
    """Retourne une clé API invalide."""
    return "invalid-key"


@pytest.fixture
def sample_predict_request():
    """Retourne un exemple de requête de prédiction."""
    return {
        "user_age": "25",
        "user_genre": "Homme",
        "genre_preference": "Global Manga",
        "category_preference": "Action",
        "user_comment": "",
        "prediction_type": "recommendation",
        "collection": {
            "Hunter X Hunter": {
                "volumes": {"1": "uuid-1", "2": "uuid-2"},
                "id_series": "series-uuid-1"
            }
        },
        "read": {
            "One Piece": {
                "volumes": {"1": "uuid-3"},
                "id_series": "series-uuid-2"
            }
        },
        "user_mood": "Action"
    }


@pytest.fixture
def sample_predict_response():
    """Retourne un exemple de réponse de prédiction."""
    return {
        "serie_recomendees": [
            {
                "title": "Naruto",
                "id_series": "naruto-uuid",
                "responce_IA": "Parfait pour les fans d'action"
            }
        ],
        "status": "success",
        "responce_IA_global": "Voici vos recommandations personnalisées"
    }


@pytest.fixture
def mock_vector_store():
    """Mock du VectorStore pour les tests."""
    with patch("app.services.predict_service.VectorStore") as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_synthesizer():
    """Mock du Synthesizer pour les tests."""
    with patch("app.services.predict_service.Synthesizer") as mock:
        mock_instance = MagicMock()
        mock_instance.generate_global_response_with_metrics.return_value = (
            "Réponse test générée", 100, 60, 0.85
        )
        mock.return_value = mock_instance
        yield mock_instance
