# Documentation complète : Lancer et valider la surveillance Prometheus & Alertmanager

Ce guide explique étape par étape comment démarrer, configurer, vérifier et documenter la surveillance et la gestion des alertes pour BookSync API Agent en production.

---

# Alertes Prometheus pour BookSync

## 1. Lancement de Prometheus

- Place `prometheus.yml` et `alert_rules.yml` à la racine du projet.
- Lance Prometheus avec Docker :
  ```bash
  docker run -p 9090:9090 -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml -v $(pwd)/alert_rules.yml:/etc/prometheus/alert_rules.yml prom/prometheus
  ```
- Accède à http://localhost:9090

## 2. Visualisation des alertes

- Va dans l’onglet **Alerts** pour voir les règles actives.
- Les alertes "HighLLMLatency", "PredictionErrors", "VectorSearchFailures" sont prêtes à détecter les incidents sur l’API.

## 3. Prendre des captures d’écran

- Prends une capture de l’onglet Alerts avec les règles actives.
- Prends une capture de l’onglet Status > Alertmanager discovery.

## 4. Explications

- Les alertes sont déclenchées si la latence LLM est trop élevée, s’il y a trop d’erreurs de prédiction ou d’échecs de recherche vectorielle.
- Ces alertes permettent d’être notifié rapidement en cas d’incident critique sur l’API.

---

**Pour la certification, montre les captures d’écran et explique à quoi servent chaque alerte.**
