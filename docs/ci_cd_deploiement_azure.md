# Guide CI/CD BookSync API Agent sur Azure (GitHub Actions)

Ce guide explique **pas à pas** comment :
- Builder et tester l’image Docker localement
- Pousser une image sur Azure Container Registry (ACR)
- Déclencher et surveiller le pipeline GitHub Actions
- Comprendre chaque étape du workflow CI/CD
- Faire un rollback, gérer les secrets, valider le déploiement
- Prendre les captures d’écran attendues pour la certification

---

## 1. Prérequis et préparation

### A. Accès et outils nécessaires
- **Compte Azure** avec droits sur le groupe de ressources, l’ACR et le Container App
- **Accès au repo GitHub** (droits sur les secrets et les Actions)
- **Docker installé** sur ta machine locale (pour build/test en local)
- **Azure CLI** installé (`az`)
- **Git** installé

### B. Secrets GitHub à configurer
- Va dans GitHub > Settings > Secrets and variables > Actions
- Ajoute le secret `AZURE_CREDENTIALS` (JSON exporté depuis Azure, voir doc officielle Azure pour GitHub Actions)
- **Capture d’écran à prendre** : la page des secrets GitHub avec `AZURE_CREDENTIALS` présent

---

## 2. Build et test Docker en local (optionnel mais conseillé)

Avant de pousser quoi que ce soit, tu peux tester localement :

```bash
git clone <url-du-repo>
cd <repo>
docker build -t api-booksync:test .
docker run -p 3000:3000 api-booksync:test
```
- Va sur http://localhost:3000/docs pour vérifier que l’API démarre
- **Capture d’écran à prendre** : le terminal avec le build réussi et l’API qui tourne

Pour tester les endpoints :
```bash
curl http://localhost:3000/predict/health
```
- **Capture d’écran à prendre** : la réponse OK du health check

---

## 3. Pousser une image sur Azure Container Registry (ACR)

### A. Login à Azure et à l’ACR
```bash
az login
az acr login --name booksyncrepo
```

### B. Tag et push de l’image
```bash
# Tag l’image avec le nom de l’ACR
docker tag api-booksync:test booksyncrepo.azurecr.io/api-booksync:manualtest
# Push sur l’ACR
docker push booksyncrepo.azurecr.io/api-booksync:manualtest
```
- **Capture d’écran à prendre** : le push réussi dans le terminal
- Va sur Azure Portal > bookSyncRepo > Référentiels > api-booksync pour voir l’image
- **Capture d’écran à prendre** : l’image visible dans l’ACR

---

## 4. Déclencher le pipeline GitHub Actions (CI/CD)

### A. Déclenchement automatique
- **À chaque push sur la branche `main`**, le pipeline démarre tout seul
- Pour forcer un déclenchement :
```bash
git add .
git commit -m "test pipeline"
git push origin main
```
- **Capture d’écran à prendre** : le commit/push dans le terminal

### B. Déclenchement manuel
- Va sur GitHub > Actions > Choisis le workflow > "Run workflow" (si activé)
- **Capture d’écran à prendre** : le bouton Run workflow et le lancement

---

## 5. Comprendre chaque étape du workflow GitHub Actions

### A. Job 1 : Tests
- **Checkout** : récupère le code
- **Setup Python** : installe Python 3.12
- **Install dependencies** : installe les dépendances du projet
- **Run tests with coverage** : lance `pytest` et génère un rapport de couverture
- **Upload coverage report** : sauvegarde le rapport comme artefact
- **Capture d’écran à prendre** : le détail du job "test" sur GitHub Actions (succès ou échec)

### B. Job 2 : Build & Deploy
- **Azure CLI login** : se connecte à Azure avec le secret
- **Docker login to ACR** : login à l’ACR
- **Build and Push Docker image** : build l’image et la push sur l’ACR (tag = SHA du commit)
- **Deploy to Azure Container Apps** : met à jour le container app avec la nouvelle image
- **Capture d’écran à prendre** : le détail du job "build-and-deploy" sur GitHub Actions

