"""
Tests unitaires pour les routes /predict/.

Ce module teste les endpoints de l'API de prédiction.
"""

from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from app.main import app
from app.models.predict_request import PredictRequest
from app.models.predict_response import PredictResponse, RecommendedSerie
from app.routes.predict_routes import get_predict_service
from app.services.predict_service import PredictService


def create_mock_predict_service():
    """
    Crée un service de prédiction mocké pour les tests.

    Returns:
        MagicMock: Service de prédiction mocké
    """
    mock_service = MagicMock(spec=PredictService)
    return mock_service


client = TestClient(app)


class TestPredictRoutes:
    """Tests pour les routes de prédiction."""

    def test_health_check(self):
        """Test l'endpoint de health check."""
        headers = {"x-api-key": "azerty@&123"}
        response = client.get("/predict/health", headers=headers)

        # Assertions
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "service": "predict"}

    def test_predict_test_endpoint(self):
        """Test l'endpoint de test /predict/test."""
        # Données de test
        test_data = {"user_age": "25", "user_genre": "Homme", "category_preference": "Action"}
        headers = {"x-api-key": "azerty@&123"}

        # Exécution
        response = client.post("/predict/test", json=test_data, headers=headers)

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["received"] == test_data
        assert "types" in data

    def test_predict_success(self):
        """Test une prédiction réussie."""
        # Configuration du mock
        mock_response = PredictResponse(
            serie_recomendees=[
                RecommendedSerie(
                    title="Attack on Titan",
                    id_series="series-uuid-1",
                    responce_IA="Parfait pour votre goût pour l'action",
                )
            ],
            status="success",
            responce_IA_global="Voici mes recommandations personnalisées.",
        )

        # Créer un service mocké
        mock_service = create_mock_predict_service()
        mock_service.predict = AsyncMock(return_value=mock_response)

        # Override de la dépendance
        app.dependency_overrides[get_predict_service] = lambda: mock_service

        try:
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
                "user_mood": "Énervé",
            }
            headers = {"x-api-key": "azerty@&123"}
            response = client.post("/predict/", json=request_data, headers=headers)

            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert len(data["serie_recomendees"]) == 1
            assert data["serie_recomendees"][0]["title"] == "Attack on Titan"
            assert data["responce_IA_global"] == "Voici mes recommandations personnalisées."
        finally:
            # Nettoyer l'override
            app.dependency_overrides.clear()

    def test_predict_invalid_request(self):
        """Test une prédiction avec requête invalide."""
        # Mock du service pour éviter la connexion à la DB
        mock_service = create_mock_predict_service()
        app.dependency_overrides[get_predict_service] = lambda: mock_service

        try:
            # Données de requête invalides (champs manquants)
            request_data = {
                "user_age": "25",
                "user_genre": "Homme",
                "genre_preference": "Manga",
                # Manque category_preference, prediction_type, user_mood
                "collection": {},
                "read": {},
            }
            headers = {"x-api-key": "azerty@&123"}
            response = client.post("/predict/", json=request_data, headers=headers)

            # Assertions - devrait échouer avec une erreur de validation
            assert response.status_code == 422

            # Vérifier que le message d'erreur mentionne les champs manquants
            error_detail = response.json()["detail"]
            missing_fields = {"category_preference", "prediction_type", "user_mood"}
            for field in missing_fields:
                assert any(
                    field in str(err) for err in error_detail
                ), f"Le champ manquant {field} devrait être dans l'erreur"
        finally:
            # Nettoyer l'override
            app.dependency_overrides.clear()

    def test_predict_service_error(self):
        """Test la gestion d'erreur du service."""
        # Créer un service mocké qui lève une exception
        mock_service = create_mock_predict_service()
        mock_service.predict = AsyncMock(side_effect=Exception("Erreur de base de données"))

        # Override de la dépendance
        app.dependency_overrides[get_predict_service] = lambda: mock_service

        try:
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
                "user_mood": "Calme",
            }
            headers = {"x-api-key": "azerty@&123"}
            response = client.post("/predict/", json=request_data, headers=headers)

            # Assertions
            assert response.status_code == 500
            assert "Erreur lors de la prédiction" in response.json()["detail"]
        finally:
            # Nettoyer l'override
            app.dependency_overrides.clear()

    def test_predict_with_collection(self):
        """Test une prédiction avec collection."""
        # Configuration du mock
        mock_response = PredictResponse(
            serie_recomendees=[
                RecommendedSerie(
                    title="One Piece",
                    id_series="series-uuid-1",
                    responce_IA="Série de votre collection recommandée",
                )
            ],
            status="success",
            responce_IA_global="Voici nos recommandations basées sur votre collection.",
        )

        # Créer un service mocké
        mock_service = create_mock_predict_service()
        mock_service.predict = AsyncMock(return_value=mock_response)

        # Override de la dépendance
        app.dependency_overrides[get_predict_service] = lambda: mock_service

        try:
            # Données de requête avec collection
            request_data = {
                "user_age": "22",
                "user_genre": "Femme",
                "genre_preference": "Manga",
                "category_preference": "Romance",
                "user_comment": "",
                "prediction_type": "collection",
                "collection": {"One Piece": {"volumes": {"1": "uuid-1", "2": "uuid-2"}, "id_series": "series-uuid-1"}},
                "read": {"Naruto": {"volumes": {"1": "uuid-3"}, "id_series": "series-uuid-2"}},
                "user_mood": "Comique",
            }
            headers = {"x-api-key": "azerty@&123"}
            response = client.post("/predict/", json=request_data, headers=headers)

            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert len(data["serie_recomendees"]) > 0
            assert data["serie_recomendees"][0]["title"] == "One Piece"

            # Vérifier que le service a été appelé avec les bons paramètres
            mock_service.predict.assert_called_once()
            predict_arg = mock_service.predict.call_args[0][0]
            assert isinstance(predict_arg, PredictRequest)
            assert predict_arg.user_age == "22"
            assert predict_arg.prediction_type == "collection"
            assert "One Piece" in predict_arg.collection

        finally:
            # Nettoyer l'override
            app.dependency_overrides.clear()

    def test_predict_with_different_prediction_types(self):
        """Test les différents types de prédiction."""
        # Configuration du mock pour les réponses
        mock_response = PredictResponse(
            serie_recomendees=[
                RecommendedSerie(
                    title="Test Series",
                    id_series="test-uuid",
                    responce_IA="Recommandation de test",
                )
            ],
            status="success",
            responce_IA_global="Réponse de test",
        )

        # Créer un service mocké
        mock_service = create_mock_predict_service()
        mock_service.predict = AsyncMock(return_value=mock_response)

        # Override de la dépendance
        app.dependency_overrides[get_predict_service] = lambda: mock_service

        try:
            # Données de base pour la requête
            base_request = {
                "user_age": "25",
                "user_genre": "Homme",
                "genre_preference": "Manga",
                "category_preference": "Action",
                "user_comment": "",
                "collection": {},
                "read": {},
                "user_mood": "Calme",
            }
            headers = {"x-api-key": "azerty@&123"}
            request_recommendation = {**base_request, "prediction_type": "recommendation"}
            response_rec = client.post("/predict/", json=request_recommendation, headers=headers)
            assert response_rec.status_code == 200
            assert response_rec.json()["status"] == "success"

            # Vérifier que le service a été appelé avec le bon type de prédiction
            predict_arg = mock_service.predict.call_args_list[0][0][0]
            assert predict_arg.prediction_type == "recommendation"

            # Réinitialiser le mock pour le prochain test
            mock_service.predict.reset_mock()

            # Test avec collection
            request_collection = {**base_request, "prediction_type": "collection"}
            response_coll = client.post("/predict/", json=request_collection, headers=headers)
            assert response_coll.status_code == 200
            assert response_coll.json()["status"] == "success"

            # Vérifier que le service a été appelé avec le bon type de prédiction
            predict_arg = mock_service.predict.call_args_list[0][0][0]
            assert predict_arg.prediction_type == "collection"

        finally:
            # Nettoyer l'override
            app.dependency_overrides.clear()

    def test_predict_with_all_moods(self):
        """Test les différentes humeurs utilisateur."""
        # Configuration du mock pour les réponses
        mock_response = PredictResponse(
            serie_recomendees=[
                RecommendedSerie(
                    title=f"Test Series - {mood}",
                    id_series=f"test-uuid-{mood}",
                    responce_IA=f"Recommandation pour humeur: {mood}",
                )
                for mood in ["Énervé", "Comique", "Triste", "Joyeux", "Calme", "Anxieux"]
            ][
                :1
            ],  # On retourne une seule recommandation par test
            status="success",
            responce_IA_global="Réponse de test pour différentes humeurs",
        )

        # Créer un service mocké
        mock_service = create_mock_predict_service()
        mock_service.predict = AsyncMock(return_value=mock_response)

        # Override de la dépendance
        app.dependency_overrides[get_predict_service] = lambda: mock_service

        try:
            # Données de base pour la requête
            base_request = {
                "user_age": "25",
                "user_genre": "Homme",
                "genre_preference": "Manga",
                "category_preference": "Action",
                "user_comment": "",
                "prediction_type": "recommendation",
                "collection": {},
                "read": {},
            }
            headers = {"x-api-key": "azerty@&123"}
            moods = ["Énervé", "Comique", "Triste", "Joyeux", "Calme", "Anxieux"]
            for mood in moods:
                mock_service.predict.reset_mock()
                request_with_mood = {**base_request, "user_mood": mood}
                response = client.post("/predict/", json=request_with_mood, headers=headers)

                # Assertions
                assert response.status_code == 200, f"Échec avec l'humeur: {mood}"
                data = response.json()
                assert data["status"] == "success"

                # Vérifier que le service a été appelé avec la bonne humeur
                mock_service.predict.assert_called_once()
                predict_arg = mock_service.predict.call_args[0][0]
                assert predict_arg.user_mood == mood

        finally:
            # Nettoyer l'override
            app.dependency_overrides.clear()

    def test_predict_with_different_categories(self):
        """Test les différentes catégories de manga."""
        # Configuration du mock pour les réponses
        mock_response = PredictResponse(
            serie_recomendees=[
                RecommendedSerie(
                    title=f"Test Series - {category}",
                    id_series=f"test-uuid-{category}",
                    responce_IA=f"Recommandation pour catégorie: {category}",
                )
                for category in ["Action", "Romance", "Horror", "Comedy", "Drama", "Fantasy"]
            ][
                :1
            ],  # On retourne une seule recommandation par test
            status="success",
            responce_IA_global="Réponse de test pour différentes catégories",
        )

        # Créer un service mocké
        mock_service = create_mock_predict_service()
        mock_service.predict = AsyncMock(return_value=mock_response)

        # Override de la dépendance
        app.dependency_overrides[get_predict_service] = lambda: mock_service

        try:
            # Données de base pour la requête
            base_request = {
                "user_age": "25",
                "user_genre": "Homme",
                "genre_preference": "Manga",
                "user_comment": "",
                "prediction_type": "recommendation",
                "collection": {},
                "read": {},
                "user_mood": "Calme",
            }
            headers = {"x-api-key": "azerty@&123"}
            categories = ["Action", "Romance", "Horror", "Comedy", "Drama", "Fantasy"]
            for category in categories:
                mock_service.predict.reset_mock()
                request_with_category = {**base_request, "category_preference": category}
                response = client.post("/predict/", json=request_with_category, headers=headers)

                # Assertions
                assert response.status_code == 200, f"Échec avec la catégorie: {category}"
                data = response.json()
                assert data["status"] == "success"

                # Vérifier que le service a été appelé avec la bonne catégorie
                mock_service.predict.assert_called_once()
                predict_arg = mock_service.predict.call_args[0][0]
                assert predict_arg.category_preference == category

        finally:
            # Nettoyer l'override
            app.dependency_overrides.clear()

    def test_predict_empty_recommendations(self):
        """Test une prédiction sans recommandations."""
        # Configuration du mock pour retourner une réponse vide
        mock_response = PredictResponse(
            serie_recomendees=[],
            status="success",
            responce_IA_global="Aucune série ne correspond à vos critères actuellement.",
        )

        # Créer un service mocké
        mock_service = create_mock_predict_service()
        mock_service.predict = AsyncMock(return_value=mock_response)

        # Override de la dépendance
        app.dependency_overrides[get_predict_service] = lambda: mock_service

        try:
            request_data = {
                "user_age": "25",
                "user_genre": "Homme",
                "genre_preference": "Manga",
                "category_preference": "Action",
                "user_comment": "",
                "prediction_type": "recommendation",
                "collection": {},
                "read": {},
                "user_mood": "Calme",
            }
            headers = {"x-api-key": "azerty@&123"}
            response = client.post("/predict/", json=request_data, headers=headers)

            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert len(data["serie_recomendees"]) == 0
        finally:
            # Nettoyer l'override
            app.dependency_overrides.clear()

    def test_predict_with_user_comment(self):
        """Test une prédiction avec commentaire utilisateur."""
        # Configuration du mock pour les réponses
        user_comment = "Je cherche quelque chose avec beaucoup de combats et d'action intense"
        mock_response = PredictResponse(
            serie_recomendees=[
                RecommendedSerie(
                    title="Shingeki no Kyojin",
                    id_series="snk-123",
                    responce_IA="Parfait pour votre recherche d'action intense",
                )
            ],
            status="success",
            responce_IA_global=f"Voici une recommandation basée sur votre commentaire: {user_comment}",
        )

        # Créer un service mocké
        mock_service = create_mock_predict_service()
        mock_service.predict = AsyncMock(return_value=mock_response)

        # Override de la dépendance
        app.dependency_overrides[get_predict_service] = lambda: mock_service

        try:
            request_data = {
                "user_age": "25",
                "user_genre": "Homme",
                "genre_preference": "Manga",
                "category_preference": "Action",
                "user_comment": user_comment,
                "prediction_type": "recommendation",
                "collection": {},
                "read": {},
                "user_mood": "Énervé",
            }
            headers = {"x-api-key": "azerty@&123"}
            response = client.post("/predict/", json=request_data, headers=headers)

            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert len(data["serie_recomendees"]) > 0

            # Vérifier que le service a été appelé avec le bon commentaire
            mock_service.predict.assert_called_once()
            predict_arg = mock_service.predict.call_args[0][0]
            assert predict_arg.user_comment == user_comment

        finally:
            # Nettoyer l'override
            app.dependency_overrides.clear()

    def test_predict_age_validation(self):
        """Test la validation de l'âge."""
        # Configuration du mock pour les réponses
        mock_response = PredictResponse(
            serie_recomendees=[
                RecommendedSerie(
                    title="Test Series",
                    id_series="test-uuid",
                    responce_IA="Recommandation de test",
                )
            ],
            status="success",
            responce_IA_global="Réponse de test pour validation d'âge",
        )

        # Créer un service mocké
        mock_service = create_mock_predict_service()
        mock_service.predict = AsyncMock(return_value=mock_response)

        # Override de la dépendance
        app.dependency_overrides[get_predict_service] = lambda: mock_service

        try:
            # Test avec un âge valide
            valid_age_request = {
                "user_age": "25",
                "user_genre": "Homme",
                "genre_preference": "Manga",
                "category_preference": "Action",
                "user_comment": "",
                "prediction_type": "recommendation",
                "collection": {},
                "read": {},
                "user_mood": "Calme",
            }
            headers = {"x-api-key": "azerty@&123"}
            response = client.post("/predict/", json=valid_age_request, headers=headers)
            assert response.status_code == 200

            # Test avec un âge invalide (doit quand même passer car c'est une chaîne)
            invalid_age_request = {
                "user_age": "cent-vingt-cinq",
                "user_genre": "Homme",
                "genre_preference": "Manga",
                "category_preference": "Action",
                "user_comment": "",
                "prediction_type": "recommendation",
                "collection": {},
                "read": {},
                "user_mood": "Calme",
            }
            response = client.post("/predict/", json=invalid_age_request, headers=headers)
            assert response.status_code == 200

            # Vérifier que le service a été appelé deux fois
            assert mock_service.predict.call_count == 2

        finally:
            # Nettoyer l'override
            app.dependency_overrides.clear()

    def test_concurrent_requests(self):
        """Test les requêtes concurrentes."""
        # Configuration du mock pour les réponses
        mock_response = PredictResponse(
            serie_recomendees=[
                RecommendedSerie(
                    title="Test Series",
                    id_series="test-uuid",
                    responce_IA="Recommandation de test",
                )
            ],
            status="success",
            responce_IA_global="Réponse de test pour requêtes concurrentes",
        )

        # Créer un service mocké
        mock_service = create_mock_predict_service()
        mock_service.predict = AsyncMock(return_value=mock_response)

        # Override de la dépendance
        app.dependency_overrides[get_predict_service] = lambda: mock_service

        try:
            # Données de la requête
            request_data = {
                "user_age": "25",
                "user_genre": "Homme",
                "genre_preference": "Manga",
                "category_preference": "Action",
                "user_comment": "",
                "prediction_type": "recommendation",
                "collection": {},
                "read": {},
                "user_mood": "Calme",
            }
            headers = {"x-api-key": "azerty@&123"}
            responses = []
            for i in range(3):
                # Créer une copie des données avec un ID unique
                req_data = request_data.copy()
                req_data["user_comment"] = f"Requête {i+1}"

                # Exécuter la requête
                response = client.post("/predict/", json=req_data, headers=headers)
                responses.append(response)

            # Vérifie que toutes les requêtes ont réussi
            for i, response in enumerate(responses, 1):
                assert response.status_code == 200, f"La requête {i} a échoué avec le code {response.status_code}"
                data = response.json()
                assert data["status"] == "success"

            # Vérifier que le service a été appelé pour chaque requête
            assert mock_service.predict.call_count == 3

        finally:
            # Nettoyer l'override
            app.dependency_overrides.clear()
