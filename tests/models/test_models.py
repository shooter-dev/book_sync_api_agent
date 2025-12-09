"""
Tests unitaires pour les modèles Pydantic.

Ce module teste la validation et la sérialisation des modèles de données.
"""

import pytest
from pydantic import ValidationError
from app.models.predict_request import PredictRequest
from app.models.predict_response import PredictResponse, RecommendedSerie


class TestPredictRequest:
    """Tests pour le modèle PredictRequest."""

    def test_valid_request_minimal(self):
        """Test une requête valide avec champs minimaux."""
        # Données minimales
        request_data = {
            "user_age": "25",
            "user_genre": "Homme",
            "genre_preference": "Manga",
            "category_preference": "Action",
            "prediction_type": "recommendation",
            "user_mood": "Calme"
        }

        # Exécution
        request = PredictRequest(**request_data)

        # Assertions
        assert request.user_age == "25"
        assert request.user_genre == "Homme"
        assert request.genre_preference == "Manga"
        assert request.category_preference == "Action"
        assert request.prediction_type == "recommendation"
        assert request.user_mood == "Calme"
        assert request.user_comment == ""  # Valeur par défaut
        assert request.collection is None  # Valeur par défaut
        assert request.read is None  # Valeur par défaut

    def test_valid_request_complete(self):
        """Test une requête valide complète."""
        request_data = {
            "user_age": "25",
            "user_genre": "Homme",
            "genre_preference": "Manga",
            "category_preference": "Action",
            "user_comment": "Je cherche de l'action intense",
            "prediction_type": "collection",
            "collection": {
                "One Piece": {
                    "volumes": {"1": "uuid-1"},
                    "id_series": "series-uuid-1"
                }
            },
            "read": {
                "Naruto": {
                    "volumes": {"1": "uuid-2"},
                    "id_series": "series-uuid-2"
                }
            },
            "user_mood": "Énervé",
            "question": "Quelle série me recommandez-vous ?",
            "limit": 10,
            "metadata_filter": {"genre": "Action"}
        }

        # Exécution
        request = PredictRequest(**request_data)

        # Assertions
        assert request.user_comment == "Je cherche de l'action intense"
        assert request.prediction_type == "collection"
        assert "One Piece" in request.collection
        assert "Naruto" in request.read
        assert request.question == "Quelle série me recommandez-vous ?"
        assert request.limit == 10
        assert request.metadata_filter == {"genre": "Action"}

    def test_missing_required_fields(self):
        """Test qu'une erreur est levée si des champs obligatoires manquent."""
        # Données incomplètes
        incomplete_data = {
            "user_age": "25"
            # Manque user_genre, genre_preference, etc.
        }

        # Exécution et assertion
        with pytest.raises(ValidationError) as exc_info:
            PredictRequest(**incomplete_data)

        # Vérifie que les champs manquants sont mentionnés
        errors = exc_info.value.errors()
        error_fields = [error['loc'][0] for error in errors]
        assert 'user_genre' in error_fields
        assert 'genre_preference' in error_fields
        assert 'category_preference' in error_fields

    def test_prediction_type_validation(self):
        """Test la validation du type de prédiction."""
        base_data = {
            "user_age": "25",
            "user_genre": "Homme",
            "genre_preference": "Manga",
            "category_preference": "Action",
            "user_mood": "Calme"
        }

        # Test avec "collection"
        request_collection = PredictRequest(**{**base_data, "prediction_type": "collection"})
        assert request_collection.prediction_type == "collection"

        # Test avec "recommendation"
        request_recommendation = PredictRequest(**{**base_data, "prediction_type": "recommendation"})
        assert request_recommendation.prediction_type == "recommendation"

        # Test avec une valeur invalide
        with pytest.raises(ValidationError):
            PredictRequest(**{**base_data, "prediction_type": "invalid_type"})

    def test_limit_validation(self):
        """Test la validation de la limite."""
        base_data = {
            "user_age": "25",
            "user_genre": "Homme",
            "genre_preference": "Manga",
            "category_preference": "Action",
            "prediction_type": "recommendation",
            "user_mood": "Calme"
        }

        # Test avec limite valide
        request_valid = PredictRequest(**{**base_data, "limit": 10})
        assert request_valid.limit == 10

        # Test avec limite trop petite
        with pytest.raises(ValidationError):
            PredictRequest(**{**base_data, "limit": 0})

        # Test avec limite trop grande
        with pytest.raises(ValidationError):
            PredictRequest(**{**base_data, "limit": 25})

    def test_collection_dict_format(self):
        """Test le format dictionnaire pour collection."""
        request_data = {
            "user_age": "25",
            "user_genre": "Homme",
            "genre_preference": "Manga",
            "category_preference": "Action",
            "prediction_type": "recommendation",
            "user_mood": "Calme",
            "collection": {
                "Attack on Titan": {
                    "volumes": {"1": "uuid-1", "2": "uuid-2"},
                    "id_series": "series-uuid"
                }
            }
        }

        # Exécution
        request = PredictRequest(**request_data)

        # Assertions
        assert isinstance(request.collection, dict)
        assert "Attack on Titan" in request.collection
        assert request.collection["Attack on Titan"]["id_series"] == "series-uuid"

    def test_collection_string_format(self):
        """Test le format string pour collection."""
        request_data = {
            "user_age": "25",
            "user_genre": "Homme",
            "genre_preference": "Manga",
            "category_preference": "Action",
            "prediction_type": "recommendation",
            "user_mood": "Calme",
            "collection": "{}"
        }

        # Exécution
        request = PredictRequest(**request_data)

        # Assertions
        assert isinstance(request.collection, str)
        assert request.collection == "{}"

    def test_json_schema_example(self):
        """Test l'exemple du schéma JSON."""
        # Récupère l'exemple du modèle
        example = PredictRequest.Config.json_schema_extra["example"]

        # Vérifie que l'exemple est valide
        request = PredictRequest(**example)
        assert request is not None
        assert request.user_age == "33"
        assert request.user_genre == "Homme"