---

## 6. Vérifier le déploiement sur Azure

- Va sur Azure Portal > Container Apps > api-booksync
- Vérifie l’onglet "Révisions" ou "Déploiements" : la nouvelle image (tag = SHA du commit) doit être active
- Va sur l’URL publique de l’API (ou via Azure Portal) et teste `/predict/health`
- **Capture d’écran à prendre** :
  - L’interface Azure avec la bonne image déployée
  - Le health check OK
  - Les logs du container (onglet Logs)

---

## 7. Rollback (en cas d’échec de déploiement)

- Va sur Azure Portal > bookSyncRepo > Référentiels > api-booksync
- Repère le tag de l’image précédente stable
- Va sur Azure Portal > Container Apps > api-booksync > Mettre à jour > choisis l’image précédente
- Ou en CLI :
```bash
az containerapp update --name api-booksync --resource-group vplatevoetRG --image booksyncrepo.azurecr.io/api-booksync:<TAG_PRECEDENT>
```
- Vérifie le health check
- **Capture d’écran à prendre** : rollback effectué, health check OK

---

## 8. Sécurité et rotation des secrets

- Pour changer les credentials Azure :
  - Va sur Azure Portal > bookSyncRepo > Accès clés > régénère la clé
  - Mets à jour le secret `AZURE_CREDENTIALS` dans GitHub
  - Relance un déploiement pour valider
- **Capture d’écran à prendre** : la page de rotation de clé sur Azure, la mise à jour du secret sur GitHub

---

## 9. Conseils pour la certification et l’oral

- **Explique chaque étape** : build local, push, pipeline, déploiement, rollback, sécurité
- **Sois prêt à montrer chaque capture d’écran**
- **Sois capable de justifier chaque action** (ex : pourquoi on fait un health check, pourquoi on rollback, pourquoi on sécurise les secrets)
- **Montre le suivi dans GitHub Actions** (historique des runs, logs, artefacts)
- **Montre le suivi dans Azure** (images, déploiements, logs, health)

---

## 10. Checklist des captures d’écran à fournir
- Secrets GitHub configurés
- Build Docker local réussi
- API locale qui tourne + health check OK
- Push image sur ACR réussi
- Image visible dans Azure ACR
- Commit/push déclenchant le pipeline
- Lancement manuel du workflow (si utilisé)
- Jobs "test" et "build-and-deploy" sur GitHub Actions (succès/échec)
- Déploiement visible sur Azure (bonne image)
- Health check OK sur l’API déployée
- Logs du container sur Azure
- Rollback effectué et validé
- Rotation de secrets (Azure + GitHub)

---

# Déploiement Azure CI/CD : Création du secret AZURE_CREDENTIALS

## Générer les identifiants Azure pour GitHub Actions

Pour permettre à GitHub Actions de déployer automatiquement sur Azure, il faut fournir un secret appelé `AZURE_CREDENTIALS` contenant les informations d'un Service Principal Azure. Ce Service Principal agit comme un "compte technique" sécurisé pour les opérations automatisées.

### 1. Ligne de commande à exécuter

```sh
az ad sp create-for-rbac --name "<api-booksync>" --sdk-auth
```

### 2. Explication détaillée

- **az ad sp create-for-rbac** :
  - Cette commande Azure CLI crée un Service Principal (SP), c'est-à-dire une identité d'application qui pourra être utilisée pour s'authentifier auprès d'Azure et effectuer des actions (déploiement, gestion de ressources, etc.).
  - L'option `--name "<api-booksync>"` permet de donner un nom explicite à ce Service Principal (remplace `<api-booksync>` par le nom de ton application ou projet si besoin).
  - L'option `--sdk-auth` génère un bloc JSON formaté spécialement pour être utilisé dans les outils d'automatisation comme GitHub Actions.

