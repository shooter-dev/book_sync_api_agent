# Documentation : Tests de performance et de charge

Ce guide explique comment réaliser et intégrer des tests de performance et de charge pour BookSync API Agent dans le pipeline CI/CD.

---

## 1. Script de test de performance

Utiliser le script `scripts/perf_test.sh` pour lancer un test de charge sur l'API :

```bash
./scripts/perf_test.sh <URL_API> <API_KEY>
```

- `<URL_API>` : URL de l'API à tester (ex : http://localhost:8000)
- `<API_KEY>` : Clé API valide
- Le script utilise Apache Benchmark (ab) pour envoyer 500 requêtes concurrentes (20 simultanées) avec le payload `perf_payload.json`.
- Le rapport est généré dans `perf_report.txt`.

## 2. Intégration dans le pipeline CI/CD

- Ajouter l'exécution du script dans le workflow GitHub Actions avant le déploiement en production.
- Définir des seuils de performance (latence max, taux d'erreur) et faire échouer le pipeline si les seuils ne sont pas respectés.

## 3. Stratégie de tests

- Réaliser des tests de charge à chaque mise à jour majeure.
- Archiver les rapports pour analyse et amélioration continue.
- Adapter le payload et les paramètres selon les cas d'usage réels.

---

**Bonnes pratiques :**
- Utiliser des outils complémentaires (locust, k6) pour des scénarios avancés.
- Surveiller les métriques Prometheus pendant les tests pour détecter les goulets d'étranglement.

---

# Ce fichier est à supprimer (voir docs/_A_SUPPRIMER.txt)
