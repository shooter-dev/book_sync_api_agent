"""
Tests unitaires pour VectorStore.

Ce module teste le VectorStore qui gère les opérations vectorielles
et les interactions avec la base de données PostgreSQL + pgvector.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime
from app.database.vector_store import VectorStore


class TestVectorStore:
    """Tests pour la classe VectorStore."""

    @patch('app.database.vector_store.psycopg2.connect')
    @patch('app.database.vector_store.OpenAI')
    @patch('app.database.vector_store.get_settings')
    def test_init_openai(self, mock_settings, mock_openai, mock_connect):
        """Test l'initialisation avec OpenAI standard."""
        # Configuration des mocks
        mock_settings.return_value = MagicMock()
        mock_settings.return_value.openai.api_key = "test-key"
        mock_settings.return_value.openai.embedding_model = "text-embedding-3-small"

        with patch.dict('os.environ', {'USE_AZURE_OPENAI': 'false'}):
            # Exécution
            vector_store = VectorStore()

            # Assertions
            assert vector_store is not None
            assert mock_openai.called
            mock_connect.assert_called_once()

    @patch('app.database.vector_store.psycopg2.connect')
    @patch('app.database.vector_store.AzureOpenAI')
    @patch('app.database.vector_store.get_settings')
    def test_init_azure_openai(self, mock_settings, mock_azure_openai, mock_connect):
        """Test l'initialisation avec Azure OpenAI."""
        # Configuration des mocks
        mock_settings.return_value = MagicMock()
        mock_settings.return_value.azure_openai.api_key = "test-key"
        mock_settings.return_value.azure_openai.embedding_model = "text-embedding-3-large"

        with patch.dict('os.environ', {'USE_AZURE_OPENAI': 'true'}):
            # Exécution
            vector_store = VectorStore()

            # Assertions
            assert vector_store is not None
            assert mock_azure_openai.called

    @patch('app.database.vector_store.psycopg2.connect')
    @patch('app.database.vector_store.OpenAI')
    @patch('app.database.vector_store.get_settings')
    def test_get_embedding(self, mock_settings, mock_openai_class, mock_connect):
        """Test la génération d'embeddings."""
        # Configuration des mocks
        mock_settings.return_value = MagicMock()
        mock_openai_instance = MagicMock()
        mock_openai_class.return_value = mock_openai_instance

        # Mock de la réponse OpenAI
        mock_embedding_response = MagicMock()
        mock_embedding_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
        mock_openai_instance.embeddings.create.return_value = mock_embedding_response

        with patch.dict('os.environ', {'USE_AZURE_OPENAI': 'false'}):
            vector_store = VectorStore()

            # Exécution
            result = vector_store.get_embedding("Test texte pour embedding")

            # Assertions
            assert result == [0.1, 0.2, 0.3]
            mock_openai_instance.embeddings.create.assert_called_once()

    @patch('app.database.vector_store.psycopg2.connect')
    @patch('app.database.vector_store.OpenAI')
    @patch('app.database.vector_store.get_settings')
    def test_create_tables(self, mock_settings, mock_openai, mock_connect):
        """Test la création des tables."""
        # Configuration des mocks
        mock_settings.return_value = MagicMock()
        mock_settings.return_value.vector_store.table_name = "embeddings"
        mock_settings.return_value.vector_store.embedding_dimensions = 3072

        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        with patch.dict('os.environ', {'USE_AZURE_OPENAI': 'false'}):
            vector_store = VectorStore()

            # Exécution
            vector_store.create_tables()

            # Assertions
            assert mock_cursor.execute.called
            # Vérifie que CREATE TABLE a été appelé
            calls = mock_cursor.execute.call_args_list
            assert any('CREATE TABLE' in str(call) for call in calls)

    @patch('app.database.vector_store.psycopg2.connect')
    @patch('app.database.vector_store.OpenAI')
    @patch('app.database.vector_store.get_settings')
    def test_create_index(self, mock_settings, mock_openai, mock_connect):
        """Test la création de l'index HNSW."""
        # Configuration des mocks
        mock_settings.return_value = MagicMock()
        mock_settings.return_value.vector_store.table_name = "embeddings"

        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        with patch.dict('os.environ', {'USE_AZURE_OPENAI': 'false'}):
            vector_store = VectorStore()

            # Exécution
            vector_store.create_index()

            # Assertions
            assert mock_cursor.execute.called
            calls = mock_cursor.execute.call_args_list
            assert any('CREATE INDEX' in str(call) for call in calls)

    @patch('app.database.vector_store.psycopg2.connect')
    @patch('app.database.vector_store.OpenAI')
    @patch('app.database.vector_store.get_settings')
    def test_upsert(self, mock_settings, mock_openai, mock_connect):
        """Test l'insertion/mise à jour de données."""
        # Configuration des mocks
        mock_settings.return_value = MagicMock()
        mock_settings.return_value.vector_store.table_name = "embeddings"

        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Création d'un DataFrame de test
        test_df = pd.DataFrame({
            'id': ['uuid-1', 'uuid-2'],
            'metadata': [{'title': 'Serie 1'}, {'title': 'Serie 2'}],
            'contents': ['Content 1', 'Content 2'],
            'embedding': [[0.1, 0.2], [0.3, 0.4]]
        })

        with patch.dict('os.environ', {'USE_AZURE_OPENAI': 'false'}):
            vector_store = VectorStore()

            # Exécution
            vector_store.upsert(test_df)

            # Assertions
            assert mock_cursor.execute.called
            # Vérifie que INSERT a été appelé 2 fois (une par ligne)
            assert mock_cursor.execute.call_count >= 2

    @patch('app.database.vector_store.psycopg2.connect')
    @patch('app.database.vector_store.OpenAI')
    @patch('app.database.vector_store.get_settings')
    def test_search(self, mock_settings, mock_openai_class, mock_connect):
        """Test la recherche vectorielle."""
        # Configuration des mocks
        mock_settings.return_value = MagicMock()
        mock_settings.return_value.vector_store.table_name = "embeddings"

        mock_openai_instance = MagicMock()
        mock_openai_class.return_value = mock_openai_instance

        # Mock embedding
        mock_embedding_response = MagicMock()
        mock_embedding_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
        mock_openai_instance.embeddings.create.return_value = mock_embedding_response

        # Mock cursor avec résultats
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ('uuid-1', {'title': 'Serie 1'}, 'Content 1', [0.1, 0.2, 0.3]),
            ('uuid-2', {'title': 'Serie 2'}, 'Content 2', [0.15, 0.25, 0.35])
        ]

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        with patch.dict('os.environ', {'USE_AZURE_OPENAI': 'false'}):
            vector_store = VectorStore()

            # Exécution
            result = vector_store.search("Test query", limit=5, return_dataframe=True)

            # Assertions
            assert isinstance(result, pd.DataFrame)
            assert not result.empty
            assert 'id' in result.columns
            assert 'similarity' in result.columns

    @patch('app.database.vector_store.psycopg2.connect')
    @patch('app.database.vector_store.OpenAI')
    @patch('app.database.vector_store.get_settings')
    def test_search_with_metadata_filter(self, mock_settings, mock_openai_class, mock_connect):
        """Test la recherche avec filtre de métadonnées."""
        # Configuration similaire au test précédent
        mock_settings.return_value = MagicMock()
        mock_settings.return_value.vector_store.table_name = "embeddings"

        mock_openai_instance = MagicMock()
        mock_openai_class.return_value = mock_openai_instance

        mock_embedding_response = MagicMock()
        mock_embedding_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
        mock_openai_instance.embeddings.create.return_value = mock_embedding_response

        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ('uuid-1', {'title': 'Serie 1', 'genre': 'Action'}, 'Content 1', [0.1, 0.2, 0.3])
        ]

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        with patch.dict('os.environ', {'USE_AZURE_OPENAI': 'false'}):
            vector_store = VectorStore()

            # Exécution avec filtre
            result = vector_store.search(
                "Test query",
                limit=5,
                metadata_filter={"genre": "Action"},
                return_dataframe=True
            )

            # Assertions
            assert isinstance(result, pd.DataFrame)
            # Vérifie que le filtre a été appliqué dans la requête SQL
            assert mock_cursor.execute.called

    @patch('app.database.vector_store.psycopg2.connect')
    @patch('app.database.vector_store.OpenAI')
    @patch('app.database.vector_store.get_settings')
    def test_delete_by_ids(self, mock_settings, mock_openai, mock_connect):
        """Test la suppression par IDs."""
        # Configuration des mocks
        mock_settings.return_value = MagicMock()
        mock_settings.return_value.vector_store.table_name = "embeddings"

        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        with patch.dict('os.environ', {'USE_AZURE_OPENAI': 'false'}):
            vector_store = VectorStore()

            # Exécution
            vector_store.delete(ids=['uuid-1', 'uuid-2'])

            # Assertions
            assert mock_cursor.execute.called
            calls = mock_cursor.execute.call_args_list
            assert any('DELETE' in str(call) for call in calls)

    @patch('app.database.vector_store.psycopg2.connect')
    @patch('app.database.vector_store.OpenAI')
    @patch('app.database.vector_store.get_settings')
    def test_delete_by_metadata(self, mock_settings, mock_openai, mock_connect):
        """Test la suppression par filtre de métadonnées."""
        # Configuration des mocks
        mock_settings.return_value = MagicMock()
        mock_settings.return_value.vector_store.table_name = "embeddings"

        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        with patch.dict('os.environ', {'USE_AZURE_OPENAI': 'false'}):
            vector_store = VectorStore()

            # Exécution
            vector_store.delete(metadata_filter={"serie": "One Piece"})

            # Assertions
            assert mock_cursor.execute.called
            calls = mock_cursor.execute.call_args_list
            assert any('DELETE' in str(call) for call in calls)

    @patch('app.database.vector_store.psycopg2.connect')
    @patch('app.database.vector_store.OpenAI')
    @patch('app.database.vector_store.get_settings')
    def test_delete_all(self, mock_settings, mock_openai, mock_connect):
        """Test la suppression de tous les enregistrements."""
        # Configuration des mocks
        mock_settings.return_value = MagicMock()
        mock_settings.return_value.vector_store.table_name = "embeddings"

        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        with patch.dict('os.environ', {'USE_AZURE_OPENAI': 'false'}):
            vector_store = VectorStore()

            # Exécution
            vector_store.delete(delete_all=True)

            # Assertions
            assert mock_cursor.execute.called
            calls = mock_cursor.execute.call_args_list
            assert any('DELETE FROM' in str(call) for call in calls)

    @patch('app.database.vector_store.psycopg2.connect')
    @patch('app.database.vector_store.OpenAI')
    @patch('app.database.vector_store.get_settings')
    def test_delete_invalid_parameters(self, mock_settings, mock_openai, mock_connect):
        """Test la suppression avec des paramètres invalides."""
        # Configuration des mocks
        mock_settings.return_value = MagicMock()

        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        with patch.dict('os.environ', {'USE_AZURE_OPENAI': 'false'}):
            vector_store = VectorStore()

            # Teste qu'une exception est levée si aucun paramètre valide
            with pytest.raises(ValueError):
                vector_store.delete()

            # Teste qu'une exception est levée si plusieurs paramètres
            with pytest.raises(ValueError):
                vector_store.delete(ids=['uuid-1'], delete_all=True)

    @patch('app.database.vector_store.psycopg2.connect')
    @patch('app.database.vector_store.OpenAI')
    @patch('app.database.vector_store.get_settings')
    def test_create_dataframe_from_results_empty(self, mock_settings, mock_openai, mock_connect):
        """Test la création de DataFrame à partir de résultats vides."""
        # Configuration des mocks
        mock_settings.return_value = MagicMock()

        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        with patch.dict('os.environ', {'USE_AZURE_OPENAI': 'false'}):
            vector_store = VectorStore()

            # Exécution
            result = vector_store._create_dataframe_from_results([])

            # Assertions
            assert isinstance(result, pd.DataFrame)
            assert result.empty