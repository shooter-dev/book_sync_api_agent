# Déploiement complet BookSync sur Azure (CI/CD, monitoring, rollback, sécurité)

Ce guide explique étape par étape comment :
- Déclencher un déploiement automatisé (CI/CD GitHub Actions)
- Mettre en place le monitoring Prometheus
- Gérer les alertes et la supervision
- Simuler un incident et effectuer un rollback
- Gérer la sécurité et la rotation des secrets
- Prendre des captures d'écran pour la certification

---

## 1. Déclencher un déploiement CI/CD (GitHub Actions)

### a. Pré-requis
- Le fichier `.github/workflows/deploy.yml` doit exister (voir exemple fourni)
- Le secret `AZURE_CREDENTIALS` doit être configuré dans GitHub (Settings > Secrets and variables > Actions)
- Le code source doit être prêt à être déployé

### b. Déclencher le pipeline
1. Pousse tes modifications sur la branche `main` :
   ```bash
   git add .
   git commit -m "feat: nouvelle fonctionnalité ou correctif"
   git push origin main
   ```
2. Va dans l’onglet **Actions** de GitHub
3. Vérifie que le workflow "Build and Deploy to Azure Container App" s’exécute
4. Attends la fin du pipeline (tests, build, push, déploiement)
5. Prends une capture d’écran de l’exécution réussie

---

## 2. Monitoring et alertes Prometheus

### a. Lancer Prometheus en local (pour test)
1. Vérifie que le fichier `prometheus.yml` et `alert_rules.yml` sont présents à la racine
2. Lance Prometheus avec Docker :
   ```bash
   docker run -p 9090:9090 -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml -v $(pwd)/alert_rules.yml:/etc/prometheus/alert_rules.yml prom/prometheus
   ```
3. Accède à http://localhost:9090
4. Va dans l’onglet **Alerts** pour voir les règles actives
5. Prends une capture d’écran des alertes

---

## 3. Simuler un incident et rollback

### a. Simuler une panne
1. Modifie le code pour que `/predict/health` retourne une erreur (ex : lève une exception ou retourne un status 500)
2. Commit et push sur `main` pour déclencher le pipeline (voir étape 1)
3. Vérifie que l’application déployée est en erreur (health check KO)
4. Prends une capture d’écran de l’erreur (portail Azure, logs, ou health check)

### b. Rollback
1. Dans GitHub, va dans l’onglet **Actions**
2. Sélectionne un workflow précédent (avant la panne)
3. Clique sur "Re-run job" ou redeploie un commit stable
4. Vérifie que le health check repasse OK
5. Prends une capture d’écran du retour à la normale

---

## 4. Sécurité et rotation des secrets

### a. Rotation des secrets
1. Va dans Azure Portal > ton registre de conteneurs > Accès clés
2. Clique sur "Régénérer" pour changer la clé d’accès
3. Mets à jour le secret `AZURE_CREDENTIALS` dans GitHub avec la nouvelle valeur
4. Prends une capture d’écran de la rotation

---

## 5. Schéma du pipeline et traçabilité

- Ajoute un schéma visuel du pipeline CI/CD dans la documentation (ex : draw.io, mermaid, ou capture d’écran du workflow GitHub)
- Explique la traçabilité : chaque étape du pipeline est loggée dans GitHub Actions, chaque image Docker est taguée par commit SHA
- Prends une capture d’écran du schéma et des logs

---

## 6. Tests de performance et de charge

- Ajoute un job de tests de charge (ex : locust, k6) dans le workflow GitHub Actions
- Documente les résultats dans un rapport ou capture d’écran

---

## 7. Monitoring en production

- Configure Prometheus/Grafana sur l’environnement de prod (voir documentation Azure)
- Mets en place des alertes critiques (voir `alert_rules.yml`)
- Prends une capture d’écran des dashboards et alertes

---

## 8. Conseils pour la certification
- Prépare un dossier avec toutes les captures d’écran (CI/CD, monitoring, rollback, rotation des secrets, schéma pipeline)
- Sois capable d’expliquer chaque étape (à quoi ça sert, comment on le déclenche, comment on vérifie)
- Utilise ce guide comme fil conducteur lors de l’oral

---

**Pour toute question, relis ce guide ou demande à ton équipe !**
