"""
Tests pour le service de prédiction.

Ces tests vérifient la logique métier du service de recommandation.
"""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock, AsyncMock

from app.services.predict_service import PredictService
from app.models.predict_request import PredictRequest
from app.models.predict_response import PredictResponse, RecommendedSerie


class TestPredictServiceInit:
    """Tests pour l'initialisation du PredictService."""

    @patch("app.services.predict_service.VectorStore")
    @patch("app.services.predict_service.Synthesizer")
    def test_service_initialization(self, mock_synth, mock_vector):
        """Test que le service s'initialise correctement."""
        service = PredictService()
        assert service.vector_store is not None
        assert service.synthesizer is not None


class TestSearchSimilarVolumes:
    """Tests pour la méthode _search_similar_volumes."""

    @patch("app.services.predict_service.VectorStore")
    @patch("app.services.predict_service.Synthesizer")
    def test_search_with_collection(self, mock_synth, mock_vector):
        """Test la recherche avec une collection."""
        # Configurer le mock
        mock_vector_instance = MagicMock()
        mock_vector_instance.search.return_value = pd.DataFrame({
            "serie_title": ["Naruto"],
            "serie_id": ["naruto-uuid"],
            "genre": ["Action"],
            "categorie": ["Shonen"]
        })
        mock_vector.return_value = mock_vector_instance

        service = PredictService()
        service.vector_store = mock_vector_instance

        request = PredictRequest(
            user_age="25",
            user_genre="Homme",
            genre_preference="Manga",
            category_preference="Action",
            prediction_type="collection",
            user_mood="Action",
            collection={
                "Hunter X Hunter": {
                    "volumes": {"1": "uuid-1"},
                    "id_series": "hxh-uuid"
                }
            }
        )

        results = service._search_similar_volumes(request, limit=5)
        assert mock_vector_instance.search.called

    @patch("app.services.predict_service.VectorStore")
    @patch("app.services.predict_service.Synthesizer")
    def test_search_without_collection(self, mock_synth, mock_vector):
        """Test la recherche sans collection (basée sur préférences)."""
        mock_vector_instance = MagicMock()
        mock_vector_instance.search.return_value = pd.DataFrame({
            "serie_title": ["One Piece"],
            "serie_id": ["op-uuid"],
            "genre": ["Action"],
            "categorie": ["Shonen"]
        })
        mock_vector.return_value = mock_vector_instance

        service = PredictService()
        service.vector_store = mock_vector_instance

        request = PredictRequest(
            user_age="20",
            user_genre="Homme",
            genre_preference="Manga",
            category_preference="Action",
            prediction_type="recommendation",
            user_mood="Comique"
        )

        results = service._search_similar_volumes(request, limit=5)
        assert mock_vector_instance.search.called

    @patch("app.services.predict_service.VectorStore")
    @patch("app.services.predict_service.Synthesizer")
    def test_search_with_error(self, mock_synth, mock_vector):
        """Test la gestion d'erreur lors de la recherche."""
        mock_vector_instance = MagicMock()
        mock_vector_instance.search.side_effect = Exception("DB Error")
        mock_vector.return_value = mock_vector_instance

        service = PredictService()
        service.vector_store = mock_vector_instance

        request = PredictRequest(
            user_age="25",
            user_genre="Homme",
            genre_preference="Manga",
            category_preference="Action",
            prediction_type="recommendation",
            user_mood="Action"
        )

        results = service._search_similar_volumes(request)
        # Devrait retourner un DataFrame vide en cas d'erreur
        assert results.empty


class TestExtractSeriesRecommendations:
    """Tests pour la méthode _extract_series_recommendations."""

    @patch("app.services.predict_service.VectorStore")
    @patch("app.services.predict_service.Synthesizer")
    def test_extract_from_valid_results(self, mock_synth, mock_vector):
        """Test l'extraction de recommandations valides."""
        service = PredictService()

        search_results = pd.DataFrame({
            "serie_title": ["Demon Slayer", "Jujutsu Kaisen"],
            "serie_id": ["ds-uuid", "jjk-uuid"],
            "genre": ["Action", "Action"],
            "categorie": ["Shonen", "Shonen"]
        })

        request = PredictRequest(
            user_age="18",
            user_genre="Homme",
            genre_preference="Manga",
            category_preference="Action",
            prediction_type="recommendation",
            user_mood="Action"
        )

        recommendations = service._extract_series_recommendations(search_results, request)
        assert len(recommendations) == 2
        assert recommendations[0].title == "Demon Slayer"
        assert recommendations[0].id_series == "ds-uuid"

    @patch("app.services.predict_service.VectorStore")
    @patch("app.services.predict_service.Synthesizer")
    def test_extract_from_empty_results(self, mock_synth, mock_vector):
        """Test l'extraction avec des résultats vides."""
        service = PredictService()

        search_results = pd.DataFrame()

        request = PredictRequest(
            user_age="25",
            user_genre="Femme",
            genre_preference="Manga",
            category_preference="Romance",
            prediction_type="recommendation",
            user_mood="Romantique"
        )

        recommendations = service._extract_series_recommendations(search_results, request)
        assert len(recommendations) == 0


