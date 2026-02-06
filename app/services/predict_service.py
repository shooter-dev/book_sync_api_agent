import logging
import time
from typing import Optional, Dict, Any, List

from app.database.vector_store import VectorStore
from app.models.predict_request import PredictRequest
from app.models.predict_response import PredictResponse, RecommendedSerie
from app.services.synthesizer import Synthesizer
from app.metrics.llm_metrics import (
    metrics_collector,
    total_operations,
    input_tokens_total,
    output_tokens_total,
    response_time_seconds,
    success_total,
    error_total,
    error_total_global,
    cost_dollars_total,
    get_agent_label,
    prediction_requests_total,
    llm_errors_total
)


class PredictService:
    """Service pour gérer les prédictions basées sur la recherche vectorielle."""

    def __init__(self):
        self.vector_store = VectorStore()
        self.synthesizer = Synthesizer()

    def _search_similar_volumes(self, request: PredictRequest, limit: int = 10):
        """
        Recherche les volumes similaires à la collection et aux volumes lus de l'utilisateur.
        """
        all_results = []

        try:
            # Rechercher des volumes similaires à ceux de la collection
            if request.collection:
                for serie_name, serie_data in request.collection.items():
                    if isinstance(serie_data, dict) and "volumes" in serie_data:
                        # Utiliser le nom de la série pour la recherche
                        search_query = f"Serie: {serie_name} Genre: {request.category_preference}"

                        results = self.vector_store.search(query_text=search_query, limit=5, return_dataframe=True)

                        if not results.empty:
                            all_results.append(results)

            # Rechercher des volumes similaires à ceux déjà lus
            if request.read and request.read != "{}":
                read_data = request.read if isinstance(request.read, dict) else {}
                for serie_name, serie_data in read_data.items():
                    if isinstance(serie_data, dict) and "volumes" in serie_data:
                        # Utiliser le nom de la série pour la recherche
                        search_query = f"Serie: {serie_name} Genre: {request.category_preference}"

                        results = self.vector_store.search(query_text=search_query, limit=5, return_dataframe=True)

                        if not results.empty:
                            all_results.append(results)

            # Si pas de collection/lecture, recherche basée sur les préférences
            if not all_results:
                mood_text = f" {request.user_mood}" if request.user_mood else ""
                search_query = f"Genre: {request.category_preference}{mood_text} manga"

                results = self.vector_store.search(query_text=search_query, limit=limit, return_dataframe=True)

                if not results.empty:
                    all_results.append(results)

            # Combiner tous les résultats
            if all_results:
                import pandas as pd

                combined_results = pd.concat(all_results, ignore_index=True)

                # Supprimer les doublons basés sur serie_title dans metadata
                if not combined_results.empty and "metadata" in combined_results.columns:
                    seen_series = set()
                    unique_results = []

                    for _, row in combined_results.iterrows():
                        metadata = row.get("metadata", {})
                        if isinstance(metadata, dict):
                            serie_title = metadata.get("serie_title", "")
                            if serie_title and serie_title not in seen_series:
                                seen_series.add(serie_title)
                                unique_results.append(row)

                    if unique_results:
                        return pd.DataFrame(unique_results).head(limit)

                return combined_results.head(limit)

            # Retourner un DataFrame vide si aucun résultat
            import pandas as pd

            return pd.DataFrame()

        except Exception as e:
            logging.error(f"Erreur lors de la recherche de volumes similaires: {e}")
            import pandas as pd

            return pd.DataFrame()

    def _extract_series_recommendations(self, search_results, request: PredictRequest) -> List[RecommendedSerie]:
        """
        Extrait les recommandations de séries avec id_series et format demandé.
        """
        recommended_series = []

        if search_results.empty:
            return recommended_series

        for _, row in search_results.iterrows():
            try:
                # Les métadonnées sont étendues dans les colonnes du DataFrame
                serie_title = row.get("serie_title", "")
                serie_id = row.get("serie_id", "")
                genre = row.get("genre", "")
                category = row.get("categorie", "")
                similarity_score = row.get("similarity", 0.0)

                print(f"Serie: {serie_title} | Score: {similarity_score:.4f} | Genre: {genre}")

                if serie_title and serie_id:
                    # Générer une réponse IA personnalisée
                    reason = self._generate_ai_response(serie_title, genre, category, request)

                    recommended_series.append(
                        RecommendedSerie(title=serie_title, id_series=serie_id, responce_IA=reason)
                    )

            except Exception as e:
                logging.warning(f"Erreur lors de l'extraction de la série: {e}")
                continue

        return recommended_series

    def _generate_ai_response(self, title: str, genre: str, category: str, request: PredictRequest) -> str:
        """
        Génère une réponse IA personnalisée pour chaque série recommandée.
        """
        reasons = []

        # Correspondance avec les préférences
        if request.category_preference.lower() in genre.lower():
            reasons.append(f"correspond à votre goût pour le {request.category_preference}")

        # Correspondance avec l'humeur
        if request.user_mood:
            if request.user_mood.lower() == "énervé" and any(
                word in genre.lower() for word in ["action", "combat", "aventure"]
            ):
                reasons.append("parfait pour évacuer votre énervement")
            elif request.user_mood.lower() == "comique" and any(
                word in genre.lower() for word in ["comédie", "humour"]
            ):
                reasons.append("idéal pour votre humeur comique")

        # Correspondance avec l'âge
        if category.lower() == "seinen" and int(request.user_age) >= 18:
            reasons.append("adapté à votre maturité")
        elif category.lower() == "shonen":
            reasons.append("style dynamique et accessible")

        # Raison par défaut
        if not reasons:
            reasons.append(f"recommandé pour les amateurs de {genre}")

        return f"{title} - {' et '.join(reasons[:2])}"

    async def predict(self, request: PredictRequest) -> PredictResponse:
        """
        Effectue une prédiction basée sur le profil utilisateur et ses préférences.

        Cette méthode utilise le collecteur de métriques LLMOps pour surveiller:
        - La latence des requêtes
        - Le nombre de résultats de recherche vectorielle
        - Les erreurs éventuelles
        """
        metrics_collector.start_request()
        op_start = time.time()
        agent_label = get_agent_label({
            "user_age": getattr(request, "user_age", None),
            "user_genre": getattr(request, "user_genre", None),
            "agent": getattr(request, "agent", None)
        })
        try:
            print("=== DEBUT PREDICT SERVICE ===")
            print(f"Profil: {request.user_genre} {request.user_age} ans")
            print(f"Préférences: {request.genre_preference} - {request.category_preference}")
            print(f"Humeur: {request.user_mood}")
            print(f"Type: {request.prediction_type}")

            # Rechercher les volumes similaires (10 max)
            search_results = self._search_similar_volumes(request, limit=10)
            print(f"Résultats trouvés: {len(search_results)}")

            # Enregistrer les métriques de recherche vectorielle
            metrics_collector.record_vector_search(
                success=not search_results.empty,
                results_count=len(search_results)
            )

            # Extraire les séries recommandées
            recommended_series = self._extract_series_recommendations(search_results, request)
            print(f"Séries extraites: {len(recommended_series)}")

            # Générer la réponse globale via l'agent IA
            if search_results.empty:
                context_text = "Aucun contexte spécifique trouvé."
            else:
                context_text = "Recommandations basées sur votre profil et vos préférences."

            # Préparer le profil pour l'agent
            user_profile = {
                "user_age": request.user_age,
                "user_genre": request.user_genre,
                "genre_preference": request.genre_preference,
                "category_preference": request.category_preference,
                "user_mood": request.user_mood,
                "prediction_type": request.prediction_type,
                "collection": request.collection,
                "read": request.read,
                # Ajout d'un champ agent si existant
                "agent": getattr(request, "agent", None)
            }
            agent_label = get_agent_label(user_profile)

            # Générer la réponse globale
            synthesizer_response, prompt_tokens, completion_tokens, avg_similarity = self.synthesizer.generate_global_response_with_metrics(
                recommended_series=recommended_series, user_profile=user_profile
            )
            # MOCK si tokens non fournis
            if prompt_tokens is None:
                prompt_tokens = 0
            if completion_tokens is None:
                completion_tokens = 0
            # Incrémentation systématique des métriques attendues
            input_tokens_total.labels(agent=agent_label).inc(prompt_tokens)
            output_tokens_total.labels(agent=agent_label).inc(completion_tokens)
            total_operations.labels(agent=agent_label).inc()
            success_total.inc()
            # Toujours incrémenter error_total avec 0 si succès (pour visibilité Prometheus)
            error_total.labels(error_type="none").inc(0)
            error_total_global.inc(0)
            # Enregistrer les metriques de tokens consommes
            metrics_collector.record_tokens(prompt_tokens, completion_tokens)
            # Enregistrer la similarite (si disponible)
            if avg_similarity is not None:
                metrics_collector.record_similarity(avg_similarity)
            # Enregistrer le succès de la requête (métriques LLMOps)
            metrics_collector.end_request(success=True)
            latency = time.time() - op_start
            response_time_seconds.observe(latency)
            cost = (
                (prompt_tokens / 1000) * metrics_collector.PRICE_PER_1K_PROMPT_TOKENS +
                (completion_tokens / 1000) * metrics_collector.PRICE_PER_1K_COMPLETION_TOKENS
            )
            cost_dollars_total.inc(cost)
            return PredictResponse(
                serie_recomendees=recommended_series, status="success", responce_IA_global=synthesizer_response
            )
        except Exception as e:
            logging.error(f"Erreur lors de la prédiction: {e}")
            metrics_collector.record_error(error_type="predict_error")
            metrics_collector.end_request(success=False)
            error_total.labels(error_type="predict_error").inc()
            error_total_global.inc()
            total_operations.labels(agent=agent_label).inc()
            # Toujours incrémenter les tokens à 0 en cas d'erreur
            input_tokens_total.labels(agent=agent_label).inc(0)
            output_tokens_total.labels(agent=agent_label).inc(0)
            latency = time.time() - op_start
            response_time_seconds.observe(latency)
            return PredictResponse(
                serie_recomendees=[], status="error", responce_IA_global=f"Une erreur s'est produite: {str(e)}"
            )
