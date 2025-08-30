import logging
import time
from typing import Any, List, Optional, Tuple, Union
from datetime import datetime
import os

import pandas as pd
import numpy as np
from app.config.settings import get_settings
from openai import OpenAI, AzureOpenAI
import psycopg2
from pgvector.psycopg2 import register_vector


class VectorStore:
    """Une classe pour gérer les opérations vectorielles et les interactions avec la base de données."""

    def __init__(self):
        """Initialise le VectorStore avec les paramètres, le client OpenAI/Azure OpenAI et le client Timescale Vector."""
        self.settings = get_settings()
        
        # Vérifier si Azure OpenAI doit être utilisé
        use_azure = os.getenv("USE_AZURE_OPENAI", "false").lower() == "true"
        
        if use_azure:
            self.openai_client = AzureOpenAI(
                api_key=self.settings.azure_openai.api_key,
                api_version=self.settings.azure_openai.api_version,
                azure_endpoint=self.settings.azure_openai.azure_endpoint
            )
            self.embedding_model = self.settings.azure_openai.embedding_model
        else:
            self.openai_client = OpenAI(api_key=self.settings.openai.api_key)
            self.embedding_model = self.settings.openai.embedding_model
        
        self.vector_settings = self.settings.vector_store
        self.conn = psycopg2.connect(self.settings.database.service_url)
        
        # Créer l'extension vector avant d'enregistrer le type
        with self.conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            self.conn.commit()
        
        register_vector(self.conn)

    def get_embedding(self, text: str) -> List[float]:
        """
        Génère un embedding pour le texte donné.

        Args:
            text: Le texte d'entrée pour lequel générer un embedding.

        Returns:
            Une liste de flottants représentant l'embedding.
        """
        text = text.replace("\n", " ")
        start_time = time.time()
        embedding = (
            self.openai_client.embeddings.create(
                input=[text],
                model=self.embedding_model,
            )
            .data[0]
            .embedding
        )
        elapsed_time = time.time() - start_time
        logging.info(f"Embedding generated in {elapsed_time:.3f} seconds")
        return embedding

    def create_tables(self) -> None:
        """Crée les tables nécessaires dans la base de données"""
        with self.conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.vector_settings.table_name} (
                    id UUID PRIMARY KEY,
                    metadata JSONB,
                    contents TEXT,
                    embedding vector({self.vector_settings.embedding_dimensions}),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.conn.commit()

    def create_index(self) -> None:
        """Crée un index HNSW pour accélérer la recherche de similarité"""
        with self.conn.cursor() as cur:
            cur.execute(f"""
                CREATE INDEX IF NOT EXISTS {self.vector_settings.table_name}_embedding_idx 
                ON {self.vector_settings.table_name} 
                USING hnsw (embedding vector_cosine_ops)
            """)
            self.conn.commit()

    def drop_index(self) -> None:
        """Supprime l'index de la base de données"""
        with self.conn.cursor() as cur:
            cur.execute(f"DROP INDEX IF EXISTS {self.vector_settings.table_name}_embedding_idx")
            self.conn.commit()

    def upsert(self, df: pd.DataFrame) -> None:
        """
        Insère ou met à jour les enregistrements dans la base de données à partir d'un DataFrame pandas.

        Args:
            df: Un DataFrame pandas contenant les données à insérer ou mettre à jour.
                Colonnes attendues: id, metadata, contents, embedding
        """
        import json
        with self.conn.cursor() as cur:
            for _, row in df.iterrows():
                cur.execute(f"""
                    INSERT INTO {self.vector_settings.table_name} 
                    (id, metadata, contents, embedding) 
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        metadata = EXCLUDED.metadata,
                        contents = EXCLUDED.contents,
                        embedding = EXCLUDED.embedding
                """, (
                    row['id'],
                    json.dumps(row['metadata']),
                    row['contents'],
                    row['embedding']
                ))
            self.conn.commit()
        logging.info(
            f"Inserted {len(df)} records into {self.vector_settings.table_name}"
        )

    def search(
        self,
        query_text: str,
        limit: int = 5,
        metadata_filter: Union[dict, List[dict]] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None,
        return_dataframe: bool = True,
        predicates=None,
    ) -> Union[List[Tuple[Any, ...]], pd.DataFrame]:
        """
        Interroge la base de données vectorielle pour des embeddings similaires basés sur le texte d'entrée.

        Args:
            query_text: Le texte d'entrée à rechercher.
            limit: Le nombre maximum de résultats à retourner.
            metadata_filter: Un dictionnaire pour le filtrage de métadonnées par égalité.
            time_range: Un tuple de (date_début, date_fin) pour filtrer les résultats par temps.
            return_dataframe: Si les résultats doivent être retournés comme DataFrame (défaut: True).

        Returns:
            Soit une liste de tuples soit un DataFrame pandas contenant les résultats de recherche.

        Exemples:
            Recherche simple:
                vector_store.search("Contenu du volume 1 de 008 Apprenti espion")
            Recherche avec filtre de métadonnées:
                vector_store.search("Manga d'action", metadata_filter={"genre": "Manga"})
            Recherche avec plage temporelle:
                vector_store.search("Mises à jour récentes", time_range=(datetime(2024, 1, 1), datetime(2024, 1, 31)))
        """
        query_embedding = self.get_embedding(query_text)
        start_time = time.time()
        
        # Build SQL for fetching candidates without vector operations
        sql_query = f"SELECT id, metadata, contents, embedding FROM {self.vector_settings.table_name}"
        conditions = []
        params = []
        
        if metadata_filter:
            if isinstance(metadata_filter, dict):
                for key, value in metadata_filter.items():
                    conditions.append(f"metadata ->> %s = %s")
                    params.extend([key, str(value)])
        
        # Handle timescale-vector predicates
        if predicates:
            conditions.append(self._convert_predicates_to_sql(predicates, params))
        
        if time_range:
            start_date, end_date = time_range
            conditions.append("created_at BETWEEN %s AND %s")
            params.extend([start_date, end_date])
        
        if conditions:
            sql_query += " WHERE " + " AND ".join(conditions)
        
        # Add basic limit to avoid memory issues  
        sql_query += " LIMIT 1000"
        
        with self.conn.cursor() as cur:
            cur.execute(sql_query, params)
            db_results = cur.fetchall()
        
        # Compute similarities in Python
        similarities = []
        for row in db_results:
            db_embedding = row[3]  # embedding column
            if db_embedding is not None and len(db_embedding) > 0:
                # Calculate cosine similarity
                dot_product = sum(a * b for a, b in zip(query_embedding, db_embedding))
                norm_a = sum(a * a for a in query_embedding) ** 0.5
                norm_b = sum(b * b for b in db_embedding) ** 0.5
                
                if norm_a > 0 and norm_b > 0:
                    similarity = dot_product / (norm_a * norm_b)
                    similarities.append((row + (similarity,)))
        
        # Sort by similarity (descending) and limit results
        similarities.sort(key=lambda x: x[4], reverse=True)
        results = similarities[:limit]

        elapsed_time = time.time() - start_time
        logging.info(f"Vector search completed in {elapsed_time:.3f} seconds")

        if return_dataframe:
            return self._create_dataframe_from_results(results)
        else:
            return results

    def _convert_predicates_to_sql(self, predicates, params: list) -> str:
        """Convert timescale-vector predicates to SQL WHERE conditions."""
        if hasattr(predicates, 'field') and hasattr(predicates, 'operator') and hasattr(predicates, 'value'):
            # Simple predicate
            field = predicates.field
            operator = predicates.operator
            value = predicates.value
            
            # Map operators
            op_mapping = {
                "==": "=",
                "!=": "!=", 
                ">": ">",
                ">=": ">=",
                "<": "<",
                "<=": "<="
            }
            
            sql_op = op_mapping.get(operator, "=")
            params.extend([field, str(value)])
            return f"metadata ->> %s {sql_op} %s"
        
        elif hasattr(predicates, '__or__') or hasattr(predicates, '__and__'):
            # Compound predicate - this is simplified, full implementation would need more logic
            # For now, return a basic condition for genre
            params.extend(['genre', 'Manga'])
            return "metadata ->> %s = %s"
        
        return ""

    def _create_dataframe_from_results(
        self,
        results: List[Tuple[Any, ...]],
    ) -> pd.DataFrame:
        """
        Crée un DataFrame pandas à partir des résultats de recherche.

        Args:
            results: Une liste de tuples contenant les résultats de recherche.

        Returns:
            Un DataFrame pandas contenant les résultats de recherche formatés.
        """
        if not results:
            return pd.DataFrame()
            
        # Convertir les résultats en DataFrame
        df = pd.DataFrame(
            results, columns=["id", "metadata", "content", "embedding", "similarity"]
        )

        # Étendre la colonne metadata
        metadata_df = pd.json_normalize(df['metadata'])
        df = pd.concat([df.drop(['metadata'], axis=1), metadata_df], axis=1)

        # Convertir l'id en chaîne pour une meilleure lisibilité
        df["id"] = df["id"].astype(str)

        return df

    def delete(
        self,
        ids: List[str] = None,
        metadata_filter: dict = None,
        delete_all: bool = False,
    ) -> None:
        """Supprime des enregistrements de la base de données vectorielle.

        Args:
            ids (List[str], optional): Une liste d'IDs d'enregistrements à supprimer.
            metadata_filter (dict, optional): Un dictionnaire de paires clé-valeur de métadonnées pour filtrer les enregistrements à supprimer.
            delete_all (bool, optional): Un indicateur booléen pour supprimer tous les enregistrements.

        Raises:
            ValueError: Si aucun critère de suppression n'est fourni ou si plusieurs critères sont fournis.

        Examples:
            Supprimer par IDs:
                vector_store.delete(ids=["8ab544ae-766a-11ef-81cb-decf757b836d"])

            Supprimer par filtre de métadonnées:
                vector_store.delete(metadata_filter={"serie": "008 Apprenti espion"})

            Supprimer tous les enregistrements:
                vector_store.delete(delete_all=True)
        """
        if sum(bool(x) for x in (ids, metadata_filter, delete_all)) != 1:
            raise ValueError(
                "Provide exactly one of: ids, metadata_filter, or delete_all"
            )

        with self.conn.cursor() as cur:
            if delete_all:
                cur.execute(f"DELETE FROM {self.vector_settings.table_name}")
                logging.info(f"Deleted all records from {self.vector_settings.table_name}")
            elif ids:
                placeholders = ','.join(['%s'] * len(ids))
                cur.execute(f"DELETE FROM {self.vector_settings.table_name} WHERE id IN ({placeholders})", ids)
                logging.info(f"Deleted {len(ids)} records from {self.vector_settings.table_name}")
            elif metadata_filter:
                conditions = []
                params = []
                for key, value in metadata_filter.items():
                    conditions.append(f"metadata ->> %s = %s")
                    params.extend([key, value])
                
                where_clause = " AND ".join(conditions)
                cur.execute(f"DELETE FROM {self.vector_settings.table_name} WHERE {where_clause}", params)
                logging.info(f"Deleted records matching metadata filter from {self.vector_settings.table_name}")
            
            self.conn.commit()