class TestGenerateAiResponse:
    """Tests pour la méthode _generate_ai_response."""

    @patch("app.services.predict_service.VectorStore")
    @patch("app.services.predict_service.Synthesizer")
    def test_generate_response_with_matching_preference(self, mock_synth, mock_vector):
        """Test la génération de réponse avec préférence correspondante."""
        service = PredictService()

        request = PredictRequest(
            user_age="25",
            user_genre="Homme",
            genre_preference="Manga",
            category_preference="Action",
            prediction_type="recommendation",
            user_mood="Action"
        )

        response = service._generate_ai_response(
            title="Naruto",
            genre="Action, Aventure",
            category="Shonen",
            request=request
        )

        assert "Naruto" in response
        assert isinstance(response, str)

    @patch("app.services.predict_service.VectorStore")
    @patch("app.services.predict_service.Synthesizer")
    def test_generate_response_for_seinen(self, mock_synth, mock_vector):
        """Test la génération de réponse pour un seinen avec utilisateur adulte."""
        service = PredictService()

        request = PredictRequest(
            user_age="25",
            user_genre="Homme",
            genre_preference="Manga",
            category_preference="Thriller",
            prediction_type="recommendation",
            user_mood="Sombre"
        )

        response = service._generate_ai_response(
            title="Monster",
            genre="Thriller, Psychological",
            category="Seinen",
            request=request
        )

        assert "Monster" in response


class TestPredict:
    """Tests pour la méthode predict."""

    @pytest.mark.asyncio
    @patch("app.services.predict_service.VectorStore")
    @patch("app.services.predict_service.Synthesizer")
    async def test_predict_returns_response(self, mock_synth, mock_vector):
        """Test que predict retourne une réponse valide."""
        # Configurer les mocks
        mock_vector_instance = MagicMock()
        mock_vector_instance.search.return_value = pd.DataFrame({
            "serie_title": ["Test Serie"],
            "serie_id": ["test-uuid"],
            "genre": ["Action"],
            "categorie": ["Shonen"]
        })
        mock_vector.return_value = mock_vector_instance

        mock_synth_instance = MagicMock()
        mock_synth_instance.generate_global_response.return_value = "Réponse test"
        mock_synth.return_value = mock_synth_instance

        service = PredictService()
        service.vector_store = mock_vector_instance
        service.synthesizer = mock_synth_instance

        request = PredictRequest(
            user_age="25",
            user_genre="Homme",
            genre_preference="Manga",
            category_preference="Action",
            prediction_type="recommendation",
            user_mood="Action"
        )

        response = await service.predict(request)

        assert isinstance(response, PredictResponse)
        assert response.status == "success"

    @pytest.mark.asyncio
    @patch("app.services.predict_service.VectorStore")
    @patch("app.services.predict_service.Synthesizer")
    async def test_predict_handles_error(self, mock_synth, mock_vector):
        """Test que predict gère les erreurs correctement."""
        mock_vector_instance = MagicMock()
        mock_vector_instance.search.side_effect = Exception("Test error")
        mock_vector.return_value = mock_vector_instance

        mock_synth_instance = MagicMock()
        mock_synth.return_value = mock_synth_instance

        service = PredictService()
        service.vector_store = mock_vector_instance
        service.synthesizer = mock_synth_instance

        request = PredictRequest(
            user_age="25",
            user_genre="Homme",
            genre_preference="Manga",
            category_preference="Action",
            prediction_type="recommendation",
            user_mood="Action"
        )

        response = await service.predict(request)

        assert isinstance(response, PredictResponse)
        # Le service gère l'erreur et retourne quand même une réponse
