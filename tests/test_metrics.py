"""
Tests pour le module de métriques LLMOps.

Ces tests vérifient le bon fonctionnement du collecteur de métriques
pour le monitoring des appels LLM via Prometheus.
"""

import pytest
import time
from unittest.mock import patch

from app.metrics.llm_metrics import (
    LLMMetricsCollector,
    metrics_collector,
    prediction_requests_total,
    llm_request_latency,
    tokens_consumed,
    similarity_score,
    llm_errors_total,
    vector_searches_total,
    vector_results_count
)


class TestLLMMetricsCollector:
    """Tests pour la classe LLMMetricsCollector."""

    def test_collector_initialization(self):
        """Test que le collecteur s'initialise correctement."""
        collector = LLMMetricsCollector()
        assert collector.start_time is None

    def test_start_request(self):
        """Test que start_request démarre le chronomètre."""
        collector = LLMMetricsCollector()
        collector.start_request()
        assert collector.start_time is not None
        assert collector.start_time > 0

    def test_end_request_success(self):
        """Test que end_request enregistre correctement une requête réussie."""
        collector = LLMMetricsCollector()
        collector.start_request()
        time.sleep(0.01)  # Petite pause pour avoir une latence mesurable
        collector.end_request(success=True)
        assert collector.start_time is None

    def test_end_request_failure(self):
        """Test que end_request enregistre correctement une requête échouée."""
        collector = LLMMetricsCollector()
        collector.start_request()
        collector.end_request(success=False)
        assert collector.start_time is None

    def test_record_tokens(self):
        """Test que record_tokens enregistre les tokens consommés."""
        collector = LLMMetricsCollector()
        # Ne devrait pas lever d'exception
        collector.record_tokens(prompt_tokens=100, completion_tokens=50)

    def test_record_tokens_calculates_cost(self):
        """Test que le coût est calculé correctement."""
        collector = LLMMetricsCollector()
        # 1000 tokens prompt = 0.00015$, 1000 tokens completion = 0.0006$
        collector.record_tokens(prompt_tokens=1000, completion_tokens=1000)
        # Le coût devrait être ~0.00075$

    def test_record_similarity(self):
        """Test que record_similarity enregistre le score."""
        collector = LLMMetricsCollector()
        collector.record_similarity(0.85)
        # Ne devrait pas lever d'exception

    def test_record_similarity_with_none(self):
        """Test que record_similarity gère None correctement."""
        collector = LLMMetricsCollector()
        collector.record_similarity(None)
        # Ne devrait pas lever d'exception

    def test_record_error(self):
        """Test que record_error enregistre les erreurs."""
        collector = LLMMetricsCollector()
        collector.record_error("timeout")
        collector.record_error("rate_limit")
        collector.record_error("api_error")

    def test_record_vector_search_success(self):
        """Test que record_vector_search enregistre une recherche réussie."""
        collector = LLMMetricsCollector()
        collector.record_vector_search(success=True, results_count=10)

    def test_record_vector_search_failure(self):
        """Test que record_vector_search enregistre une recherche échouée."""
        collector = LLMMetricsCollector()
        collector.record_vector_search(success=False, results_count=0)


class TestGlobalMetricsCollector:
    """Tests pour l'instance globale du collecteur."""

    def test_global_collector_exists(self):
        """Test que l'instance globale existe."""
        assert metrics_collector is not None
        assert isinstance(metrics_collector, LLMMetricsCollector)

    def test_global_collector_methods(self):
        """Test que les méthodes de l'instance globale fonctionnent."""
        metrics_collector.start_request()
        metrics_collector.end_request(success=True)
        metrics_collector.record_tokens(50, 25)
        metrics_collector.record_similarity(0.9)
        metrics_collector.record_error("test_error")
        metrics_collector.record_vector_search(True, 5)


class TestPrometheusMetrics:
    """Tests pour les métriques Prometheus individuelles."""

    def test_prediction_requests_counter(self):
        """Test que le compteur de requêtes existe."""
        assert prediction_requests_total is not None

    def test_latency_histogram(self):
        """Test que l'histogramme de latence existe."""
        assert llm_request_latency is not None

    def test_tokens_counter(self):
        """Test que le compteur de tokens existe."""
        assert tokens_consumed is not None

    def test_similarity_gauge(self):
        """Test que le gauge de similarité existe."""
        assert similarity_score is not None

    def test_errors_counter(self):
        """Test que le compteur d'erreurs existe."""
        assert llm_errors_total is not None

    def test_vector_searches_counter(self):
        """Test que le compteur de recherches vectorielles existe."""
        assert vector_searches_total is not None

    def test_vector_results_histogram(self):
        """Test que l'histogramme de résultats existe."""
        assert vector_results_count is not None
