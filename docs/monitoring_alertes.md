# Monitoring et alertes en production

## 1. Mise en place
- Déploie Prometheus et Grafana sur l’environnement de production (Azure, VM, ou Kubernetes)
- Configure le scrape de l’API BookSync et l’import des dashboards

## 2. Configuration des alertes
- Utilise le fichier `alert_rules.yml` pour définir les alertes critiques
- Connecte Alertmanager pour recevoir des notifications (email, Slack, etc.)

## 3. Vérification
- Va sur l’interface Prometheus/Grafana
- Vérifie que les alertes sont actives et que les dashboards affichent les métriques

## 4. Preuves pour la certification
- Prends une capture d’écran des dashboards et des alertes actives
- Explique à quoi sert chaque alerte et comment tu es notifié

---

**Pour la certification, montre les dashboards et explique la gestion des incidents.**