- **Ce que fait la commande :**
  1. Crée un Service Principal dans Azure Active Directory avec les droits nécessaires pour gérer les ressources de l'abonnement courant.
  2. Génère un secret (mot de passe) associé à ce Service Principal.
  3. Retourne un JSON contenant toutes les informations d'identification nécessaires (clientId, clientSecret, subscriptionId, tenantId, etc.).

- **Ce JSON doit être copié tel quel dans GitHub, dans la section "Secrets" du dépôt, sous le nom `AZURE_CREDENTIALS`**.

### 3. Utilisation dans GitHub Actions

Dans le workflow GitHub Actions, ce secret sera utilisé pour se connecter à Azure automatiquement, par exemple avec l'action officielle :

```yaml
- name: Azure Login
  uses: azure/login@v1
  with:
    creds: ${{ secrets.AZURE_CREDENTIALS }}
```

### 4. Sécurité
- Ne partage jamais ce JSON en clair.
- Si tu régénères le secret, pense à le mettre à jour dans GitHub et à supprimer l'ancien si besoin.

---

**Résumé :**
Cette commande est la première étape indispensable pour automatiser les déploiements Azure via CI/CD. Elle crée un compte technique sécurisé et te fournit les identifiants à transmettre à GitHub Actions pour permettre l'accès automatisé à ton cloud Azure.

---

## 11. Simuler une panne sur l'API et tester le rollback CI/CD

### Objectif
Simuler une panne sur l'API (endpoint `/predict/health`) pour vérifier que le pipeline CI/CD détecte l'erreur, puis restaurer le service (rollback) et valider le retour à la normale.

### Étapes détaillées et explications

#### 1. Modifier la route `/predict/health` pour simuler une panne
- Ouvre le fichier : `app/routes/predict_routes.py`
- Repère la fonction suivante (ou ajoute-la si elle n'existe pas) :

```python
@router.get("/health")
async def health_check():
    """
    Endpoint de surveillance de l'état de santé du service de prédiction.
    (Version modifiée pour simuler une erreur)
    """
    # Simulation d'une panne pour test du rollback
    raise HTTPException(status_code=500, detail="Erreur simulée pour test rollback")
```

- **Explication** :
    - Cette modification force l'API à retourner une erreur 500 sur `/predict/health`.
    - Cela simule une panne détectable par le pipeline CI/CD ou le monitoring Azure.

#### 2. Commit et push la modification
- Dans ton terminal :
```bash
git add app/routes/predict_routes.py
git commit -m "test: simulate failure on /predict/health for CI/CD rollback demo"
git push origin main
```
- **Explication** :
    - Le pipeline GitHub Actions va se déclencher automatiquement.
    - Les tests ou le déploiement devraient échouer (ou le monitoring doit signaler l'erreur).

#### 3. Vérifier l'échec dans GitHub Actions et/ou Azure
- Va sur GitHub > Actions > workflow en cours.
- Vérifie que le job échoue (ou que le health check échoue sur Azure).
- Prends une capture d'écran de l'échec (pour la doc ou la soutenance).

#### 4. Rollback : restaurer le code d'origine
- Remets la fonction `/predict/health` dans son état initial :

```python
@router.get("/health")
async def health_check():
    """
    Endpoint de surveillance de l'état de santé du service de prédiction.
    """
    return {"status": "healthy", "service": "predict"}
```

- Commit et push à nouveau :
```bash
git add app/routes/predict_routes.py
git commit -m "fix: restore healthy health_check endpoint after failure simulation"
git push origin main
```
- **Explication** :
    - Le pipeline va se relancer.
    - L'API doit repasser au vert (health check OK).
    - Prends une capture d'écran du retour à la normale.

#### 5. Résumer à l'oral ou dans la doc
- Pourquoi faire ça ?
    - Pour prouver que le pipeline CI/CD détecte bien les pannes.
    - Pour montrer que tu sais rollback rapidement en cas d'incident.
    - Pour valider la robustesse de la chaîne de déploiement.
- Ce process est reproductible à tout moment pour démontrer la maîtrise du CI/CD et du monitoring.

---
