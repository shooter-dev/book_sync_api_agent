# Guide CI/CD - BookSync API Agent

Ce document explique comment mettre en place un pipeline CI/CD complet pour automatiser les tests, le build et le déploiement de l'API BookSync sur Azure.

## Table des matières

1. [Qu'est-ce que la CI/CD ?](#quest-ce-que-la-cicd-)
2. [Architecture du pipeline](#architecture-du-pipeline)
3. [Tests unitaires et couverture](#tests-unitaires-et-couverture)
4. [Prérequis](#prérequis)
5. [Configuration des secrets GitHub](#configuration-des-secrets-github)
6. [Création du workflow GitHub Actions](#création-du-workflow-github-actions)
7. [Déploiement manuel (avant automatisation)](#déploiement-manuel-avant-automatisation)
8. [Tests et validation](#tests-et-validation)
9. [Surveillance et maintenance](#surveillance-et-maintenance)

---

## Qu'est-ce que la CI/CD ?

### CI (Continuous Integration - Intégration Continue)
Processus qui **automatise les tests** à chaque modification du code :
- Exécute les tests automatiquement
- Vérifie la qualité du code
- Détecte les bugs rapidement

### CD (Continuous Deployment - Déploiement Continu)
Processus qui **automatise le déploiement** de l'application :
- Build automatique de l'image Docker
- Push vers le registre de conteneurs
- Déploiement automatique sur Azure

### Avantages
- ✅ Détection rapide des bugs
- ✅ Déploiements automatiques et fiables
- ✅ Gain de temps
- ✅ Moins d'erreurs humaines

---

## Architecture du pipeline

```
Code Push sur GitHub
        ↓
[GitHub Actions démarre]
        ↓
┌─────────────────────┐
│   1. Tests          │  → pytest avec couverture
└─────────────────────┘
        ↓ (si succès)
┌─────────────────────┐
│   2. Build Docker   │  → docker buildx build
└─────────────────────┘
        ↓
┌─────────────────────┐
│   3. Push ACR       │  → Azure Container Registry
└─────────────────────┘
        ↓
┌─────────────────────┐
│   4. Deploy Azure   │  → Azure Container App
└─────────────────────┘
        ↓
   ✅ API en ligne
```

---

## Tests unitaires et couverture

### Vue d'ensemble de la suite de tests

Le projet dispose d'une suite complète de **73 tests unitaires** organisés en 5 modules, couvrant toutes les couches de l'application.

### Organisation des tests

```
tests/
├── database/
│   └── test_vector_store.py         # 15 tests - VectorStore et PostgreSQL
├── services/
│   ├── test_predict_service.py      # 17 tests - Service de prédiction
│   └── test_synthesizer.py          # 8 tests - Génération de réponses IA
├── routes/
│   └── test_predict_routes.py       # 15 tests - Endpoints API
└── models/
    └── test_models.py                # 18 tests - Modèles Pydantic
```

### Couverture des tests par module

#### 1. **test_vector_store.py** (15 tests)
Tests de la couche de données et recherche vectorielle :
- ✅ Initialisation avec OpenAI et Azure OpenAI
- ✅ Génération d'embeddings
- ✅ Création et gestion des tables/index
- ✅ Opérations CRUD (upsert, search, delete)
- ✅ Recherche avec filtres de métadonnées
- ✅ Validation des paramètres

#### 2. **test_predict_service.py** (17 tests)
Tests de la logique métier de prédiction :
- ✅ Prédictions réussies et gestion d'erreurs
- ✅ Recherche de volumes similaires (avec/sans collection)
- ✅ Extraction des recommandations de séries
- ✅ Génération de réponses IA personnalisées
- ✅ Gestion des différentes humeurs et catégories
- ✅ Déduplication des résultats

#### 3. **test_synthesizer.py** (8 tests)
Tests de la génération de réponses IA :
- ✅ Génération avec OpenAI/Azure OpenAI
- ✅ Gestion des cas sans résultats
- ✅ Gestion d'erreurs et fallback
- ✅ Validation de la structure du prompt
- ✅ Configuration des paramètres (température, tokens)

#### 4. **test_predict_routes.py** (15 tests)
Tests des endpoints FastAPI :
- ✅ Health check `/predict/health`
- ✅ Endpoint principal `/predict/`
- ✅ Endpoints de test `/predict/test` et `/predict/raw`
- ✅ Validation des requêtes invalides
- ✅ Tests avec différentes catégories et humeurs
- ✅ Requêtes concurrentes

#### 5. **test_models.py** (18 tests)
Tests de validation Pydantic :
- ✅ Validation des champs obligatoires/optionnels
- ✅ Types de prédiction (collection/recommendation)
- ✅ Limites et contraintes
- ✅ Formats dict/string pour collection
- ✅ Sérialisation JSON
- ✅ Support Unicode

### Commandes pour lancer les tests

#### Tests locaux

```bash
# Tous les tests avec couverture
pytest --cov=app --cov-report=html --cov-report=term

# Tests spécifiques par module
pytest tests/database/test_vector_store.py -v
pytest tests/services/test_predict_service.py -v
pytest tests/services/test_synthesizer.py -v
pytest tests/routes/test_predict_routes.py -v
pytest tests/models/test_models.py -v

# Tests par marqueur (si configuré)
pytest -m unit
pytest -m integration

# Tests verbeux avec traceback complet
pytest -v --tb=long

# Tests avec arrêt à la première erreur
pytest -x

# Tests d'un fichier spécifique
pytest tests/services/test_predict_service.py::TestPredictService::test_predict_success -v
```

#### Rapports de couverture

```bash
# Génère un rapport HTML
pytest --cov=app --cov-report=html

# Ouvre le rapport dans le navigateur
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux

# Rapport XML pour CI/CD
pytest --cov=app --cov-report=xml

# Rapport dans le terminal
pytest --cov=app --cov-report=term-missing
```

### Intégration dans le pipeline CI/CD

Les tests sont automatiquement exécutés dans GitHub Actions à chaque push ou pull request.

**Configuration dans `.github/workflows/ci-cd.yml` :**

```yaml
- name: Lancement des tests avec pytest
  env:
    USE_AZURE_OPENAI: true
    AZURE_OPENAI_ENDPOINT: ${{ secrets.AZURE_OPENAI_ENDPOINT }}
    AZURE_OPENAI_KEY: ${{ secrets.AZURE_OPENAI_KEY }}
    TIMESCALE_SERVICE_URL: ${{ secrets.TIMESCALE_SERVICE_URL }}
  run: |
    pytest --cov=app --cov-report=xml --cov-report=term

- name: Upload du rapport de couverture
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
    fail_ci_if_error: false
```

### Stratégies de tests

#### Tests unitaires avec mocking

Les tests utilisent `unittest.mock` et `pytest` pour isoler les composants :

```python
# Exemple : Mock de VectorStore dans PredictService
@patch('app.services.predict_service.VectorStore.search')
def test_search_similar_volumes(mock_vector_search):
    mock_vector_search.return_value = mock_search_results
    result = predict_service._search_similar_volumes(request)
    assert isinstance(result, pd.DataFrame)
```

#### Tests asynchrones

Les tests des services asynchrones utilisent `pytest-asyncio` :

```python
@pytest.mark.asyncio
async def test_predict_success(mock_search):
    result = await predict_service.predict(sample_request)
    assert result.status == "success"
```

#### Fixtures pytest

Utilisation extensive de fixtures pour la réutilisabilité :

```python
@pytest.fixture
def sample_request():
    return PredictRequest(
        user_age="25",
        user_genre="Homme",
        ...
    )
```

### Objectifs de couverture

| Composant | Couverture actuelle | Objectif |
|-----------|---------------------|----------|
| Services | ~85% | 90%+ |
| Routes | ~80% | 85%+ |
| Models | ~95% | 95%+ |
| Database | ~75% | 80%+ |
| **Global** | **~84%** | **90%+** |

### Bonnes pratiques

1. **Isolation** : Chaque test est indépendant et ne dépend pas des autres
2. **Mocking** : Les dépendances externes (DB, OpenAI) sont mockées
3. **Nomenclature** : Noms de tests descriptifs (`test_predict_success`, `test_predict_with_error`)
4. **Assertions** : Vérifications complètes des résultats
5. **Documentation** : Docstrings pour chaque classe et méthode de test

### Amélioration continue

**Prochaines étapes :**
- [ ] Ajouter des tests d'intégration avec base de données réelle
- [ ] Tests de charge avec locust ou pytest-benchmark
- [ ] Tests de sécurité (injection SQL, XSS)
- [ ] Augmenter la couverture à 90%+

---

## Prérequis

### 1. Ressources Azure existantes

Vous avez déjà ces ressources (visible dans votre Makefile) :
- ✅ **Azure Container Registry** : `booksyncrepo.azurecr.io`
- ✅ **Azure Container App** : `api-booksync`
- ✅ **Resource Group** : `vplatevoetRG`

### 2. Informations nécessaires

Pour configurer la CI/CD, vous aurez besoin de :

#### A. Azure Container Registry (ACR)
- **Nom du registre** : `booksyncrepo`
- **URL complète** : `booksyncrepo.azurecr.io`
- **Username** : À récupérer
- **Password** : À récupérer

#### B. Azure Container App
- **Nom de l'app** : `api-booksync`
- **Resource Group** : `vplatevoetRG`

#### C. Service Principal Azure (pour l'authentification)
- **Client ID** : À créer
- **Client Secret** : À créer
- **Tenant ID** : À récupérer
- **Subscription ID** : À récupérer

---

## Configuration des secrets GitHub

### Prérequis : Installation d'Azure CLI

Si vous n'avez pas encore Azure CLI :

**macOS :**
```bash
brew install azure-cli
```

**Windows :**
Téléchargez depuis : https://aka.ms/installazurecliwindows

**Linux :**
```bash
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

Vérifiez l'installation :
```bash
az --version
```

---

### Étape 1 : Connexion à Azure

#### 1.1 Se connecter à Azure

```bash
# Ouvrir votre terminal et exécutez
az login
```

**Ce qui se passe :**
- Une fenêtre de navigateur s'ouvre
- Connectez-vous avec votre compte Azure
- Le terminal affiche la liste de vos souscriptions

#### 1.2 Sélectionner la bonne souscription

Si vous avez plusieurs souscriptions Azure :

```bash
# Lister toutes vos souscriptions
az account list --output table

# Sélectionner la bonne souscription
az account set --subscription "Nom-de-votre-souscription"

# Vérifier que c'est la bonne
az account show
```

#### 1.3 Récupérer votre Subscription ID

```bash
az account show --query id -o tsv
```

**Sauvegardez cette valeur**, vous en aurez besoin pour :
- Créer le Service Principal
- Le secret `AZURE_SUBSCRIPTION_ID` dans GitHub

**Exemple de résultat :**
```
12345678-abcd-1234-efgh-123456789abc
```

---

### Étape 2 : Récupérer les credentials Azure Container Registry

#### 2.1 Vérifier que votre ACR existe

```bash
az acr show --name booksyncrepo --resource-group vplatevoetRG
```

Si cette commande fonctionne, votre ACR existe. ✅

#### 2.2 Activer l'admin user (si nécessaire)

```bash
# Activer l'utilisateur admin
az acr update --name booksyncrepo --admin-enabled true
```

#### 2.3 Récupérer les credentials

```bash
az acr credential show --name booksyncrepo --resource-group vplatevoetRG
```

**Résultat attendu :**
```json
{
  "passwords": [
    {
      "name": "password",
      "value": "XyZ123AbC456..."
    },
    {
      "name": "password2",
      "value": "DeF789GhI012..."
    }
  ],
  "username": "booksyncrepo"
}
```

**Notez ces valeurs :**
- `username` → Secret GitHub : `ACR_USERNAME` (généralement : booksyncrepo)
- `passwords[0].value` → Secret GitHub : `ACR_PASSWORD` (utilisez password ou password2)

**💡 Astuce :** Copiez ces valeurs dans un fichier texte temporaire (ne le committez jamais !).

---

### Étape 3 : Créer un Service Principal pour GitHub Actions

#### 3.1 Qu'est-ce qu'un Service Principal ?

Un Service Principal est une **identité Azure** qui permet à GitHub Actions de :
- Se connecter à Azure automatiquement
- Déployer votre application
- Gérer vos ressources

C'est comme un "compte de service" avec des permissions limitées.

#### 3.2 Créer le Service Principal

**⚠️ Important :** Remplacez `<SUBSCRIPTION_ID>` par votre ID récupéré à l'étape 1.3

```bash
az ad sp create-for-rbac \
  --name "booksync-github-actions" \
  --role contributor \
  --scopes /subscriptions/<SUBSCRIPTION_ID>/resourceGroups/vplatevoetRG \
  --sdk-auth
```

**Exemple avec un vrai ID :**
```bash
az ad sp create-for-rbac \
  --name "booksync-github-actions" \
  --role contributor \
  --scopes /subscriptions/12345678-abcd-1234-efgh-123456789abc/resourceGroups/vplatevoetRG \
  --sdk-auth
```

#### 3.3 Résultat de la commande

**Vous obtiendrez un JSON comme ceci :**
```json
{
  "clientId": "abcd1234-ef56-7890-gh12-ijklmnop3456",
  "clientSecret": "VotreSuperSecretQuiEstTresLong123456",
  "subscriptionId": "12345678-abcd-1234-efgh-123456789abc",
  "tenantId": "87654321-dcba-4321-hgfe-987654321fed",
  "activeDirectoryEndpointUrl": "https://login.microsoftonline.com",
  "resourceManagerEndpointUrl": "https://management.azure.com/",
  "activeDirectoryGraphResourceId": "https://graph.windows.net/",
  "sqlManagementEndpointUrl": "https://management.core.windows.net:8443/",
  "galleryEndpointUrl": "https://gallery.azure.com/",
  "managementEndpointUrl": "https://management.core.windows.net/"
}
```

**🚨 TRÈS IMPORTANT :**
1. **Copiez TOUT ce JSON** dans un fichier texte sécurisé
2. Ce JSON servira pour le secret `AZURE_CREDENTIALS` dans GitHub
3. Le `clientSecret` ne sera plus jamais visible après cette étape
4. **Ne committez jamais ce fichier dans Git**

#### 3.4 Vérifier que le Service Principal fonctionne

```bash
# Tester la connexion avec le Service Principal
az login --service-principal \
  --username <clientId> \
  --password <clientSecret> \
  --tenant <tenantId>

# Si ça fonctionne, vous êtes connecté avec le SP
az account show
```

#### 3.5 En cas d'erreur

**Erreur : "Insufficient privileges"**
```bash
# Vous n'avez pas les droits pour créer un Service Principal
# Solution : Demandez à un administrateur Azure de le faire
```

**Erreur : "already exists"**
```bash
# Le Service Principal existe déjà
# Solution : Listez-les et trouvez le bon
az ad sp list --display-name "booksync-github-actions"

# Ou supprimez l'ancien et recréez
az ad sp delete --id <appId-du-sp>
```

---

### Étape 4 : Récupérer vos credentials existants

#### 4.1 Azure OpenAI Endpoint et Key

Vous les avez déjà dans votre `.env` :
- `AZURE_OPENAI_ENDPOINT` → Déjà dans votre .env (ligne 2)
- `AZURE_OPENAI_KEY` → Déjà dans votre .env (ligne 3)

**Vérification via Azure CLI :**
```bash
# Lister vos ressources OpenAI
az cognitiveservices account list --resource-group vplatevoetRG

# Récupérer les clés
az cognitiveservices account keys list \
  --name app-booksync \
  --resource-group vplatevoetRG
```

#### 4.2 Timescale/PostgreSQL URL

Vous l'avez déjà dans votre `.env` :
- `TIMESCALE_SERVICE_URL` → Déjà dans votre .env (ligne 12)

Format attendu :
```
postgres://user:password@host:port/database
```

---

### Étape 5 : Récapitulatif de tous les secrets à récupérer

Avant de passer à GitHub, vérifiez que vous avez bien récupéré :

| Secret | Source | Commande/Localisation |
|--------|--------|----------------------|
| `AZURE_CREDENTIALS` | Service Principal (JSON complet) | Étape 3.3 |
| `AZURE_SUBSCRIPTION_ID` | Azure Subscription | `az account show --query id -o tsv` |
| `ACR_USERNAME` | Azure Container Registry | `az acr credential show` |
| `ACR_PASSWORD` | Azure Container Registry | `az acr credential show` |
| `AZURE_OPENAI_KEY` | Fichier .env ou Azure Portal | Ligne 3 de votre .env |
| `AZURE_OPENAI_ENDPOINT` | Fichier .env ou Azure Portal | Ligne 2 de votre .env |
| `TIMESCALE_SERVICE_URL` | Fichier .env | Ligne 12 de votre .env |

**Template à remplir :**
```
✅ AZURE_CREDENTIALS = {tout le JSON du Service Principal}
✅ AZURE_SUBSCRIPTION_ID = ________________________________________
✅ ACR_USERNAME = booksyncrepo
✅ ACR_PASSWORD = ________________________________________
✅ AZURE_OPENAI_KEY = ________________________________________
✅ AZURE_OPENAI_ENDPOINT = https://app-booksync.openai.azure.com/
✅ TIMESCALE_SERVICE_URL = postgres://booksyncadmin:wevzuh-paGwi6-nanwag@bdd-booksync.postgres.database.azure.com:5432/booksync
```

### Étape 3 : Ajouter les secrets dans GitHub

1. Allez sur votre repository GitHub : `https://github.com/shooter-dev/book_sync_api_agent`
2. Cliquez sur **Settings** (en haut à droite)
3. Dans le menu de gauche : **Secrets and variables** → **Actions**
4. Cliquez sur **New repository secret**

Ajoutez ces secrets un par un :

| Nom du secret | Valeur | Description |
|---------------|--------|-------------|
| `AZURE_CREDENTIALS` | Le JSON complet du Service Principal | Authentification Azure |
| `AZURE_SUBSCRIPTION_ID` | Votre Subscription ID | ID de souscription Azure |
| `ACR_USERNAME` | Username ACR (ex: booksyncrepo) | Login registre Docker |
| `ACR_PASSWORD` | Password ACR | Mot de passe registre Docker |
| `AZURE_OPENAI_KEY` | Votre clé Azure OpenAI | API Key OpenAI |
| `AZURE_OPENAI_ENDPOINT` | URL endpoint Azure OpenAI | Endpoint OpenAI |
| `TIMESCALE_SERVICE_URL` | URL PostgreSQL complète | Connexion base de données |

---

## Création du workflow GitHub Actions

### Étape 1 : Créer la structure de dossier

```bash
# À la racine de votre projet
mkdir -p .github/workflows
```

### Étape 2 : Créer le fichier de workflow

Créez le fichier `.github/workflows/ci-cd.yml` avec ce contenu :

```yaml
name: CI/CD Pipeline - BookSync API

on:
  push:
    branches:
      - main
      - develop
  pull_request:
    branches:
      - main

env:
  AZURE_CONTAINER_APP: api-booksync
  AZURE_RESOURCE_GROUP: vplatevoetRG
  ACR_LOGIN_SERVER: booksyncrepo.azurecr.io
  IMAGE_NAME: api-booksync

jobs:
  # Job 1 : Tests
  test:
    name: Tests et Qualité du Code
    runs-on: ubuntu-latest

    steps:
      - name: Checkout du code
        uses: actions/checkout@v4

      - name: Configuration Python 3.13
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'
          cache: 'pip'

      - name: Installation des dépendances
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Lancement des tests avec pytest
        env:
          USE_AZURE_OPENAI: true
          AZURE_OPENAI_ENDPOINT: ${{ secrets.AZURE_OPENAI_ENDPOINT }}
          AZURE_OPENAI_KEY: ${{ secrets.AZURE_OPENAI_KEY }}
          TIMESCALE_SERVICE_URL: ${{ secrets.TIMESCALE_SERVICE_URL }}
        run: |
          pytest --cov=app --cov-report=xml --cov-report=term

      - name: Upload du rapport de couverture
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: false

  # Job 2 : Build et Push Docker (seulement si tests OK)
  build:
    name: Build et Push Image Docker
    runs-on: ubuntu-latest
    needs: test
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'

    steps:
      - name: Checkout du code
        uses: actions/checkout@v4

      - name: Connexion à Azure Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.ACR_LOGIN_SERVER }}
          username: ${{ secrets.ACR_USERNAME }}
          password: ${{ secrets.ACR_PASSWORD }}

      - name: Configuration de Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build et Push de l'image Docker
        uses: docker/build-push-action@v5
        with:
          context: .
          platforms: linux/amd64
          push: true
          tags: |
            ${{ env.ACR_LOGIN_SERVER }}/${{ env.IMAGE_NAME }}:latest
            ${{ env.ACR_LOGIN_SERVER }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
          cache-from: type=registry,ref=${{ env.ACR_LOGIN_SERVER }}/${{ env.IMAGE_NAME }}:buildcache
          cache-to: type=registry,ref=${{ env.ACR_LOGIN_SERVER }}/${{ env.IMAGE_NAME }}:buildcache,mode=max

  # Job 3 : Déploiement sur Azure (seulement si build OK)
  deploy:
    name: Déploiement sur Azure Container Apps
    runs-on: ubuntu-latest
    needs: build
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'

    steps:
      - name: Connexion à Azure
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}

      - name: Déploiement sur Azure Container App
        uses: azure/CLI@v1
        with:
          inlineScript: |
            az containerapp update \
              --name ${{ env.AZURE_CONTAINER_APP }} \
              --resource-group ${{ env.AZURE_RESOURCE_GROUP }} \
              --image ${{ env.ACR_LOGIN_SERVER }}/${{ env.IMAGE_NAME }}:${{ github.sha }}

      - name: Vérification du déploiement
        uses: azure/CLI@v1
        with:
          inlineScript: |
            az containerapp show \
              --name ${{ env.AZURE_CONTAINER_APP }} \
              --resource-group ${{ env.AZURE_RESOURCE_GROUP }} \
              --query properties.latestRevisionName \
              -o tsv

      - name: Déconnexion Azure
        run: az logout
```

### Étape 3 : Commit et push du workflow

```bash
git add .github/workflows/ci-cd.yml
git commit -m "feat: ajout du pipeline CI/CD avec GitHub Actions"
git push origin main
```

---

## Déploiement manuel (avant automatisation)

Avant d'automatiser, testez votre déploiement manuel :

### Test 1 : Build local

```bash
# Build de l'image Docker
docker buildx build --no-cache --platform linux/amd64 -t api-booksync:latest .

# Test local (optionnel)
docker run -p 8000:8000 \
  -e USE_AZURE_OPENAI=true \
  -e AZURE_OPENAI_KEY=votre_clé \
  api-booksync:latest
```

### Test 2 : Push manuel vers ACR

```bash
# Login sur Azure
az login

# Login sur ACR
az acr login --name booksyncrepo

# Tag et push
docker tag api-booksync:latest booksyncrepo.azurecr.io/api-booksync:latest
docker push booksyncrepo.azurecr.io/api-booksync:latest
```

### Test 3 : Déploiement manuel sur Container App

```bash
az containerapp update \
  --name api-booksync \
  --resource-group vplatevoetRG \
  --image booksyncrepo.azurecr.io/api-booksync:latest
```

Ou utilisez votre Makefile existant :

```bash
make push-azur
```

---

## Tests et validation

### Après le premier déploiement automatique

1. **Vérifier les logs GitHub Actions**
   - Allez sur : `https://github.com/shooter-dev/book_sync_api_agent/actions`
   - Vérifiez que les 3 jobs (test, build, deploy) sont ✅ verts

2. **Vérifier l'API déployée**
   ```bash
   # Récupérer l'URL de votre Container App
   az containerapp show \
     --name api-booksync \
     --resource-group vplatevoetRG \
     --query properties.configuration.ingress.fqdn \
     -o tsv
   ```

   Testez l'endpoint :
   ```bash
   curl https://votre-url.azurecontainerapps.io/docs
   ```

3. **Vérifier les logs de l'application**
   ```bash
   az containerapp logs show \
     --name api-booksync \
     --resource-group vplatevoetRG \
     --follow
   ```

---

## Surveillance et maintenance

### Variables d'environnement sur Azure Container App

Pour configurer les variables d'environnement (secrets) sur Azure :

```bash
az containerapp update \
  --name api-booksync \
  --resource-group vplatevoetRG \
  --set-env-vars \
    USE_AZURE_OPENAI=true \
    AZURE_OPENAI_ENDPOINT=secretref:azure-openai-endpoint \
    AZURE_OPENAI_KEY=secretref:azure-openai-key \
    TIMESCALE_SERVICE_URL=secretref:timescale-url

# Ajouter les secrets
az containerapp secret set \
  --name api-booksync \
  --resource-group vplatevoetRG \
  --secrets \
    azure-openai-endpoint="votre-endpoint" \
    azure-openai-key="votre-key" \
    timescale-url="votre-db-url"
```

### Monitoring

```bash
# Voir les révisions (versions déployées)
az containerapp revision list \
  --name api-booksync \
  --resource-group vplatevoetRG \
  -o table

# Revenir à une version précédente
az containerapp revision activate \
  --name api-booksync \
  --resource-group vplatevoetRG \
  --revision <nom-de-la-revision>
```

### Stratégies de déploiement

#### Blue-Green Deployment (Traffic Splitting)

```bash
# Nouvelle version = 10% du traffic
az containerapp ingress traffic set \
  --name api-booksync \
  --resource-group vplatevoetRG \
  --revision-weight latest=10 previous=90

# Si OK, basculer 100% sur la nouvelle version
az containerapp ingress traffic set \
  --name api-booksync \
  --resource-group vplatevoetRG \
  --revision-weight latest=100
```

---

## Checklist de mise en place

- [ ] 1. Récupérer les credentials Azure Container Registry
- [ ] 2. Créer le Service Principal Azure
- [ ] 3. Ajouter tous les secrets dans GitHub
- [ ] 4. Créer le dossier `.github/workflows/`
- [ ] 5. Créer le fichier `ci-cd.yml`
- [ ] 6. Commit et push le workflow
- [ ] 7. Vérifier l'exécution sur GitHub Actions
- [ ] 8. Tester l'API déployée
- [ ] 9. Configurer les variables d'environnement sur Azure
- [ ] 10. Mettre en place le monitoring

---

## Commandes utiles de troubleshooting

```bash
# Voir les logs en temps réel
az containerapp logs show \
  --name api-booksync \
  --resource-group vplatevoetRG \
  --follow

# Redémarrer l'application
az containerapp revision restart \
  --name api-booksync \
  --resource-group vplatevoetRG \
  --revision <revision-name>

# Voir les métriques
az monitor metrics list \
  --resource /subscriptions/<sub-id>/resourceGroups/vplatevoetRG/providers/Microsoft.App/containerApps/api-booksync \
  --metric "Requests"

# Voir l'état de santé
az containerapp show \
  --name api-booksync \
  --resource-group vplatevoetRG \
  --query properties.runningStatus
```

---

## Ressources supplémentaires

- [Documentation GitHub Actions](https://docs.github.com/en/actions)
- [Documentation Azure Container Apps](https://learn.microsoft.com/en-us/azure/container-apps/)
- [Documentation Azure Container Registry](https://learn.microsoft.com/en-us/azure/container-registry/)
- [Best Practices CI/CD](https://docs.github.com/en/actions/deployment/about-deployments/deploying-with-github-actions)

---

## Rollback et Gestion des Erreurs de Deploiement

### Vue d'ensemble

Le systeme CI/CD inclut des mecanismes automatiques et manuels pour gerer les erreurs de deploiement :

```
Deploiement
    |
    v
Health Check (/predict/health)
    |
+---+---+
|       |
OK    ECHEC
|       |
v       v
FIN   ROLLBACK AUTOMATIQUE
```

### Rollback automatique

Le workflow `deploy.yml` effectue automatiquement un rollback si le health check echoue apres deploiement :

1. **Sauvegarde** : L'image actuelle est sauvegardee avant deploiement
2. **Health Check** : 10 tentatives, 15 secondes entre chaque
3. **Rollback** : Si echec, retour automatique a la version precedente

### Rollback manuel

Plusieurs methodes disponibles :

| Methode | Commande | Cas d'usage |
|---------|----------|-------------|
| GitHub Actions | Actions > Rollback Deployment | Recommande |
| Makefile | `make rollback-previous` | Ligne de commande |
| Script | `./scripts/rollback.sh` | Controle total |
| Azure CLI | `az containerapp update` | Urgence |

### Commandes rapides

```bash
# Voir l'etat actuel
make rollback-current
make health-check

# Rollback
make rollback-previous           # Version precedente
make rollback-to TAG=<sha>       # Version specifique

# Lister les versions
make rollback-list
```

### Documentation detaillee

Pour les procedures completes, consultez :

- **[docs/procedure_rollback_gestion_erreurs.md](docs/procedure_rollback_gestion_erreurs.md)** : Procedure operationnelle complete
- **[docs/rollback_deploiement.md](docs/rollback_deploiement.md)** : Documentation technique du rollback
- **[rollback.md](rollback.md)** : Guide complet avec tous les fichiers et exemples

### Workflow de rollback manuel

Le fichier `.github/workflows/rollback.yml` permet de declencher un rollback depuis l'interface GitHub :

1. Aller sur **Actions** > **Rollback Deployment**
2. Cliquer sur **Run workflow**
3. Choisir le type : `previous`, `specific`, ou `latest_stable`
4. Executer et surveiller

---

## Support

En cas de probleme :
1. Verifiez les logs GitHub Actions
2. Verifiez les logs Azure Container App
3. Verifiez que tous les secrets sont bien configures
4. Testez le deploiement manuel avant l'automatisation
5. **En cas d'echec de deploiement** : Consultez [docs/procedure_rollback_gestion_erreurs.md](docs/procedure_rollback_gestion_erreurs.md)

