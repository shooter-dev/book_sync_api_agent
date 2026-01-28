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

from prometheus_client import Counter, Histogram, Gauge, Summary, REGISTRY
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

# === MÉTRIQUES ADDITIONNELLES POUR DASHBOARD AVANCÉ (compatibles Azure Monitor/Grafana) ===

# Compteur du nombre total d'opérations (toutes requêtes confondues) avec label agent
# (Grafana attend total_operations et total_operations{agent="..."})
total_operations = Counter(
    "total_operations",
    "Nombre total d'opérations exécutées par l'agent",
    ["agent"],
    registry=REGISTRY
)

# Compteur du nombre total d'opérations (toutes requêtes confondues) avec label agent
# (Grafana attend total_operations2 et total_operations2{agent="..."})
total_operations2 = Counter(
    "total_operations2",
    "Nombre total d'opérations exécutées par l'agent (debug)",
    ["agent"],
    registry=REGISTRY
)

# Compteur des tokens d'entrée et de sortie (pour compatibilité dashboard Azure) avec label agent
input_tokens_total = Counter(
    "input_tokens_total",
    "Total des tokens d'entrée consommés",
    ["agent"]
)
output_tokens_total = Counter(
    "output_tokens_total",
    "Total des tokens de sortie générés",
    ["agent"]
)

# Histogramme du temps de réponse (pour P95/P99/avg)
response_time_seconds = Histogram(
    "response_time_seconds",
    "Temps de réponse de l'agent en secondes",
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30]
)

# Compteur de succès/erreur global (pour taux de succès)
success_total = Counter(
    "success_total",
    "Nombre de requêtes réussies"
)
error_total = Counter(
    "error_total",
    "Nombre de requêtes en erreur par type",
    ["error_type"]
)
# Pour compatibilité avec les panels sans label
error_total_global = Counter(
    "error_total_global",
    "Nombre total de requêtes en erreur (tous types confondus)"
)

# Coût estimé en dollars (pour panel coût)
cost_dollars_total = Counter(
    "cost_dollars_total",
    "Coût estimé total en dollars"
)

def get_agent_label(user_profile):
    """
    Récupère le nom de l'agent à partir du profil utilisateur ou retourne 'default'.
    """
    if isinstance(user_profile, dict):
        agent = user_profile.get("agent") or user_profile.get("user_genre")
        if agent:
            return str(agent)
    return "default"


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
            response_time_seconds.observe(latency)  # Ajout pour dashboard avancé
            self.start_time = None

        status = "success" if success else "error"
        prediction_requests_total.labels(status=status).inc()
        total_operations.labels(agent="default").inc()  # Compte toutes les opérations

        if success:
            success_total.inc()
        else:
            error_total.labels(error_type="unknown").inc()
            error_total_global.inc()

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
        cost_dollars_total.inc(cost)  # Ajout pour dashboard avancé

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


def force_all_metrics():
    """
    Force l'existence de toutes les metriques pour tous les labels attendus.

    Cette fonction initialise toutes les metriques Prometheus avec une valeur de 0
    pour garantir leur visibilite dans Grafana des le demarrage de l'application,
    meme si aucune requete n'a encore ete traitee.

    Metriques initialisees:
    - total_operations (par agent)
    - input_tokens_total / output_tokens_total (par agent)
    - prediction_requests_total (par status)
    - error_total (par error_type)
    - llm_errors_total (par error_type)
    - vector_searches_total (par status)
    - success_total, error_total_global, cost_dollars_total
    """
    # Liste des agents possibles (inclut debug utilise dans main.py)
    agents = ["default", "homme", "femme", "Homme", "Femme", "debug"]

    # Initialisation des metriques par agent
    for agent in agents:
        total_operations.labels(agent=agent).inc(0)
        total_operations2.labels(agent=agent).inc(0)
        input_tokens_total.labels(agent=agent).inc(0)
        output_tokens_total.labels(agent=agent).inc(0)

    # Initialisation des metriques de prediction par status
    prediction_requests_total.labels(status="success").inc(0)
    prediction_requests_total.labels(status="error").inc(0)

    # Initialisation des metriques d'erreur par type
    error_types = ["none", "unknown", "timeout", "rate_limit", "api_error", "predict_error", "connection_error"]
    for error_type in error_types:
        error_total.labels(error_type=error_type).inc(0)
        llm_errors_total.labels(error_type=error_type).inc(0)

    # Initialisation des metriques de recherche vectorielle par status
    vector_searches_total.labels(status="success").inc(0)
    vector_searches_total.labels(status="error").inc(0)

    # Initialisation des metriques de tokens par type
    tokens_consumed.labels(type="prompt").inc(0)
    tokens_consumed.labels(type="completion").inc(0)

    # Initialisation des compteurs globaux
    success_total.inc(0)
    error_total_global.inc(0)
    cost_dollars_total.inc(0)

    # Initialisation du score de similarite avec une valeur par defaut
    similarity_score.set(0)


# === Instance globale du collecteur pour import direct ===
metrics_collector = LLMMetricsCollector()

# === Initialisation automatique des metriques au chargement du module ===
# Cela garantit que toutes les metriques sont visibles dans Grafana
# des le demarrage de l'application
force_all_metrics()
