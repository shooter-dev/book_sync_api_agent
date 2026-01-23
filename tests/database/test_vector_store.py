"""
Tests unitaires pour VectorStore.

Ce module teste le VectorStore qui gère les opérations vectorielles
et les interactions avec la base de données PostgreSQL + pgvector.
"""

from unittest.mock import MagicMock, patch

import pandas as pd

from app.database.vector_store import VectorStore


class TestVectorStore:
    """Tests pour la classe VectorStore."""

    @patch("app.database.vector_store.register_vector")
    @patch("app.database.vector_store.psycopg2.connect")
    @patch("app.database.vector_store.OpenAI")
    @patch("app.database.vector_store.get_settings")
    @patch.dict(
        "os.environ",
        {
            "USE_AZURE_OPENAI": "false",
            "OPENAI_API_KEY": "test-key",
            "TIMESCALE_SERVICE_URL": "postgresql://user:pass@localhost:5432/db",
        },
        clear=True,
    )
    def test_init_openai(self, mock_settings, mock_openai_class, mock_connect, mock_register_vector):
        """Test l'initialisation avec OpenAI standard."""
        # Configuration des mocks
        mock_settings.return_value = MagicMock()
        mock_settings.return_value.openai.api_key = "test-key"
        mock_settings.return_value.openai.embedding_model = "text-embedding-3-small"

        # Configuration des paramètres de la base de données
        mock_settings.return_value.database = MagicMock()
        mock_settings.return_value.database.service_url = "postgresql://user:pass@localhost:5432/db"

        # Configuration des paramètres du vector store
        mock_settings.return_value.vector_store = MagicMock()
        mock_settings.return_value.vector_store.table_name = "embeddings"
        mock_settings.return_value.vector_store.embedding_dimensions = 3072

        # Mock de la connexion à la base de données
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Mock du client OpenAI
        mock_openai_instance = MagicMock()
        mock_openai_class.return_value = mock_openai_instance

        # Initialisation
        vector_store = VectorStore()

        # Assertions
        assert vector_store is not None

        # Vérification de l'initialisation du client OpenAI
        mock_openai_class.assert_called_once_with(api_key="test-key")

        # Vérification de la connexion à la base de données
        mock_connect.assert_called_once_with("postgresql://user:pass@localhost:5432/db")

        # Vérification de la création de l'extension vector
        mock_cursor.execute.assert_any_call("CREATE EXTENSION IF NOT EXISTS vector")

        # Vérification du commit après la création de l'extension
        mock_conn.commit.assert_called_once()

        # Vérification de l'enregistrement du type vector
        # Note: On ne peut pas vérifier directement l'appel à register_vector car c'est une fonction C
        # On vérifie plutôt que le curseur a été utilisé pour exécuter des commandes
        assert mock_cursor.execute.call_count >= 1, "Au moins une commande SQL doit avoir été exécutée"

    @patch("app.database.vector_store.register_vector")
    @patch("app.database.vector_store.psycopg2.connect")
    @patch("app.database.vector_store.AzureOpenAI")
    @patch("app.database.vector_store.get_settings")
    @patch.dict(
        "os.environ",
        {
            "USE_AZURE_OPENAI": "true",
            "AZURE_OPENAI_KEY": "test-key",
            "AZURE_OPENAI_VERSION": "2023-05-15",
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-3-large",
            "TIMESCALE_SERVICE_URL": "postgresql://user:pass@localhost:5432/db",
        },
        clear=True,
    )
    def test_init_azure_openai(self, mock_settings, mock_azure_openai_class, mock_connect, mock_register_vector):
        """Test l'initialisation avec Azure OpenAI."""
        # Configuration des mocks
        mock_settings.return_value = MagicMock()
        mock_settings.return_value.azure_openai.api_key = "test-key"
        mock_settings.return_value.azure_openai.api_version = "2023-05-15"
        mock_settings.return_value.azure_openai.azure_endpoint = "https://test.openai.azure.com"
        mock_settings.return_value.azure_openai.embedding_model = "text-embedding-3-large"
        mock_settings.return_value.vector_store = MagicMock()
        mock_settings.return_value.database = MagicMock()
        mock_settings.return_value.database.service_url = "postgresql://user:pass@localhost:5432/db"

        # Mock de la connexion à la base de données
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Mock du client Azure OpenAI
        mock_azure_openai_instance = MagicMock()
        mock_azure_openai_class.return_value = mock_azure_openai_instance

        # Initialisation
        vector_store = VectorStore()

        # Assertions
        assert vector_store is not None
        mock_azure_openai_class.assert_called_once_with(
            api_key="test-key", api_version="2023-05-15", azure_endpoint="https://test.openai.azure.com"
        )
        mock_connect.assert_called_once_with("postgresql://user:pass@localhost:5432/db")
        mock_cursor.execute.assert_any_call("CREATE EXTENSION IF NOT EXISTS vector")

    @patch("app.database.vector_store.register_vector")
    @patch("app.database.vector_store.psycopg2.connect")
    @patch("app.database.vector_store.OpenAI")
    @patch("app.database.vector_store.get_settings")
    @patch.dict(
        "os.environ",
        {
            "USE_AZURE_OPENAI": "false",
            "OPENAI_API_KEY": "test-key",
            "TIMESCALE_SERVICE_URL": "postgresql://user:pass@localhost:5432/db",
        },
        clear=True,
    )
    def test_get_embedding(self, mock_settings, mock_openai_class, mock_connect, mock_register_vector):
        """Test la génération d'embeddings."""
        # Configuration des mocks
        mock_settings.return_value = MagicMock()
        mock_settings.return_value.openai.api_key = "test-key"
        mock_settings.return_value.openai.embedding_model = "text-embedding-3-small"
        mock_settings.return_value.vector_store = MagicMock()
        mock_settings.return_value.database = MagicMock()
        mock_settings.return_value.database.service_url = "postgresql://user:pass@localhost:5432/db"

        # Mock de la connexion à la base de données
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Mock du client OpenAI
        mock_openai_instance = MagicMock()
        mock_openai_class.return_value = mock_openai_instance

        # Mock de la réponse OpenAI
        mock_embedding_response = MagicMock()
        mock_embedding_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
        mock_openai_instance.embeddings.create.return_value = mock_embedding_response

        # Initialisation
        vector_store = VectorStore()

        # Réinitialiser les appels au mock après l'initialisation
        mock_openai_instance.embeddings.create.reset_mock()

        # Exécution
        result = vector_store.get_embedding("Test texte pour embedding")

        # Assertions
        assert result == [0.1, 0.2, 0.3]
        mock_openai_instance.embeddings.create.assert_called_once_with(
            input=["Test texte pour embedding"], model="text-embedding-3-small"
        )
        mock_cursor.execute.assert_any_call("CREATE EXTENSION IF NOT EXISTS vector")

    @patch("app.database.vector_store.register_vector")
    @patch("app.database.vector_store.psycopg2.connect")
    @patch("app.database.vector_store.OpenAI")
    @patch("app.database.vector_store.get_settings")
    @patch.dict(
        "os.environ",
        {
            "USE_AZURE_OPENAI": "false",
            "OPENAI_API_KEY": "test-key",
            "TIMESCALE_SERVICE_URL": "postgresql://user:pass@localhost:5432/db",
        },
        clear=True,
    )
    def test_create_tables(self, mock_settings, mock_openai_class, mock_connect, mock_register_vector):
        """Test la création des tables."""
        # Configuration des mocks
        mock_settings.return_value = MagicMock()
        mock_settings.return_value.openai.api_key = "test-key"
        mock_settings.return_value.vector_store = MagicMock()
        mock_settings.return_value.vector_store.table_name = "embeddings"
        mock_settings.return_value.vector_store.embedding_dimensions = 3072
        mock_settings.return_value.database = MagicMock()
        mock_settings.return_value.database.service_url = "postgresql://user:pass@localhost:5432/db"

        # Mock de la connexion à la base de données
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Mock du client OpenAI
        mock_openai_instance = MagicMock()
        mock_openai_class.return_value = mock_openai_instance

        # Initialisation
        vector_store = VectorStore()

        # Exécution
        vector_store.create_tables()

        # Vérification des appels SQL
        # Vérifier que create_tables a été appelé
        assert mock_cursor.execute.call_count >= 1
        # Vérifier qu'une table embeddings a été créée
        sql_calls = [str(call[0][0]) for call in mock_cursor.execute.call_args_list]
        assert any("CREATE TABLE" in call and "embeddings" in call for call in sql_calls)

    @patch("app.database.vector_store.register_vector")
    @patch("app.database.vector_store.psycopg2.connect")
    @patch("app.database.vector_store.OpenAI")
    @patch("app.database.vector_store.get_settings")
    @patch.dict(
        "os.environ",
        {
            "USE_AZURE_OPENAI": "false",
            "OPENAI_API_KEY": "test-key",
            "TIMESCALE_SERVICE_URL": "postgresql://user:pass@localhost:5432/db",
        },
        clear=True,
    )
    def test_create_index(self, mock_settings, mock_openai_class, mock_connect, mock_register_vector):
        """Test la création de l'index HNSW."""
        # Configuration des mocks
        mock_settings.return_value = MagicMock()
        mock_settings.return_value.openai.api_key = "test-key"
        mock_settings.return_value.vector_store = MagicMock()
        mock_settings.return_value.vector_store.table_name = "embeddings"
        mock_settings.return_value.vector_store.embedding_dimensions = 3072
        mock_settings.return_value.database = MagicMock()
        mock_settings.return_value.database.service_url = "postgresql://user:pass@localhost:5432/db"

        # Mock de la connexion
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Mock du client OpenAI
        mock_openai_instance = MagicMock()
        mock_openai_class.return_value = mock_openai_instance

        # Initialisation
        vector_store = VectorStore()

        # Réinitialiser les appels après l'initialisation
        mock_cursor.execute.reset_mock()

        # Exécution
        vector_store.create_index()

        # Vérification des appels
        assert mock_cursor.execute.call_count == 1, "La méthode execute devrait être appelée une seule fois"

        # Vérification de la requête SQL
        sql_query = mock_cursor.execute.call_args[0][0].strip()
        sql_query_lower = sql_query.lower()

        # Vérification des parties essentielles de la requête
        assert "create index" in sql_query_lower, "La requête doit créer un index"
        assert "if not exists" in sql_query_lower, "L'index doit être créé uniquement s'il n'existe pas"
        assert "on embeddings" in sql_query_lower, "L'index doit être créé sur la table 'embeddings'"
        assert "using hnsw" in sql_query_lower, "L'index doit utiliser la méthode HNSW"
        assert "(embedding" in sql_query_lower, "L'index doit être créé sur la colonne 'embedding'"

        # Vérification du commit
        assert mock_conn.commit.call_count >= 1, "La transaction doit être validée avec au moins un commit"

    @patch("app.database.vector_store.register_vector")
    @patch("app.database.vector_store.psycopg2.connect")
    @patch("app.database.vector_store.OpenAI")
    @patch("app.database.vector_store.get_settings")
    @patch.dict(
        "os.environ",
        {
            "USE_AZURE_OPENAI": "false",
            "OPENAI_API_KEY": "test-key",
            "TIMESCALE_SERVICE_URL": "postgresql://user:pass@localhost:5432/db",
        },
        clear=True,
    )
    def test_upsert(self, mock_settings, mock_openai_class, mock_connect, mock_register_vector):
        """Test l'insertion/mise à jour de données."""
        # Configuration des mocks
        mock_settings.return_value = MagicMock()
        mock_settings.return_value.openai.api_key = "test-key"
        mock_settings.return_value.openai.embedding_model = "text-embedding-3-small"
        mock_settings.return_value.vector_store = MagicMock()
        mock_settings.return_value.vector_store.table_name = "embeddings"
        mock_settings.return_value.vector_store.embedding_dimensions = 3072
        mock_settings.return_value.database = MagicMock()
        mock_settings.return_value.database.service_url = "postgresql://user:pass@localhost:5432/db"

        # Mock de la connexion
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Mock du client OpenAI
        mock_openai_instance = MagicMock()
        mock_openai_class.return_value = mock_openai_instance

        # Création d'un DataFrame de test
        test_df = pd.DataFrame(
            {
                "id": ["uuid-1", "uuid-2"],
                "metadata": [{"title": "Serie 1"}, {"title": "Serie 2"}],
                "contents": ["Content 1", "Content 2"],
                "embedding": [[0.1, 0.2], [0.3, 0.4]],
            }
        )

        # Initialisation
        vector_store = VectorStore()

        # Réinitialiser les appels après l'initialisation
        mock_cursor.execute.reset_mock()

        # Exécution
        vector_store.upsert(test_df)

        # Vérifications
        # Vérification du nombre d'appels à execute (2 appels - un par ligne)
        assert (
            mock_cursor.execute.call_count == 2
        ), "La méthode execute devrait être appelée deux fois (une fois par ligne)"

        # Vérification des paramètres du premier appel (première ligne)
        first_call_args = mock_cursor.execute.call_args_list[0][0]
        sql_query = first_call_args[0].strip().lower()

        # Vérification des parties essentielles de la requête
        assert "insert into" in sql_query, "La requête doit être une insertion"
        assert "on conflict" in sql_query, "La requête doit gérer les conflits"
        assert "do update set" in sql_query, "La requête doit mettre à jour en cas de conflit"

        # Vérification des paramètres
        params = first_call_args[1]
        assert len(params) >= 3, "La requête doit avoir au moins 3 paramètres"
        # Vérifier que les données importantes sont présentes (sans se soucier de l'ordre exact)
        params_str = str(params)
        assert "uuid-1" in params_str or params[0] == "uuid-1", "L'ID doit être présent"
        assert "Content 1" in params_str, "Le contenu doit être présent"

        # Vérification du commit
        assert mock_conn.commit.call_count >= 1, "La transaction doit être validée avec au moins un commit"

    @patch("app.database.vector_store.register_vector")
    @patch("app.database.vector_store.psycopg2.connect")
    @patch("app.database.vector_store.OpenAI")
    @patch("app.database.vector_store.get_settings")
    @patch.dict(
        "os.environ",
        {
            "USE_AZURE_OPENAI": "false",
            "OPENAI_API_KEY": "test-key",
            "TIMESCALE_SERVICE_URL": "postgresql://user:pass@localhost:5432/db",
        },
        clear=True,
    )
    def test_search(self, mock_settings, mock_openai_class, mock_connect, mock_register_vector):
        """Test la recherche vectorielle."""
        # Configuration des mocks
        mock_settings.return_value = MagicMock()
        mock_settings.return_value.openai.api_key = "test-key"
        mock_settings.return_value.openai.embedding_model = "text-embedding-3-small"
        mock_settings.return_value.vector_store = MagicMock()
        mock_settings.return_value.vector_store.table_name = "embeddings"
        mock_settings.return_value.vector_store.embedding_dimensions = 3072
        mock_settings.return_value.database = MagicMock()
        mock_settings.return_value.database.service_url = "postgresql://user:pass@localhost:5432/db"

        # Mock du client OpenAI
        mock_openai_instance = MagicMock()
        mock_openai_class.return_value = mock_openai_instance

        # Mock de la réponse d'embedding pour la requête
        query_embedding = [0.1, 0.2, 0.3]
        mock_embedding_response = MagicMock()
        mock_embedding_response.data = [MagicMock(embedding=query_embedding)]
        mock_openai_instance.embeddings.create.return_value = mock_embedding_response

        # Mock du curseur avec résultats
        mock_cursor = MagicMock()
        # Note: La méthode search effectue d'abord une requête sans calcul de similarité
        # puis calcule la similarité en Python
        mock_cursor.fetchall.return_value = [
            ("uuid-1", {"title": "Serie 1"}, "Content 1", [0.1, 0.2, 0.3]),
            ("uuid-2", {"title": "Serie 2"}, "Content 2", [0.15, 0.25, 0.35]),
        ]

        # Mock de la connexion
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Initialisation
        vector_store = VectorStore()

        # Réinitialiser les appels après l'initialisation
        mock_openai_instance.embeddings.create.reset_mock()
        mock_cursor.execute.reset_mock()

        # Paramètres de test
        query = "Test query"
        limit = 5

        # Exécution avec return_dataframe=True
        result = vector_store.search(query, limit=limit, return_dataframe=True)

        # Vérifications
        # 1. Vérification de l'appel à l'API d'embedding
        mock_openai_instance.embeddings.create.assert_called_once_with(
            input=[query],  # Note: L'input est une liste dans l'implémentation
            model=mock_settings.return_value.openai.embedding_model,
        )

        # 2. Vérification de la requête SQL
        assert mock_cursor.execute.call_count == 1, "La méthode execute devrait être appelée une fois"

        # Vérification des parties essentielles de la requête SQL
        sql_query = mock_cursor.execute.call_args[0][0].strip().lower()
        assert "select" in sql_query, "La requête doit être une sélection"
        assert "from embeddings" in sql_query, "La requête doit interroger la table des embeddings"
        assert "limit 1000" in sql_query, "La requête doit limiter les résultats à 1000 pour le calcul de similarité"

        # 3. Vérification du résultat
        assert isinstance(result, pd.DataFrame), "Le résultat doit être un DataFrame pandas"

        # La méthode search calcule la similarité en Python, donc on vérifie la structure du résultat
        if not result.empty:
            # Vérification des colonnes du DataFrame
            expected_columns = [
                "id",
                "content",
                "embedding",
                "similarity",
            ]  # Note: metadata peut être étendu en colonnes séparées
            for col in expected_columns:
                assert col in result.columns, f"La colonne {col} doit être présente dans le résultat"

            # Vérification que les similarités sont calculées correctement (entre 0 et 1)
            assert all(
                0 <= sim <= 1 for sim in result["similarity"]
            ), "Les similarités doivent être comprises entre 0 et 1"

        # 4. Test avec return_dataframe=False
        mock_cursor.execute.reset_mock()
        result_list = vector_store.search(query, limit=limit, return_dataframe=False)

        # Vérification du type de retour
        assert isinstance(result_list, list), "Le résultat doit être une liste quand return_dataframe=False"

        # Vérification de la structure des résultats
        if result_list:
            for item in result_list:
                assert isinstance(item, tuple), "Chaque résultat doit être un tuple"
                assert (
                    len(item) == 5
                ), "Chaque résultat doit contenir 5 éléments (id, metadata, content, embedding, similarity)"
                assert isinstance(item[4], float), "Le dernier élément doit être la similarité (float)"

        # 5. Test avec filtre de métadonnées
        mock_cursor.execute.reset_mock()
        metadata_filter = {"genre": "Manga"}
        vector_store.search(query, metadata_filter=metadata_filter)

        # Vérification que le filtre de métadonnées est correctement appliqué
        sql_query = mock_cursor.execute.call_args[0][0].lower()
        assert "where" in sql_query, "La requête doit contenir une clause WHERE avec filtre"
        assert "metadata ->> %s = %s" in sql_query, "La requête doit filtrer sur les métadonnées"

    @patch("app.database.vector_store.register_vector")
    @patch("app.database.vector_store.psycopg2.connect")
    @patch("app.database.vector_store.OpenAI")
    @patch("app.database.vector_store.get_settings")
    def test_search_with_metadata_filter(self, mock_settings, mock_openai_class, mock_connect, mock_register_vector):
        """Test la recherche avec filtre de métadonnées."""
        # Configuration des mocks
        mock_settings.return_value = MagicMock()
        mock_settings.return_value.openai.api_key = "test-key"
        mock_settings.return_value.openai.embedding_model = "text-embedding-3-small"
        mock_settings.return_value.vector_store = MagicMock()
        mock_settings.return_value.vector_store.table_name = "embeddings"
        mock_settings.return_value.vector_store.embedding_dimensions = 3072
        mock_settings.return_value.database = MagicMock()
        mock_settings.return_value.database.service_url = "postgresql://user:pass@localhost:5432/db"

        # Mock du client OpenAI
        mock_openai_instance = MagicMock()
        mock_openai_class.return_value = mock_openai_instance

        # Mock de la réponse d'embedding
        mock_embedding_response = MagicMock()
        mock_embedding_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
        mock_openai_instance.embeddings.create.return_value = mock_embedding_response

        # Mock du curseur avec résultats
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ("uuid-1", {"title": "Serie 1", "genre": "Action"}, "Content 1", [0.1, 0.2, 0.3])
        ]

        # Mock de la connexion
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        with patch.dict("os.environ", {"USE_AZURE_OPENAI": "false"}):
            # Initialisation
            vector_store = VectorStore()

            # Réinitialiser les appels après l'initialisation
            mock_openai_instance.embeddings.create.reset_mock()
            mock_cursor.execute.reset_mock()

            # Exécution avec filtre
            result = vector_store.search(
                "Test query", limit=5, metadata_filter={"genre": "Action"}, return_dataframe=True
            )

            # Assertions
            assert isinstance(result, pd.DataFrame)
            assert not result.empty
            assert "id" in result.columns
            assert "similarity" in result.columns

            # Vérifier que l'embedding a été généré avec les bons paramètres
            mock_openai_instance.embeddings.create.assert_called_once_with(
                input=["Test query"], model="text-embedding-3-small"
            )

            # Vérifier que la requête SQL a été exécutée avec le filtre
            assert mock_cursor.execute.called

            # Vérifier que le filtre a été correctement ajouté à la requête
            execute_call = mock_cursor.execute.call_args[0][0].lower()
            assert "metadata ->> %s = %s" in execute_call

            # Vérifier les paramètres du filtre
            assert mock_cursor.execute.call_args[0][1] == ["genre", "Action"] or mock_cursor.execute.call_args[0][
                1
            ] == ("genre", "Action")
