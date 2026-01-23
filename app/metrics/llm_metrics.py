"""
Module de métriques LLMOps pour le monitoring des appels LLM.

Ce module collecte et expose les métriques importantes pour surveiller
les performances et les coûts des appels à l'API Azure OpenAI.

=== ARCHITECTURE LLMOPS ===

LLMOps (Large Language Model Operations) est une approche de monitoring
adaptée aux applications utilisant des LLM comme GPT-4. Contrairement au
MLOps classique qui surveille des modèles entraînés, LLMOps se concentre sur:

1. LATENCE: Temps de réponse des appels API (critique pour l'UX)
2. TOKENS: Consommation de tokens (facturation OpenAI/Azure)
3. COÛTS: Estimation des coûts en temps réel
4. QUALITÉ: Score de similarité des résultats vectoriels
5. ERREURS: Taux d'erreurs par type (timeout, rate limit, etc.)

=== PROMETHEUS ===

Prometheus est un système de monitoring open-source qui:
- Collecte les métriques via HTTP (endpoint /metrics)
- Stocke les données en séries temporelles
- Permet des requêtes avec PromQL

Types de métriques Prometheus utilisés ici:
- Counter: Compteur qui ne fait qu'augmenter (requêtes, tokens, erreurs)
- Histogram: Distribution des valeurs (latence, nombre de résultats)
- Gauge: Valeur qui peut monter ou descendre (similarité actuelle)
- Summary: Calcul de quantiles (coûts estimés)

=== GRAFANA ===

Grafana est l'outil de visualisation qui:
- Se connecte à Prometheus comme source de données
- Affiche des dashboards avec graphiques et alertes
- Permet de créer des alertes (ex: latence > 5s, coût > 10$/jour)

Exemple de requête PromQL pour Grafana:
- Latence P95: histogram_quantile(0.95, llm_request_latency_seconds_bucket)
- Tokens/heure: increase(llm_tokens_consumed_total[1h])
- Taux d'erreur: rate(llm_errors_total[5m])
"""

from prometheus_client import Counter, Histogram, Gauge, Summary
import time


# =============================================================================
# MÉTRIQUES PROMETHEUS POUR LLMOPS
# =============================================================================
# Ces métriques sont exposées sur l'endpoint /metrics et collectées par Prometheus

# Compteur du nombre total de requêtes de prédiction
# Utilisation Grafana: rate(prediction_requests_total[5m]) pour voir le débit
prediction_requests_total = Counter(
    "prediction_requests_total",
    "Nombre total de requêtes de prédiction",
    ["status"]  # success, error
)

# Histogramme de la latence des requêtes LLM
# IMPORTANT pour LLMOps: Les LLM ont des latences variables (1-30s)
# Grafana: histogram_quantile(0.95, llm_request_latency_seconds_bucket)
llm_request_latency = Histogram(
    "llm_request_latency_seconds",
    "Latence des requêtes LLM en secondes",
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

# Compteur des tokens consommés
# CRITIQUE pour LLMOps: Les tokens = facturation Azure OpenAI
# Grafana: increase(llm_tokens_consumed_total{type="prompt"}[1h])
tokens_consumed = Counter(
    "llm_tokens_consumed_total",
    "Nombre total de tokens consommés",
    ["type"]  # prompt, completion
)

# Gauge pour la similarité moyenne des résultats
# Indicateur de qualité: plus le score est haut, meilleurs sont les résultats
# Grafana: vector_similarity_score pour voir la qualité en temps réel
similarity_score = Gauge(
    "vector_similarity_score",
    "Score de similarité moyen des résultats vectoriels"
)

# Compteur des erreurs par type
# Permet d'identifier les problèmes: timeout, rate_limit, api_error
# Grafana: rate(llm_errors_total{error_type="rate_limit"}[5m])
llm_errors_total = Counter(
    "llm_errors_total",
    "Nombre total d'erreurs LLM",
    ["error_type"]  # timeout, rate_limit, api_error, etc.
)

# Summary pour les coûts estimés
# CRITIQUE pour LLMOps: Suivre les coûts en temps réel
# Grafana: llm_estimated_cost_dollars_sum pour le coût total
estimated_cost = Summary(
    "llm_estimated_cost_dollars",
    "Coût estimé des requêtes LLM en dollars"
)

# Compteur des recherches vectorielles
# Surveille les appels à la base vectorielle (pgvector/Timescale)
vector_searches_total = Counter(
    "vector_searches_total",
    "Nombre total de recherches vectorielles",
    ["status"]
)

# Histogramme du nombre de résultats par recherche
# Permet de voir si les recherches retournent assez de résultats
vector_results_count = Histogram(
    "vector_results_count",
    "Nombre de résultats par recherche vectorielle",
    buckets=[0, 1, 5, 10, 20, 50]
)


class LLMMetricsCollector:
    """
    Collecteur de métriques pour les appels LLM.

    Cette classe fournit des méthodes simples pour enregistrer
    les métriques des appels à Azure OpenAI.
    """

    # Prix approximatifs par 1000 tokens (GPT-4o-mini)
    PRICE_PER_1K_PROMPT_TOKENS = 0.00015
    PRICE_PER_1K_COMPLETION_TOKENS = 0.0006

    def __init__(self):
        self.start_time = None

    def start_request(self):
        """Démarre le chronomètre pour mesurer la latence."""
        self.start_time = time.time()

    def end_request(self, success=True):
        """
        Termine la mesure et enregistre les métriques de base.

        Args:
            success: True si la requête a réussi, False sinon
        """
        if self.start_time:
            latency = time.time() - self.start_time
            llm_request_latency.observe(latency)
            self.start_time = None

        status = "success" if success else "error"
        prediction_requests_total.labels(status=status).inc()

    def record_tokens(self, prompt_tokens, completion_tokens):
        """
        Enregistre le nombre de tokens consommés.

        Args:
            prompt_tokens: Nombre de tokens dans le prompt
            completion_tokens: Nombre de tokens dans la réponse
        """
        tokens_consumed.labels(type="prompt").inc(prompt_tokens)
        tokens_consumed.labels(type="completion").inc(completion_tokens)

        # Calcul du coût estimé
        cost = (
            (prompt_tokens / 1000) * self.PRICE_PER_1K_PROMPT_TOKENS +
            (completion_tokens / 1000) * self.PRICE_PER_1K_COMPLETION_TOKENS
        )
        estimated_cost.observe(cost)

    def record_similarity(self, avg_similarity):
        """
        Enregistre le score de similarité moyen.

        Args:
            avg_similarity: Score de similarité moyen (0-1)
        """
        if avg_similarity is not None:
            similarity_score.set(avg_similarity)

    def record_error(self, error_type):
        """
        Enregistre une erreur LLM.

        Args:
            error_type: Type d'erreur (timeout, rate_limit, api_error, etc.)
        """
        llm_errors_total.labels(error_type=error_type).inc()

    def record_vector_search(self, success=True, results_count=0):
        """
        Enregistre une recherche vectorielle.

        Args:
            success: True si la recherche a réussi
            results_count: Nombre de résultats retournés
        """
        status = "success" if success else "error"
        vector_searches_total.labels(status=status).inc()
        vector_results_count.observe(results_count)


# Instance globale du collecteur
metrics_collector = LLMMetricsCollector()