class TestRecommendedSerie:
    """Tests pour le modèle RecommendedSerie."""

    def test_valid_recommended_serie(self):
        """Test une série recommandée valide."""
        serie_data = {
            "title": "Attack on Titan",
            "id_series": "series-uuid-1",
            "responce_IA": "Parfait pour votre goût pour l'action intense"
        }

        # Exécution
        serie = RecommendedSerie(**serie_data)

        # Assertions
        assert serie.title == "Attack on Titan"
        assert serie.id_series == "series-uuid-1"
        assert serie.responce_IA == "Parfait pour votre goût pour l'action intense"

    def test_missing_fields_recommended_serie(self):
        """Test qu'une erreur est levée si des champs manquent."""
        incomplete_data = {
            "title": "Attack on Titan"
            # Manque id_series et responce_IA
        }

        # Exécution et assertion
        with pytest.raises(ValidationError):
            RecommendedSerie(**incomplete_data)

    def test_empty_fields_recommended_serie(self):
        """Test avec champs vides."""
        serie_data = {
            "title": "Attack on Titan",
            "id_series": "series-uuid-1",
            "responce_IA": ""  # Réponse vide
        }

        # Exécution
        serie = RecommendedSerie(**serie_data)

        # Assertions
        assert serie.responce_IA == ""


class TestPredictResponse:
    """Tests pour le modèle PredictResponse."""

    def test_valid_response_with_series(self):
        """Test une réponse valide avec des séries recommandées."""
        response_data = {
            "serie_recomendees": [
                {
                    "title": "Attack on Titan",
                    "id_series": "series-uuid-1",
                    "responce_IA": "Action intense"
                },
                {
                    "title": "Demon Slayer",
                    "id_series": "series-uuid-2",
                    "responce_IA": "Animation époustouflante"
                }
            ],
            "status": "success",
            "responce_IA_global": "Voici mes recommandations pour vous"
        }

        # Exécution
        response = PredictResponse(**response_data)

        # Assertions
        assert response.status == "success"
        assert len(response.serie_recomendees) == 2
        assert response.serie_recomendees[0].title == "Attack on Titan"
        assert response.serie_recomendees[1].title == "Demon Slayer"
        assert response.responce_IA_global == "Voici mes recommandations pour vous"

    def test_valid_response_empty_series(self):
        """Test une réponse valide sans séries recommandées."""
        response_data = {
            "serie_recomendees": [],
            "status": "success",
            "responce_IA_global": "Aucune série ne correspond à vos critères"
        }

        # Exécution
        response = PredictResponse(**response_data)

        # Assertions
        assert response.status == "success"
        assert len(response.serie_recomendees) == 0
        assert response.responce_IA_global == "Aucune série ne correspond à vos critères"

    def test_response_error_status(self):
        """Test une réponse avec statut d'erreur."""
        response_data = {
            "serie_recomendees": [],
            "status": "error",
            "responce_IA_global": "Une erreur s'est produite lors de la recherche"
        }

        # Exécution
        response = PredictResponse(**response_data)

        # Assertions
        assert response.status == "error"
        assert len(response.serie_recomendees) == 0

    def test_missing_required_fields_response(self):
        """Test qu'une erreur est levée si des champs obligatoires manquent."""
        incomplete_data = {
            "serie_recomendees": []
            # Manque status et responce_IA_global
        }

        # Exécution et assertion
        with pytest.raises(ValidationError):
            PredictResponse(**incomplete_data)

    def test_json_schema_example(self):
        """Test l'exemple du schéma JSON."""
        # Récupère l'exemple du modèle
        example = PredictResponse.Config.json_schema_extra["example"]

        # Vérifie que l'exemple est valide
        response = PredictResponse(**example)
        assert response is not None
        assert response.status == "success"
        assert len(response.serie_recomendees) == 2

    def test_response_serialization(self):
        """Test la sérialisation de la réponse."""
        response_data = {
            "serie_recomendees": [
                {
                    "title": "Attack on Titan",
                    "id_series": "series-uuid-1",
                    "responce_IA": "Action intense"
                }
            ],
            "status": "success",
            "responce_IA_global": "Voici ma recommandation"
        }

        # Exécution
        response = PredictResponse(**response_data)
        json_data = response.model_dump()

        # Assertions
        assert json_data["status"] == "success"
        assert len(json_data["serie_recomendees"]) == 1
        assert json_data["serie_recomendees"][0]["title"] == "Attack on Titan"

    def test_response_with_unicode(self):
        """Test la réponse avec caractères unicode."""
        response_data = {
            "serie_recomendees": [
                {
                    "title": "進撃の巨人",  # Attack on Titan en japonais
                    "id_series": "series-uuid-1",
                    "responce_IA": "アクション漫画"  # Action manga en japonais
                }
            ],
            "status": "success",
            "responce_IA_global": "日本のマンガをおすすめします"
        }

        # Exécution
        response = PredictResponse(**response_data)

        # Assertions
        assert response.serie_recomendees[0].title == "進撃の巨人"
        assert "日本のマンガ" in response.responce_IA_global