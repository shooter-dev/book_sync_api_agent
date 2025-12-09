"""
Tests unitaires pour Synthesizer.

Ce module teste le Synthesizer qui génère des réponses IA personnalisées
basées sur les profils utilisateurs et les recommandations.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.synthesizer import Synthesizer
from app.models.predict_response import RecommendedSerie


class TestSynthesizer:
    """Tests pour la classe Synthesizer."""

    @pytest.fixture
    def synthesizer(self):
        """Fixture pour créer une instance de Synthesizer."""
        return Synthesizer()

    @pytest.fixture
    def sample_recommended_series(self):
        """Fixture pour créer des séries recommandées de test."""
        return [
            RecommendedSerie(
                title="Attack on Titan",
                id_series="series-uuid-1",
                responce_IA="Parfait pour votre goût pour l'action intense"
            ),
            RecommendedSerie(
                title="Demon Slayer",
                id_series="series-uuid-2",
                responce_IA="Animation époustouflante et combats dynamiques"
            ),
            RecommendedSerie(
                title="My Hero Academia",
                id_series="series-uuid-3",
                responce_IA="Histoire inspirante de héros modernes"
            )
        ]

    @pytest.fixture
    def sample_user_profile(self):
        """Fixture pour créer un profil utilisateur de test."""
        return {
            'user_age': '25',
            'user_genre': 'Homme',
            'genre_preference': 'Manga',
            'category_preference': 'Action',
            'user_mood': 'Énervé',
            'prediction_type': 'recommendation',
            'collection': {},
            'read': {}
        }

    @pytest.fixture
    def sample_user_profile_with_collection(self):
        """Fixture pour un profil avec collection."""
        return {
            'user_age': '22',
            'user_genre': 'Femme',
            'genre_preference': 'Manga',
            'category_preference': 'Romance',
            'user_mood': 'Comique',
            'prediction_type': 'collection',
            'collection': {
                'One Piece': {
                    'volumes': {'1': 'uuid-1'},
                    'id_series': 'series-uuid-1'
                }
            },
            'read': {}
        }

    @patch('app.services.synthesizer.get_settings')
    @patch('app.services.synthesizer.OpenAI')
    def test_generate_global_response_openai(
        self,
        mock_openai_class,
        mock_settings,
        synthesizer,
        sample_recommended_series,
        sample_user_profile
    ):
        """Test la génération de réponse globale avec OpenAI standard."""
        # Configuration des mocks
        mock_settings.return_value = MagicMock()
        mock_settings.return_value.openai.api_key = "test-key"
        mock_settings.return_value.openai.default_model = "gpt-4o"

        mock_openai_instance = MagicMock()
        mock_openai_class.return_value = mock_openai_instance

        # Mock de la réponse OpenAI
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = "Voici mes recommandations personnalisées pour vous basées sur votre profil."
        mock_openai_instance.chat.completions.create.return_value = mock_completion

        with patch.dict('os.environ', {'USE_AZURE_OPENAI': 'false'}):
            # Exécution
            result = synthesizer.generate_global_response(
                recommended_series=sample_recommended_series,
                user_profile=sample_user_profile
            )

            # Assertions
            assert isinstance(result, str)
            assert len(result) > 0
            assert "recommandations personnalisées" in result.lower()
            mock_openai_instance.chat.completions.create.assert_called_once()

    @patch('app.services.synthesizer.get_settings')
    @patch('app.services.synthesizer.AzureOpenAI')
    def test_generate_global_response_azure(
        self,
        mock_azure_openai_class,
        mock_settings,
        synthesizer,
        sample_recommended_series,
        sample_user_profile
    ):
        """Test la génération de réponse globale avec Azure OpenAI."""
        # Configuration des mocks
        mock_settings.return_value = MagicMock()
        mock_settings.return_value.azure_openai.api_key = "test-key"
        mock_settings.return_value.azure_openai.default_model = "gpt-4o-mini"
        mock_settings.return_value.azure_openai.api_version = "2024-02-01"
        mock_settings.return_value.azure_openai.azure_endpoint = "https://test.openai.azure.com"

        mock_azure_instance = MagicMock()
        mock_azure_openai_class.return_value = mock_azure_instance

        # Mock de la réponse Azure OpenAI
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = "Recommandations personnalisées basées sur votre profil Azure."
        mock_azure_instance.chat.completions.create.return_value = mock_completion

        with patch.dict('os.environ', {'USE_AZURE_OPENAI': 'true'}):
            # Exécution
            result = synthesizer.generate_global_response(
                recommended_series=sample_recommended_series,
                user_profile=sample_user_profile
            )

            # Assertions
            assert isinstance(result, str)
            assert len(result) > 0
            assert mock_azure_instance.chat.completions.create.called

    @patch('app.services.synthesizer.get_settings')
    @patch('app.services.synthesizer.OpenAI')
    def test_generate_global_response_no_series(
        self,
        mock_openai_class,
        mock_settings,
        synthesizer,
        sample_user_profile
    ):
        """Test la génération de réponse sans séries recommandées."""
        # Configuration des mocks
        mock_settings.return_value = MagicMock()
        mock_settings.return_value.openai.api_key = "test-key"
        mock_settings.return_value.openai.default_model = "gpt-4o"

        mock_openai_instance = MagicMock()
        mock_openai_class.return_value = mock_openai_instance

        # Mock de la réponse OpenAI
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = "Malheureusement, aucune série ne correspond à vos critères."
        mock_openai_instance.chat.completions.create.return_value = mock_completion

        with patch.dict('os.environ', {'USE_AZURE_OPENAI': 'false'}):
            # Exécution
            result = synthesizer.generate_global_response(
                recommended_series=[],
                user_profile=sample_user_profile
            )

            # Assertions
            assert isinstance(result, str)
            assert len(result) > 0
            # Vérifie que le prompt contient "Aucune série trouvée"
            call_args = mock_openai_instance.chat.completions.create.call_args
            prompt_content = call_args.kwargs['messages'][0]['content']
            assert "Aucune série trouvée" in prompt_content

    @patch('app.services.synthesizer.get_settings')
    @patch('app.services.synthesizer.OpenAI')
    def test_generate_global_response_with_collection(
        self,
        mock_openai_class,
        mock_settings,
        synthesizer,
        sample_recommended_series,
        sample_user_profile_with_collection
    ):
        """Test la génération de réponse pour un utilisateur avec collection."""
        # Configuration des mocks
        mock_settings.return_value = MagicMock()
        mock_settings.return_value.openai.api_key = "test-key"
        mock_settings.return_value.openai.default_model = "gpt-4o"

        mock_openai_instance = MagicMock()
        mock_openai_class.return_value = mock_openai_instance

        # Mock de la réponse OpenAI
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = "Basé sur votre collection, voici des recommandations."
        mock_openai_instance.chat.completions.create.return_value = mock_completion

        with patch.dict('os.environ', {'USE_AZURE_OPENAI': 'false'}):
            # Exécution
            result = synthesizer.generate_global_response(
                recommended_series=sample_recommended_series,
                user_profile=sample_user_profile_with_collection
            )

            # Assertions
            assert isinstance(result, str)
            assert len(result) > 0

    @patch('app.services.synthesizer.get_settings')
    @patch('app.services.synthesizer.OpenAI')
    def test_generate_global_response_error_handling(
        self,
        mock_openai_class,
        mock_settings,
        synthesizer,
        sample_recommended_series,
        sample_user_profile
    ):
        """Test la gestion d'erreur lors de la génération de réponse."""
        # Configuration des mocks
        mock_settings.return_value = MagicMock()
        mock_settings.return_value.openai.api_key = "test-key"
        mock_settings.return_value.openai.default_model = "gpt-4o"

        mock_openai_instance = MagicMock()
        mock_openai_class.return_value = mock_openai_instance

        # Simule une erreur
        mock_openai_instance.chat.completions.create.side_effect = Exception("API Error")

        with patch.dict('os.environ', {'USE_AZURE_OPENAI': 'false'}):
            # Exécution
            result = synthesizer.generate_global_response(
                recommended_series=sample_recommended_series,
                user_profile=sample_user_profile
            )

            # Assertions
            assert isinstance(result, str)
            # Doit retourner le fallback message
            assert "Voici mes recommandations" in result or "basées sur votre profil" in result.lower()

    @patch('app.services.synthesizer.get_settings')
    @patch('app.services.synthesizer.OpenAI')
    def test_generate_global_response_prompt_structure(
        self,
        mock_openai_class,
        mock_settings,
        synthesizer,
        sample_recommended_series,
        sample_user_profile
    ):
        """Test la structure du prompt envoyé à OpenAI."""
        # Configuration des mocks
        mock_settings.return_value = MagicMock()
        mock_settings.return_value.openai.api_key = "test-key"
        mock_settings.return_value.openai.default_model = "gpt-4o"

        mock_openai_instance = MagicMock()
        mock_openai_class.return_value = mock_openai_instance

        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = "Test response"
        mock_openai_instance.chat.completions.create.return_value = mock_completion

        with patch.dict('os.environ', {'USE_AZURE_OPENAI': 'false'}):
            # Exécution
            synthesizer.generate_global_response(
                recommended_series=sample_recommended_series,
                user_profile=sample_user_profile
            )

            # Récupère les arguments de l'appel
            call_args = mock_openai_instance.chat.completions.create.call_args
            prompt_content = call_args.kwargs['messages'][0]['content']

            # Assertions sur le contenu du prompt
            assert '<Role_and_Objectives>' in prompt_content
            assert '<user_profile>' in prompt_content
            assert sample_user_profile['user_age'] in prompt_content
            assert sample_user_profile['category_preference'] in prompt_content
            assert 'Attack on Titan' in prompt_content
            assert 'Demon Slayer' in prompt_content
            assert 'My Hero Academia' in prompt_content

    @patch('app.services.synthesizer.get_settings')
    @patch('app.services.synthesizer.OpenAI')
    def test_generate_global_response_temperature_and_tokens(
        self,
        mock_openai_class,
        mock_settings,
        synthesizer,
        sample_recommended_series,
        sample_user_profile
    ):
        """Test les paramètres de température et max_tokens."""
        # Configuration des mocks
        mock_settings.return_value = MagicMock()
        mock_settings.return_value.openai.api_key = "test-key"
        mock_settings.return_value.openai.default_model = "gpt-4o"

        mock_openai_instance = MagicMock()
        mock_openai_class.return_value = mock_openai_instance

        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = "Test response"
        mock_openai_instance.chat.completions.create.return_value = mock_completion

        with patch.dict('os.environ', {'USE_AZURE_OPENAI': 'false'}):
            # Exécution
            synthesizer.generate_global_response(
                recommended_series=sample_recommended_series,
                user_profile=sample_user_profile
            )

            # Récupère les arguments de l'appel
            call_args = mock_openai_instance.chat.completions.create.call_args

            # Assertions sur les paramètres
            assert call_args.kwargs['temperature'] == 0.7
            assert call_args.kwargs['max_tokens'] == 200
            assert call_args.kwargs['model'] == "gpt-4o"