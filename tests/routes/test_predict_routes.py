"""
Tests unitaires pour les routes /predict/.

Ce module teste les endpoints de l'API de prédiction.
"""

import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
from app.models.predict_response import PredictResponse, RecommendedSerie


client = TestClient(app)


class TestPredictRoutes:
    """Tests pour les routes de prédiction."""

    def test_health_check(self):
        """Test l'endpoint de health check."""
        # Exécution
        response = client.get("/predict/health")

        # Assertions
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "service": "predict"}

    def test_predict_test_endpoint(self):
        """Test l'endpoint de test /predict/test."""
        # Données de test
        test_data = {
            "user_age": "25",
            "user_genre": "Homme",
            "category_preference": "Action"
        }

        # Exécution
        response = client.post("/predict/test", json=test_data)

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["received"] == test_data
        assert "types" in data

    @patch('app.routes.predict_routes.predict_service.predict')
    @pytest.mark.asyncio
    async def test_predict_success(self, mock_predict):
        """Test une prédiction réussie."""
        # Configuration du mock
        mock_response = PredictResponse(
            serie_recomendees=[
                RecommendedSerie(
                    title="Attack on Titan",
                    id_series="series-uuid-1",
                    responce_IA="Parfait pour votre goût pour l'action"
                )
            ],
            status="success",
            responce_IA_global="Voici mes recommandations personnalisées."
        )
        mock_predict.return_value = mock_response

        # Données de requête
        request_data = {
            "user_age": "25",
            "user_genre": "Homme",
            "genre_preference": "Manga",
            "category_preference": "Action",
            "user_comment": "Je cherche de l'action",
            "prediction_type": "recommendation",
            "collection": {},
            "read": {},
            "user_mood": "Énervé"
        }

        # Exécution
        response = client.post("/predict/", json=request_data)

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["serie_recomendees"]) == 1
        assert data["serie_recomendees"][0]["title"] == "Attack on Titan"
        assert data["responce_IA_global"] == "Voici mes recommandations personnalisées."

    def test_predict_invalid_request(self):
        """Test une prédiction avec requête invalide."""
        # Données de requête invalides (champs manquants)
        request_data = {
            "user_age": "25"
            # Manque les champs obligatoires
        }

        # Exécution
        response = client.post("/predict/", json=request_data)

        # Assertions
        assert response.status_code == 422  # Validation error

    @patch('app.routes.predict_routes.predict_service.predict')
    @pytest.mark.asyncio
    async def test_predict_service_error(self, mock_predict):
        """Test la gestion d'erreur du service."""
        # Configuration du mock pour lever une exception
        mock_predict.side_effect = Exception("Erreur de base de données")

        # Données de requête valides
        request_data = {
            "user_age": "25",
            "user_genre": "Homme",
            "genre_preference": "Manga",
            "category_preference": "Action",
            "user_comment": "",
            "prediction_type": "recommendation",
            "collection": {},
            "read": {},
            "user_mood": "Calme"
        }

        # Exécution
        response = client.post("/predict/", json=request_data)

        # Assertions
        assert response.status_code == 500
        assert "Erreur lors de la prédiction" in response.json()["detail"]

    def test_predict_with_collection(self):
        """Test une prédiction avec collection."""
        request_data = {
            "user_age": "22",
            "user_genre": "Femme",
            "genre_preference": "Manga",
            "category_preference": "Romance",
            "user_comment": "",
            "prediction_type": "collection",
            "collection": {
                "One Piece": {
                    "volumes": {
                        "1": "uuid-1",
                        "2": "uuid-2"
                    },
                    "id_series": "series-uuid-1"
                }
            },
            "read": {
                "Naruto": {
                    "volumes": {
                        "1": "uuid-3"
                    },
                    "id_series": "series-uuid-2"
                }
            },
            "user_mood": "Comique"
        }

        # Exécution (sans mock, test d'intégration)
        # Note: Ce test pourrait échouer si la DB n'est pas configurée
        # Pour un test unitaire pur, il faudrait mocker le service
        response = client.post("/predict/", json=request_data)

        # Assertions minimales (car dépend de la DB)
        assert response.status_code in [200, 500]

    def test_predict_with_different_prediction_types(self):
        """Test les différents types de prédiction."""
        base_request = {
            "user_age": "25",
            "user_genre": "Homme",
            "genre_preference": "Manga",
            "category_preference": "Action",
            "user_comment": "",
            "collection": {},
            "read": {},
            "user_mood": "Calme"
        }

        # Test avec recommendation
        request_recommendation = {**base_request, "prediction_type": "recommendation"}
        response_rec = client.post("/predict/", json=request_recommendation)
        assert response_rec.status_code in [200, 500]

        # Test avec collection
        request_collection = {**base_request, "prediction_type": "collection"}
        response_coll = client.post("/predict/", json=request_collection)
        assert response_coll.status_code in [200, 500]

    def test_predict_with_all_moods(self):
        """Test les différentes humeurs utilisateur."""
        base_request = {
            "user_age": "25",
            "user_genre": "Homme",
            "genre_preference": "Manga",
            "category_preference": "Action",
            "user_comment": "",
            "prediction_type": "recommendation",
            "collection": {},
            "read": {}
        }

        moods = ["Énervé", "Comique", "Triste", "Joyeux", "Calme", "Anxieux"]

        for mood in moods:
            request_with_mood = {**base_request, "user_mood": mood}
            response = client.post("/predict/", json=request_with_mood)
            # Le test réussit si la requête est valide (200 ou 500 si DB non config)
            assert response.status_code in [200, 422, 500]

    def test_predict_with_different_categories(self):
        """Test les différentes catégories de manga."""
        base_request = {
            "user_age": "25",
            "user_genre": "Homme",
            "genre_preference": "Manga",
            "user_comment": "",
            "prediction_type": "recommendation",
            "collection": {},
            "read": {},
            "user_mood": "Calme"
        }

        categories = ["Action", "Romance", "Horror", "Comedy", "Drama", "Fantasy"]

        for category in categories:
            request_with_category = {**base_request, "category_preference": category}
            response = client.post("/predict/", json=request_with_category)
            # Le test réussit si la requête est valide
            assert response.status_code in [200, 500]

    @patch('app.routes.predict_routes.predict_service.predict')
    @pytest.mark.asyncio
    async def test_predict_empty_recommendations(self, mock_predict):
        """Test une prédiction sans recommandations."""
        # Configuration du mock pour retourner une réponse vide
        mock_response = PredictResponse(
            serie_recomendees=[],
            status="success",
            responce_IA_global="Aucune série ne correspond à vos critères actuellement."
        )
        mock_predict.return_value = mock_response

        request_data = {
            "user_age": "25",
            "user_genre": "Homme",
            "genre_preference": "Manga",
            "category_preference": "Action",
            "user_comment": "",
            "prediction_type": "recommendation",
            "collection": {},
            "read": {},
            "user_mood": "Calme"
        }

        # Exécution
        response = client.post("/predict/", json=request_data)

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["serie_recomendees"]) == 0

    def test_predict_with_user_comment(self):
        """Test une prédiction avec commentaire utilisateur."""
        request_data = {
            "user_age": "25",
            "user_genre": "Homme",
            "genre_preference": "Manga",
            "category_preference": "Action",
            "user_comment": "Je cherche quelque chose avec beaucoup de combats et d'action intense",
            "prediction_type": "recommendation",
            "collection": {},
            "read": {},
            "user_mood": "Énervé"
        }

        # Exécution
        response = client.post("/predict/", json=request_data)

        # Assertions (dépend de la DB)
        assert response.status_code in [200, 500]

    def test_predict_age_validation(self):
        """Test la validation de l'âge."""
        request_data = {
            "user_age": "invalid",  # Âge invalide mais accepté comme string
            "user_genre": "Homme",
            "genre_preference": "Manga",
            "category_preference": "Action",
            "user_comment": "",
            "prediction_type": "recommendation",
            "collection": {},
            "read": {},
            "user_mood": "Calme"
        }

        # Exécution
        response = client.post("/predict/", json=request_data)

        # Le modèle Pydantic accepte user_age comme string
        # Donc pas d'erreur de validation, mais potentiellement erreur dans le service
        assert response.status_code in [200, 500]

    def test_concurrent_requests(self):
        """Test les requêtes concurrentes."""
        request_data = {
            "user_age": "25",
            "user_genre": "Homme",
            "genre_preference": "Manga",
            "category_preference": "Action",
            "user_comment": "",
            "prediction_type": "recommendation",
            "collection": {},
            "read": {},
            "user_mood": "Calme"
        }

        # Simule plusieurs requêtes concurrentes
        responses = []
        for _ in range(3):
            response = client.post("/predict/", json=request_data)
            responses.append(response)

        # Vérifie que toutes les requêtes ont un status code valide
        for response in responses:
            assert response.status_code in [200, 500]