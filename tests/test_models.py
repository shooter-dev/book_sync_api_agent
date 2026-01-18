"""
Tests pour les modèles Pydantic.

Ces tests vérifient la validation des données d'entrée et de sortie.
"""

import pytest
from pydantic import ValidationError

from app.models.predict_request import PredictRequest
from app.models.predict_response import PredictResponse, RecommendedSerie


class TestPredictRequest:
    """Tests pour le modèle PredictRequest."""

    def test_valid_request(self):
        """Test qu'une requête valide est acceptée."""
        request = PredictRequest(
            user_age="25",
            user_genre="Homme",
            genre_preference="Global Manga",
            category_preference="Action",
            prediction_type="recommendation",
            user_mood="Comique"
        )
        assert request.user_age == "25"
        assert request.user_genre == "Homme"

    def test_request_with_collection(self):
        """Test qu'une requête avec collection est acceptée."""
        request = PredictRequest(
            user_age="30",
            user_genre="Femme",
            genre_preference="Shojo",
            category_preference="Romance",
            prediction_type="collection",
            user_mood="Romantique",
            collection={
                "Fruits Basket": {
                    "volumes": {"1": "uuid-1"},
                    "id_series": "series-uuid"
                }
            }
        )
        assert request.collection is not None
        assert "Fruits Basket" in request.collection

    def test_request_missing_required_field(self):
        """Test qu'une requête sans champ requis est refusée."""
        with pytest.raises(ValidationError):
            PredictRequest(
                user_age="25",
                # user_genre manquant
                genre_preference="Manga",
                category_preference="Action",
                prediction_type="recommendation",
                user_mood="Action"
            )

    def test_request_invalid_prediction_type(self):
        """Test qu'un type de prédiction invalide est refusé."""
        with pytest.raises(ValidationError):
            PredictRequest(
                user_age="25",
                user_genre="Homme",
                genre_preference="Manga",
                category_preference="Action",
                prediction_type="invalid_type",  # Doit être "collection" ou "recommendation"
                user_mood="Action"
            )

    def test_request_with_default_values(self):
        """Test que les valeurs par défaut sont appliquées."""
        request = PredictRequest(
            user_age="20",
            user_genre="Autre",
            genre_preference="Seinen",
            category_preference="Thriller",
            prediction_type="recommendation",
            user_mood="Sombre"
        )
        assert request.user_comment == ""
        assert request.limit == 5
        assert request.collection is None

    def test_request_limit_bounds(self):
        """Test que les limites de 'limit' sont respectées."""
        # Limite trop basse
        with pytest.raises(ValidationError):
            PredictRequest(
                user_age="25",
                user_genre="Homme",
                genre_preference="Manga",
                category_preference="Action",
                prediction_type="recommendation",
                user_mood="Action",
                limit=0  # Minimum est 1
            )


class TestRecommendedSerie:
    """Tests pour le modèle RecommendedSerie."""

    def test_valid_recommended_serie(self):
        """Test qu'une série recommandée valide est acceptée."""
        serie = RecommendedSerie(
            title="One Piece",
            id_series="one-piece-uuid",
            responce_IA="Une aventure épique pour les fans d'action"
        )
        assert serie.title == "One Piece"
        assert serie.id_series == "one-piece-uuid"

    def test_recommended_serie_missing_field(self):
        """Test qu'une série sans champ requis est refusée."""
        with pytest.raises(ValidationError):
            RecommendedSerie(
                title="Naruto"
                # id_series manquant
            )


class TestPredictResponse:
    """Tests pour le modèle PredictResponse."""

    def test_valid_response(self):
        """Test qu'une réponse valide est acceptée."""
        response = PredictResponse(
            serie_recomendees=[
                RecommendedSerie(
                    title="Demon Slayer",
                    id_series="ds-uuid",
                    responce_IA="Action intense"
                )
            ],
            status="success",
            responce_IA_global="Voici vos recommandations"
        )
        assert response.status == "success"
        assert len(response.serie_recomendees) == 1

    def test_response_empty_recommendations(self):
        """Test qu'une réponse sans recommandations est acceptée."""
        response = PredictResponse(
            serie_recomendees=[],
            status="success",
            responce_IA_global="Aucune recommandation trouvée"
        )
        assert len(response.serie_recomendees) == 0

    def test_response_error_status(self):
        """Test qu'une réponse d'erreur est acceptée."""
        response = PredictResponse(
            serie_recomendees=[],
            status="error",
            responce_IA_global="Une erreur s'est produite"
        )
        assert response.status == "error"
