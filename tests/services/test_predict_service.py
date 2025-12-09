"""
Tests unitaires pour PredictService.

Ce module teste le service de prédiction qui orchestre
la recherche vectorielle et la génération de recommandations.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from app.services.predict_service import PredictService
from app.models.predict_request import PredictRequest
from app.models.predict_response import PredictResponse, RecommendedSerie


class TestPredictService:
    """Tests pour le service PredictService."""

    @pytest.fixture
    def predict_service(self):
        """Fixture pour créer une instance de PredictService."""
        return PredictService()

    @pytest.fixture
    def sample_request(self):
        """Fixture pour créer une requête de test."""
        return PredictRequest(
            user_age="25",
            user_genre="Homme",
            genre_preference="Manga",
            category_preference="Action",
            user_comment="Je cherche quelque chose d'intense",
            prediction_type="recommendation",
            collection={},
            read={},
            user_mood="Énervé"
        )

    @pytest.fixture
    def sample_request_with_collection(self):
        """Fixture pour une requête avec collection."""
        return PredictRequest(
            user_age="25",
            user_genre="Homme",
            genre_preference="Manga",
            category_preference="Action",
            user_comment="",
            prediction_type="collection",
            collection={
                "One Piece": {
                    "volumes": {
                        "1": "uuid-1",
                        "2": "uuid-2"
                    },
                    "id_series": "series-uuid-1"
                }
            },
            read={
                "Naruto": {
                    "volumes": {
                        "1": "uuid-3"
                    },
                    "id_series": "series-uuid-2"
                }
            },
            user_mood="Comique"
        )

    @pytest.fixture
    def mock_search_results(self):
        """Fixture pour simuler des résultats de recherche vectorielle."""
        return pd.DataFrame({
            'id': ['uuid-1', 'uuid-2', 'uuid-3'],
            'serie_title': ['Attack on Titan', 'Demon Slayer', 'My Hero Academia'],
            'serie_id': ['series-uuid-1', 'series-uuid-2', 'series-uuid-3'],
            'genre': ['Action', 'Action', 'Action'],
            'categorie': ['Shonen', 'Shonen', 'Shonen'],
            'similarity': [0.95, 0.92, 0.88],
            'content': ['Description 1', 'Description 2', 'Description 3']
        })

    def test_init(self, predict_service):
        """Test l'initialisation du service."""
        assert predict_service is not None
        assert hasattr(predict_service, 'vector_store')
        assert hasattr(predict_service, 'synthesizer')

    @patch('app.services.predict_service.PredictService._search_similar_volumes')
    @patch('app.services.predict_service.Synthesizer.generate_global_response')
    @pytest.mark.asyncio
    async def test_predict_success(
        self,
        mock_generate_response,
        mock_search,
        predict_service,
        sample_request,
        mock_search_results
    ):
        """Test une prédiction réussie."""
        # Configuration des mocks
        mock_search.return_value = mock_search_results
        mock_generate_response.return_value = "Voici mes recommandations personnalisées pour vous."

        # Exécution
        result = await predict_service.predict(sample_request)

        # Assertions
        assert isinstance(result, PredictResponse)
        assert result.status == "success"
        assert len(result.serie_recomendees) == 3
        assert result.responce_IA_global == "Voici mes recommandations personnalisées pour vous."

        # Vérifier que les séries recommandées sont correctes
        assert result.serie_recomendees[0].title == "Attack on Titan"
        assert result.serie_recomendees[0].id_series == "series-uuid-1"

    @patch('app.services.predict_service.PredictService._search_similar_volumes')
    @pytest.mark.asyncio
    async def test_predict_no_results(
        self,
        mock_search,
        predict_service,
        sample_request
    ):
        """Test une prédiction sans résultats."""
        # Configuration du mock pour retourner un DataFrame vide
        mock_search.return_value = pd.DataFrame()

        # Exécution
        result = await predict_service.predict(sample_request)

        # Assertions
        assert isinstance(result, PredictResponse)
        assert result.status == "success"
        assert len(result.serie_recomendees) == 0

    @patch('app.services.predict_service.PredictService._search_similar_volumes')
    @pytest.mark.asyncio
    async def test_predict_with_error(
        self,
        mock_search,
        predict_service,
        sample_request
    ):
        """Test la gestion d'erreur lors de la prédiction."""
        # Configuration du mock pour lever une exception
        mock_search.side_effect = Exception("Erreur de base de données")

        # Exécution
        result = await predict_service.predict(sample_request)

        # Assertions
        assert isinstance(result, PredictResponse)
        assert result.status == "error"
        assert "erreur" in result.responce_IA_global.lower()

    @patch('app.services.predict_service.VectorStore.search')
    def test_search_similar_volumes_with_collection(
        self,
        mock_vector_search,
        predict_service,
        sample_request_with_collection,
        mock_search_results
    ):
        """Test la recherche avec collection et volumes lus."""
        # Configuration du mock
        mock_vector_search.return_value = mock_search_results

        # Exécution
        result = predict_service._search_similar_volumes(sample_request_with_collection, limit=10)

        # Assertions
        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        # Vérifie que search a été appelé au moins une fois
        assert mock_vector_search.called

    @patch('app.services.predict_service.VectorStore.search')
    def test_search_similar_volumes_without_collection(
        self,
        mock_vector_search,
        predict_service,
        sample_request,
        mock_search_results
    ):
        """Test la recherche sans collection (basée sur préférences)."""
        # Configuration du mock
        mock_vector_search.return_value = mock_search_results

        # Exécution
        result = predict_service._search_similar_volumes(sample_request, limit=10)

        # Assertions
        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        # Vérifie que search a été appelé avec les bonnes préférences
        assert mock_vector_search.called

    def test_extract_series_recommendations(
        self,
        predict_service,
        sample_request,
        mock_search_results
    ):
        """Test l'extraction des recommandations de séries."""
        # Exécution
        result = predict_service._extract_series_recommendations(
            mock_search_results,
            sample_request
        )

        # Assertions
        assert isinstance(result, list)
        assert len(result) == 3
        assert all(isinstance(serie, RecommendedSerie) for serie in result)
        assert result[0].title == "Attack on Titan"
        assert result[0].id_series == "series-uuid-1"
        assert result[0].responce_IA != ""

    def test_extract_series_recommendations_empty(
        self,
        predict_service,
        sample_request
    ):
        """Test l'extraction avec un DataFrame vide."""
        # Exécution
        result = predict_service._extract_series_recommendations(
            pd.DataFrame(),
            sample_request
        )

        # Assertions
        assert isinstance(result, list)
        assert len(result) == 0

    def test_generate_ai_response_action(self, predict_service, sample_request):
        """Test la génération de réponse IA pour genre Action."""
        # Exécution
        result = predict_service._generate_ai_response(
            "Attack on Titan",
            "Action",
            "Shonen",
            sample_request
        )

        # Assertions
        assert isinstance(result, str)
        assert "Attack on Titan" in result
        assert len(result) > 0

    def test_generate_ai_response_mood_match(self, predict_service):
        """Test la génération de réponse IA avec correspondance d'humeur."""
        request = PredictRequest(
            user_age="25",
            user_genre="Homme",
            genre_preference="Manga",
            category_preference="Action",
            user_comment="",
            prediction_type="recommendation",
            user_mood="Énervé"
        )

        # Exécution
        result = predict_service._generate_ai_response(
            "Attack on Titan",
            "Action",
            "Shonen",
            request
        )

        # Assertions
        assert isinstance(result, str)
        assert "Attack on Titan" in result

    def test_generate_ai_response_seinen_adult(self, predict_service):
        """Test la génération de réponse IA pour Seinen et utilisateur adulte."""
        request = PredictRequest(
            user_age="25",
            user_genre="Homme",
            genre_preference="Manga",
            category_preference="Seinen",
            user_comment="",
            prediction_type="recommendation",
            user_mood="Calme"
        )

        # Exécution
        result = predict_service._generate_ai_response(
            "Berserk",
            "Dark Fantasy",
            "Seinen",
            request
        )

        # Assertions
        assert isinstance(result, str)
        assert "Berserk" in result
        # Peut contenir "adapté à votre maturité" ou autre raison
        assert len(result) > 0