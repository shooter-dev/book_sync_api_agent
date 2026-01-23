# Monitoring LLMOps - Book Sync API

Ce dossier contient la configuration pour le monitoring de l'API avec Prometheus et Grafana.

## Architecture LLMOps

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  FastAPI    │ ───► │  Prometheus │ ───► │   Grafana   │
│  /metrics   │      │  (collecte) │      │  (visualise)│
└─────────────┘      └─────────────┘      └─────────────┘
```

## Métriques LLMOps collectées

| Métrique | Type | Description |
|----------|------|-------------|
| `prediction_requests_total` | Counter | Nombre total de requêtes |
| `llm_request_latency_seconds` | Histogram | Latence des appels LLM |
| `llm_tokens_consumed_total` | Counter | Tokens consommés (prompt/completion) |
| `llm_estimated_cost_dollars` | Summary | Coût estimé des requêtes |
| `vector_similarity_score` | Gauge | Score de similarité moyen |
| `llm_errors_total` | Counter | Erreurs par type |
| `vector_searches_total` | Counter | Recherches vectorielles |

## Démarrage rapide

### 1. Lancer l'API (expose /metrics)

```bash
uvicorn app.main:app --port 3000
```

L'endpoint `/metrics` est automatiquement disponible.

### 2. Lancer Prometheus

```bash
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus
```

Accéder à: http://localhost:9090

### 3. Lancer Grafana

```bash
docker run -d \
  --name grafana \
  -p 3001:3000 \
  grafana/grafana
```

Accéder à: http://localhost:3001 (admin/admin)

### 4. Configurer Grafana

1. Ajouter Prometheus comme Data Source
   - URL: http://host.docker.internal:9090
2. Importer le dashboard: `grafana-dashboard.json`

## Requêtes PromQL utiles

```promql
# Taux de requêtes par minute
rate(prediction_requests_total[5m]) * 60

# Latence P95
histogram_quantile(0.95, llm_request_latency_seconds_bucket)

# Tokens par heure
increase(llm_tokens_consumed_total[1h])

# Taux d'erreur
rate(llm_errors_total[5m]) / rate(prediction_requests_total[5m])

# Coût total
llm_estimated_cost_dollars_sum
```

## Alertes recommandées

1. **Latence élevée**: P95 > 10 secondes
2. **Taux d'erreur**: > 5%
3. **Coût journalier**: > 10$
4. **Rate limit**: llm_errors_total{error_type="rate_limit"} > 0
