# Guide d'implémentation des priorités

Ce guide explique pas à pas comment implémenter les 4 points prioritaires pour atteindre 100% de conformité sur les compétences C9 à C13.

**Architecture du projet** : Application Django (front-end) qui communique avec l'API FastAPI BookSync (back-end IA).

---

## Table des matières

1. [Authentification API (C9)](#1-authentification-api-c9)
2. [Augmenter les tests à 80% (C12)](#2-augmenter-les-tests-à-80-c12)
3. [Ajouter les tests dans CI/CD (C13)](#3-ajouter-les-tests-dans-cicd-c13)
4. [Dashboard de monitoring (C11)](#4-dashboard-de-monitoring-c11)

---

## 1. Authentification API (C9)

### Contexte : Architecture Django + FastAPI

```
┌─────────────────────────────────────────────────────────────────┐
│                        UTILISATEUR                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     APPLICATION DJANGO                           │
│  ┌─────────────────┐                                            │
│  │ Auth Django     │  ← L'utilisateur se connecte via Django    │
│  │ (sessions)      │                                            │
│  └─────────────────┘                                            │
│           │                                                      │
│           ▼                                                      │
│  ┌─────────────────┐     X-API-Key: xxx                         │
│  │ Vue Django      │ ─────────────────────┐                     │
│  │ (appel API)     │                      │                     │
│  └─────────────────┘                      │                     │
└───────────────────────────────────────────│─────────────────────┘
                                            │
                                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     API FASTAPI (BookSync)                       │
│  ┌─────────────────┐                                            │
│  │ Middleware Auth │  ← Vérifie la clé API                      │
│  │ (API Key)       │                                            │
│  └─────────────────┘                                            │
│           │                                                      │
│           ▼                                                      │
│  ┌─────────────────┐                                            │
│  │ /predict/       │  ← Endpoint protégé                        │
│  └─────────────────┘                                            │
└─────────────────────────────────────────────────────────────────┘
```

### Pourquoi cette architecture valide C9 ?

| Critère C9 | Validation |
|------------|------------|
| "L'API restreint l'accès avec authentification" | ✅ L'API vérifie la clé API sur chaque requête |
| Protection contre accès direct | ✅ Sans la clé, impossible d'appeler `/predict/` |
| Séparation des responsabilités | ✅ Django gère les users, FastAPI gère l'IA |

### Objectif

Protéger l'API FastAPI avec une clé API (API Key) que Django utilisera pour communiquer.

---

### Étape 1.1 : Générer et configurer la clé API

#### Côté FastAPI (BookSync API)

Dans le fichier `.env` de l'API FastAPI, ajouter :

```bash
# Authentification API
API_KEY=votre-cle-api-secrete-ici
```

Pour générer une clé sécurisée, utiliser Python :

```python
import secrets
print(secrets.token_urlsafe(32))
# Exemple de sortie : "Kj8mN2pL9qR4sT7vW0xY3zA6bC1dE5fG"
```

#### Côté Django (Application front)

Dans le fichier `settings.py` ou `.env` de Django, ajouter la même clé :

```python
# settings.py Django
BOOKSYNC_API_URL = "https://api-booksync.azurecontainerapps.io"
BOOKSYNC_API_KEY = "votre-cle-api-secrete-ici"  # Même clé que FastAPI
```

Ou via `.env` Django :

```bash
BOOKSYNC_API_URL=https://api-booksync.azurecontainerapps.io
BOOKSYNC_API_KEY=votre-cle-api-secrete-ici
```

---

### Étape 1.2 : Créer le middleware d'authentification (FastAPI)

Créer un nouveau fichier `app/middleware/auth.py` :

```python
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
import os

# Configuration de l'API Key
API_KEY = os.getenv("API_KEY")
API_KEY_NAME = "X-API-Key"

# Header pour récupérer la clé
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)):
    """
    Vérifie que la clé API est valide.

    Args:
        api_key: La clé API envoyée dans le header

    Returns:
        La clé API si valide

    Raises:
        HTTPException 401 si la clé est manquante
        HTTPException 403 si la clé est invalide
    """
    # Si pas de clé configurée, on laisse passer (dev mode)
    if not API_KEY:
        return None

    # Si pas de clé fournie
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API manquante. Ajoutez le header X-API-Key."
        )

    # Si clé invalide
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Clé API invalide."
        )

    return api_key
```

### Étape 1.3 : Appliquer l'authentification aux routes

Modifier le fichier `app/routes/predict_routes.py` :

```python
from fastapi import APIRouter, Depends, HTTPException
from app.models.predict_request import PredictRequest
from app.models.predict_response import PredictResponse
from app.services.predict_service import PredictService
from app.middleware.auth import verify_api_key

router = APIRouter(prefix="/predict", tags=["Predictions"])
predict_service = PredictService()


@router.post("/", response_model=PredictResponse)
async def predict(
    request: PredictRequest,
    api_key: str = Depends(verify_api_key)  # Ajouter cette ligne
):
    """
    Endpoint principal pour les recommandations personnalisées.

    Nécessite une clé API valide dans le header X-API-Key.
    """
    try:
        response = await predict_service.predict(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    Health check - pas besoin d'authentification.
    """
    return {"status": "healthy", "service": "predict"}


@router.post("/test")
async def test_endpoint(
    data: dict,
    api_key: str = Depends(verify_api_key)  # Protégé aussi
):
    """Endpoint de test pour le debug."""
    return {"status": "ok", "received": data}
```

### Étape 1.4 : Mettre à jour la documentation Swagger

Dans `app/main.py`, ajouter la description de l'authentification :

```python
from fastapi import FastAPI

app = FastAPI(
    title="BookSync API Agent",
    description="""
    API de recommandation de mangas/livres avec IA.

    ## Authentification

    Cette API nécessite une clé API pour accéder aux endpoints protégés.

    Ajoutez le header suivant à vos requêtes :
    ```
    X-API-Key: votre-cle-api
    ```

    L'endpoint `/predict/health` est accessible sans authentification.
    """,
    version="1.0.0"
)
```

### Étape 1.5 : Exemple d'utilisation (test direct)

```bash
# Avec authentification (succès)
curl -X POST "http://localhost:3000/predict/" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: votre-cle-api-secrete" \
  -d '{
    "user_age": "25",
    "user_genre": "Homme",
    "genre_preference": "Japanese Manga",
    "category_preference": "Action",
    "prediction_type": "recommendation",
    "collection": {},
    "read": {},
    "user_mood": "Heureux",
    "limit": 5
  }'

# Sans authentification (erreur 401)
curl -X POST "http://localhost:3000/predict/" \
  -H "Content-Type: application/json" \
  -d '{"user_age": "25"}'
# Réponse: {"detail": "Clé API manquante. Ajoutez le header X-API-Key."}

# Avec mauvaise clé (erreur 403)
curl -X POST "http://localhost:3000/predict/" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: mauvaise-cle" \
  -d '{"user_age": "25"}'
# Réponse: {"detail": "Clé API invalide."}
```

---

### Étape 1.6 : Intégration côté Django

#### Créer un service pour appeler l'API BookSync

Dans votre application Django, créer un fichier `services/booksync_api.py` :

```python
import requests
from django.conf import settings


class BookSyncAPIError(Exception):
    """Erreur lors de l'appel à l'API BookSync."""
    pass


def get_recommendations(user_profile: dict) -> dict:
    """
    Appelle l'API BookSync pour obtenir des recommandations.

    Args:
        user_profile: Dictionnaire contenant le profil utilisateur
            - user_age: Âge de l'utilisateur
            - user_genre: Genre ("Homme"/"Femme")
            - genre_preference: Type de manga préféré
            - category_preference: Catégorie préférée
            - user_mood: Humeur actuelle
            - collection: Collection de l'utilisateur
            - read: Volumes lus
            - limit: Nombre de recommandations (max 20)

    Returns:
        dict: Réponse de l'API avec les recommandations

    Raises:
        BookSyncAPIError: En cas d'erreur de l'API
    """
    url = f"{settings.BOOKSYNC_API_URL}/predict/"

    headers = {
        "Content-Type": "application/json",
        "X-API-Key": settings.BOOKSYNC_API_KEY,  # Clé API configurée
    }

    try:
        response = requests.post(url, json=user_profile, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            raise BookSyncAPIError("Clé API manquante ou invalide")
        elif e.response.status_code == 403:
            raise BookSyncAPIError("Accès refusé à l'API")
        else:
            raise BookSyncAPIError(f"Erreur API: {e.response.status_code}")

    except requests.exceptions.Timeout:
        raise BookSyncAPIError("Timeout lors de l'appel à l'API")

    except requests.exceptions.RequestException as e:
        raise BookSyncAPIError(f"Erreur de connexion: {str(e)}")
```

#### Utiliser le service dans une vue Django

```python
# views.py Django
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .services.booksync_api import get_recommendations, BookSyncAPIError


@login_required
def recommendations_view(request):
    """Vue pour obtenir des recommandations personnalisées."""

    # Construire le profil utilisateur depuis la session Django
    user = request.user
    user_profile = {
        "user_age": str(user.profile.age),
        "user_genre": user.profile.genre,
        "genre_preference": request.GET.get("genre_preference", "Japanese Manga"),
        "category_preference": request.GET.get("category_preference", "Action"),
        "user_mood": request.GET.get("mood", "Heureux"),
        "prediction_type": "recommendation",
        "collection": get_user_collection(user),  # Fonction à implémenter
        "read": get_user_read_volumes(user),      # Fonction à implémenter
        "limit": int(request.GET.get("limit", 5)),
    }

    try:
        # Appel à l'API BookSync avec la clé API
        result = get_recommendations(user_profile)
        return JsonResponse(result)

    except BookSyncAPIError as e:
        return JsonResponse({"error": str(e)}, status=500)
```

#### Configuration Django requise

```python
# settings.py
import os

# Configuration de l'API BookSync
BOOKSYNC_API_URL = os.getenv("BOOKSYNC_API_URL", "http://localhost:3000")
BOOKSYNC_API_KEY = os.getenv("BOOKSYNC_API_KEY", "")

# Vérification au démarrage (optionnel)
if not BOOKSYNC_API_KEY:
    import warnings
    warnings.warn("BOOKSYNC_API_KEY non configurée. L'API BookSync ne fonctionnera pas.")
```

---

### Résumé de l'architecture d'authentification

```
┌─────────────────┐                              ┌─────────────────┐
│     Django      │                              │    FastAPI      │
│                 │                              │   (BookSync)    │
├─────────────────┤                              ├─────────────────┤
│                 │      POST /predict/          │                 │
│  Vue Django     │ ─────────────────────────▶  │  Middleware     │
│                 │   Header: X-API-Key: xxx     │  verify_api_key │
│                 │                              │        │        │
│                 │                              │        ▼        │
│                 │      200 OK + JSON           │  Route          │
│                 │ ◀─────────────────────────── │  /predict/      │
│                 │                              │                 │
└─────────────────┘                              └─────────────────┘

Configuration:
- Django: BOOKSYNC_API_KEY dans settings.py
- FastAPI: API_KEY dans .env
- Les deux doivent avoir LA MÊME valeur
```

---

### Structure des fichiers après modification

**Côté FastAPI (BookSync API)** :
```
app/
├── middleware/
│   ├── __init__.py      # Nouveau fichier (vide)
│   └── auth.py          # Nouveau fichier
├── routes/
│   └── predict_routes.py  # Modifié
└── main.py              # Modifié
```

**Côté Django** :
```
votre_app/
├── services/
│   └── booksync_api.py  # Nouveau fichier
├── views.py             # Modifié (ajout appel API)
└── settings.py          # Modifié (ajout config API)
```

---

## 2. Augmenter les tests à 80% (C12)

### Objectif

Passer de 39% à 80% de couverture de tests.

### Étape 2.1 : Structure des tests

```
tests/
├── __init__.py
├── conftest.py              # Fixtures partagées
├── routes/
│   ├── __init__.py
│   └── test_predict_routes.py
├── services/
│   ├── __init__.py
│   ├── test_predict_service.py
│   └── test_synthesizer.py
├── models/
│   ├── __init__.py
│   └── test_models.py
└── middleware/
    ├── __init__.py
    └── test_auth.py
```

### Étape 2.2 : Fichier conftest.py (fixtures partagées)

Créer ou modifier `tests/conftest.py` :

```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import os

# Définir les variables d'environnement pour les tests
os.environ["API_KEY"] = "test-api-key-123"
os.environ["USE_AZURE_OPENAI"] = "false"

from app.main import app


@pytest.fixture
def client():
    """Client de test FastAPI."""
    return TestClient(app)


@pytest.fixture
def api_headers():
    """Headers avec clé API valide."""
    return {
        "Content-Type": "application/json",
        "X-API-Key": "test-api-key-123"
    }


@pytest.fixture
def valid_predict_request():
    """Requête de prédiction valide."""
    return {
        "user_age": "25",
        "user_genre": "Homme",
        "genre_preference": "Japanese Manga",
        "category_preference": "Action",
        "user_comment": "",
        "prediction_type": "recommendation",
        "collection": {},
        "read": {},
        "user_mood": "Heureux",
        "limit": 5
    }


@pytest.fixture
def mock_vector_store():
    """Mock du VectorStore pour éviter les appels DB."""
    with patch('app.services.predict_service.VectorStore') as mock:
        mock_instance = Mock()
        mock_instance.similarity_search.return_value = [
            {
                "id": "123",
                "title": "Test Manga",
                "metadata": {"genre": "Action"},
                "similarity": 0.95
            }
        ]
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_synthesizer():
    """Mock du Synthesizer pour éviter les appels OpenAI."""
    with patch('app.services.predict_service.Synthesizer') as mock:
        mock_instance = Mock()
        mock_instance.generate_global_response.return_value = "Voici mes recommandations..."
        mock.return_value = mock_instance
        yield mock_instance
```

### Étape 2.3 : Tests des routes API

Créer `tests/routes/test_predict_routes.py` :

```python
import pytest
from fastapi import status


class TestHealthEndpoint:
    """Tests pour l'endpoint /predict/health."""

    def test_health_returns_200(self, client):
        """Le health check retourne 200."""
        response = client.get("/predict/health")
        assert response.status_code == status.HTTP_200_OK

    def test_health_returns_healthy_status(self, client):
        """Le health check retourne status healthy."""
        response = client.get("/predict/health")
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_no_auth_required(self, client):
        """Le health check ne nécessite pas d'authentification."""
        response = client.get("/predict/health")
        assert response.status_code == status.HTTP_200_OK


class TestPredictEndpoint:
    """Tests pour l'endpoint POST /predict/."""

    def test_predict_without_api_key_returns_401(self, client, valid_predict_request):
        """Sans clé API, retourne 401."""
        response = client.post("/predict/", json=valid_predict_request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_predict_with_invalid_api_key_returns_403(self, client, valid_predict_request):
        """Avec clé API invalide, retourne 403."""
        headers = {"X-API-Key": "mauvaise-cle"}
        response = client.post("/predict/", json=valid_predict_request, headers=headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_predict_with_valid_api_key_returns_200(
        self, client, api_headers, valid_predict_request, mock_vector_store, mock_synthesizer
    ):
        """Avec clé API valide, retourne 200."""
        response = client.post("/predict/", json=valid_predict_request, headers=api_headers)
        assert response.status_code == status.HTTP_200_OK

    def test_predict_returns_correct_structure(
        self, client, api_headers, valid_predict_request, mock_vector_store, mock_synthesizer
    ):
        """La réponse a la bonne structure."""
        response = client.post("/predict/", json=valid_predict_request, headers=api_headers)
        data = response.json()

        assert "serie_recomendees" in data
        assert "status" in data
        assert "responce_IA_global" in data

    def test_predict_missing_required_field_returns_422(self, client, api_headers):
        """Champ requis manquant retourne 422."""
        incomplete_request = {"user_age": "25"}
        response = client.post("/predict/", json=incomplete_request, headers=api_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_predict_invalid_limit_returns_422(self, client, api_headers, valid_predict_request):
        """Limit > 20 retourne 422."""
        valid_predict_request["limit"] = 50
        response = client.post("/predict/", json=valid_predict_request, headers=api_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestTestEndpoint:
    """Tests pour l'endpoint POST /predict/test."""

    def test_test_endpoint_requires_auth(self, client):
        """L'endpoint test nécessite une authentification."""
        response = client.post("/predict/test", json={"test": "data"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_test_endpoint_returns_received_data(self, client, api_headers):
        """L'endpoint test retourne les données reçues."""
        test_data = {"key": "value", "number": 42}
        response = client.post("/predict/test", json=test_data, headers=api_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "ok"
        assert data["received"] == test_data
```

### Étape 2.4 : Tests des modèles Pydantic

Créer `tests/models/test_models.py` :

```python
import pytest
from pydantic import ValidationError
from app.models.predict_request import PredictRequest
from app.models.predict_response import PredictResponse, RecommendedSerie


class TestPredictRequest:
    """Tests pour le modèle PredictRequest."""

    def test_valid_request_creation(self):
        """Création d'une requête valide."""
        request = PredictRequest(
            user_age="25",
            user_genre="Homme",
            genre_preference="Japanese Manga",
            category_preference="Action",
            prediction_type="recommendation",
            collection={},
            read={},
            user_mood="Heureux",
            limit=5
        )
        assert request.user_age == "25"
        assert request.limit == 5

    def test_default_values(self):
        """Les valeurs par défaut sont appliquées."""
        request = PredictRequest(
            user_age="20",
            user_genre="Femme",
            prediction_type="recommendation"
        )
        assert request.limit == 5
        assert request.collection == {}
        assert request.read == {}

    def test_invalid_limit_too_high(self):
        """Limit > 20 lève une erreur."""
        with pytest.raises(ValidationError):
            PredictRequest(
                user_age="25",
                user_genre="Homme",
                prediction_type="recommendation",
                limit=50
            )

    def test_invalid_prediction_type(self):
        """Type de prédiction invalide lève une erreur."""
        with pytest.raises(ValidationError):
            PredictRequest(
                user_age="25",
                user_genre="Homme",
                prediction_type="invalid_type"
            )


class TestPredictResponse:
    """Tests pour le modèle PredictResponse."""

    def test_valid_response_creation(self):
        """Création d'une réponse valide."""
        response = PredictResponse(
            serie_recomendees=[],
            status="success",
            responce_IA_global="Test message"
        )
        assert response.status == "success"

    def test_response_with_recommendations(self):
        """Réponse avec des recommandations."""
        serie = RecommendedSerie(
            title="Test Manga",
            id_series="123",
            responce_IA="Recommandé pour vous"
        )
        response = PredictResponse(
            serie_recomendees=[serie],
            status="success",
            responce_IA_global="Voici une recommandation"
        )
        assert len(response.serie_recomendees) == 1
        assert response.serie_recomendees[0].title == "Test Manga"


class TestRecommendedSerie:
    """Tests pour le modèle RecommendedSerie."""

    def test_valid_serie_creation(self):
        """Création d'une série recommandée valide."""
        serie = RecommendedSerie(
            title="One Piece",
            id_series="456",
            responce_IA="Un classique incontournable"
        )
        assert serie.title == "One Piece"
        assert serie.id_series == "456"
```

### Étape 2.5 : Tests du middleware d'authentification

Créer `tests/middleware/test_auth.py` :

```python
import pytest
from unittest.mock import patch
from fastapi import HTTPException
import os


class TestApiKeyVerification:
    """Tests pour la vérification de la clé API."""

    @pytest.mark.asyncio
    async def test_valid_api_key_passes(self):
        """Une clé API valide passe la vérification."""
        with patch.dict(os.environ, {"API_KEY": "test-key"}):
            from app.middleware.auth import verify_api_key
            result = await verify_api_key("test-key")
            assert result == "test-key"

    @pytest.mark.asyncio
    async def test_missing_api_key_raises_401(self):
        """Clé API manquante lève 401."""
        with patch.dict(os.environ, {"API_KEY": "test-key"}):
            from app.middleware.auth import verify_api_key
            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key(None)
            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_api_key_raises_403(self):
        """Clé API invalide lève 403."""
        with patch.dict(os.environ, {"API_KEY": "test-key"}):
            from app.middleware.auth import verify_api_key
            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key("wrong-key")
            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_no_api_key_configured_passes(self):
        """Sans clé configurée, tout passe (mode dev)."""
        with patch.dict(os.environ, {"API_KEY": ""}):
            from app.middleware.auth import verify_api_key
            result = await verify_api_key(None)
            assert result is None
```

### Étape 2.6 : Tests des services

Créer `tests/services/test_predict_service.py` :

```python
import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.predict_service import PredictService
from app.models.predict_request import PredictRequest


class TestPredictService:
    """Tests pour le service de prédiction."""

    @pytest.fixture
    def predict_service(self):
        """Instance du service de prédiction."""
        with patch('app.services.predict_service.VectorStore'):
            with patch('app.services.predict_service.Synthesizer'):
                return PredictService()

    @pytest.fixture
    def sample_request(self):
        """Requête de test."""
        return PredictRequest(
            user_age="25",
            user_genre="Homme",
            genre_preference="Japanese Manga",
            category_preference="Action",
            prediction_type="recommendation",
            collection={},
            read={},
            user_mood="Heureux",
            limit=5
        )

    def test_service_initialization(self, predict_service):
        """Le service s'initialise correctement."""
        assert predict_service is not None

    @pytest.mark.asyncio
    async def test_predict_returns_response(self, predict_service, sample_request):
        """La méthode predict retourne une réponse."""
        # Mock des dépendances internes
        predict_service.vector_store.similarity_search = AsyncMock(return_value=[
            {"id": "1", "title": "Test", "metadata": {}, "similarity": 0.9}
        ])
        predict_service.synthesizer.generate_global_response = AsyncMock(
            return_value="Recommandations..."
        )

        response = await predict_service.predict(sample_request)

        assert response is not None
        assert response.status == "success"

    @pytest.mark.asyncio
    async def test_predict_with_empty_collection(self, predict_service, sample_request):
        """Prédiction avec collection vide fonctionne."""
        predict_service.vector_store.similarity_search = AsyncMock(return_value=[])
        predict_service.synthesizer.generate_global_response = AsyncMock(
            return_value="Pas de recommandations"
        )

        response = await predict_service.predict(sample_request)

        assert response.status == "success"
        assert len(response.serie_recomendees) == 0
```

### Étape 2.7 : Lancer les tests

```bash
# Tous les tests avec couverture
pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing

# Vérifier que la couverture atteint 80%
pytest tests/ --cov=app --cov-fail-under=80

# Tests par catégorie
pytest tests/ -m unit -v          # Tests unitaires
pytest tests/ -m integration -v   # Tests d'intégration
pytest tests/ -m api -v           # Tests API
```

### Résultat attendu

```
Name                              Stmts   Miss  Cover
-----------------------------------------------------
app/__init__.py                       0      0   100%
app/main.py                          15      2    87%
app/middleware/auth.py               20      2    90%
app/models/predict_request.py        25      3    88%
app/models/predict_response.py       18      2    89%
app/routes/predict_routes.py         35      5    86%
app/services/predict_service.py      60      8    87%
-----------------------------------------------------
TOTAL                               173     22    87%
```

---

## 3. Ajouter les tests dans CI/CD (C13)

### Objectif

Ajouter un job de tests dans le pipeline GitHub Actions avant le déploiement.

### Étape 3.1 : Modifier le workflow

Modifier `.github/workflows/deploy.yml` :

```yaml
name: Build, Test and Deploy to Azure Container Apps

on:
  push:
    branches:
      - main
    paths-ignore:
      - '**.md'
      - 'docs/**'
      - '.gitignore'

env:
  AZURE_CONTAINER_REGISTRY: booksyncrepo.azurecr.io
  IMAGE_NAME: api-booksync
  RESOURCE_GROUP: vplatevoetRG
  CONTAINER_APP: api-booksync

jobs:
  # ==========================================
  # JOB 1 : Tests automatisés
  # ==========================================
  test:
    name: Run Tests
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run tests with coverage
        env:
          API_KEY: test-key-for-ci
          USE_AZURE_OPENAI: false
        run: |
          pytest tests/ -v --cov=app --cov-report=xml --cov-report=term-missing

      - name: Check coverage threshold
        run: |
          coverage report --fail-under=80

      - name: Upload coverage report
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: coverage-report
          path: coverage.xml

  # ==========================================
  # JOB 2 : Build et déploiement
  # ==========================================
  build-and-deploy:
    name: Build and Deploy
    runs-on: ubuntu-latest
    needs: test  # Attend que les tests passent

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Login to Azure
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}

      - name: Login to Azure Container Registry
        run: |
          az acr login --name booksyncrepo

      - name: Build and push Docker image
        run: |
          docker build -t ${{ env.AZURE_CONTAINER_REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }} .
          docker build -t ${{ env.AZURE_CONTAINER_REGISTRY }}/${{ env.IMAGE_NAME }}:latest .
          docker push ${{ env.AZURE_CONTAINER_REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
          docker push ${{ env.AZURE_CONTAINER_REGISTRY }}/${{ env.IMAGE_NAME }}:latest

      - name: Deploy to Azure Container Apps
        run: |
          az containerapp update \
            --name ${{ env.CONTAINER_APP }} \
            --resource-group ${{ env.RESOURCE_GROUP }} \
            --image ${{ env.AZURE_CONTAINER_REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
```

### Étape 3.2 : Ajouter un workflow de tests pour les PR

Créer `.github/workflows/test.yml` :

```yaml
name: Tests on Pull Request

on:
  pull_request:
    branches:
      - main
      - develop

jobs:
  test:
    name: Run Tests
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run linting
        run: |
          pip install flake8
          flake8 app/ --max-line-length=120 --ignore=E501,W503

      - name: Run tests
        env:
          API_KEY: test-key-for-ci
          USE_AZURE_OPENAI: false
        run: |
          pytest tests/ -v --cov=app --cov-report=term-missing

      - name: Check coverage
        run: |
          coverage report --fail-under=80
```

### Étape 3.3 : Visualisation du pipeline

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Push main     │────▶│   Job: test     │────▶│ Job: build-     │
│                 │     │                 │     │ and-deploy      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │                        │
                               ▼                        ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │ - Install deps  │     │ - Docker build  │
                        │ - Run pytest    │     │ - Push to ACR   │
                        │ - Check 80%     │     │ - Deploy Azure  │
                        └─────────────────┘     └─────────────────┘
```

---

## 4. Dashboard de monitoring LLMOps (C11)

### Objectif

Mettre en place un dashboard de monitoring avec Prometheus et Grafana, incluant des métriques **LLMOps** spécifiques pour le suivi du modèle IA.

### Pourquoi LLMOps ?

Pour un projet utilisant l'IA générative (Azure OpenAI), il est important de suivre des métriques spécifiques :

| Métrique LLMOps | Description | Importance |
|-----------------|-------------|------------|
| **Tokens consommés** | Nombre de tokens input/output | Coût et budget |
| **Latence LLM** | Temps de réponse Azure OpenAI | Performance |
| **Latence embeddings** | Temps de génération des vecteurs | Performance |
| **Taux d'erreur IA** | Erreurs API OpenAI | Fiabilité |
| **Coût estimé** | Estimation du coût par requête | Budget |
| **Qualité des réponses** | Score de similarité moyen | Pertinence |

### Architecture LLMOps proposée

```
┌─────────────────────────────────────────────────────────────────┐
│                     API FastAPI (BookSync)                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   /predict/     │  │  Azure OpenAI   │  │   PostgreSQL    │  │
│  │   endpoint      │──│  (GPT-4o-mini)  │──│   (pgvector)    │  │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  │
│           │                    │                    │           │
│           ▼                    ▼                    ▼           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Métriques Prometheus + LLMOps               │   │
│  │  - Latence API        - Tokens consommés                 │   │
│  │  - Latence LLM        - Coût estimé                      │   │
│  │  - Latence embeddings - Similarité moyenne               │   │
│  │  - Erreurs            - Requêtes actives                 │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Prometheus    │────▶│    Grafana      │────▶│   Alerting      │
│   (collecte)    │     │  (dashboard)    │     │  (optionnel)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

---

### Étape 4.1 : Ajouter les dépendances

Dans `requirements.txt`, ajouter :

```
prometheus-fastapi-instrumentator==6.1.0
prometheus-client==0.19.0
```

### Étape 4.2 : Configurer Prometheus dans FastAPI

Modifier `app/main.py` :

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.routes import predict_routes

# Création de l'application
app = FastAPI(
    title="BookSync API Agent",
    description="API de recommandation de mangas/livres avec IA",
    version="1.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclure les routes
app.include_router(predict_routes.router)

# Configuration Prometheus
# Expose les métriques sur /metrics
instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/metrics", "/health"],
    inprogress_name="http_requests_inprogress",
    inprogress_labels=True,
)

# Instrumenter l'application
instrumentator.instrument(app)

# Exposer les métriques
instrumentator.expose(app, include_in_schema=True, tags=["Monitoring"])


@app.get("/")
async def root():
    """Page d'accueil de l'API."""
    return {
        "message": "BookSync API Agent",
        "docs": "/docs",
        "health": "/predict/health",
        "metrics": "/metrics"
    }
```

### Étape 4.3 : Ajouter des métriques LLMOps personnalisées

Créer `app/metrics/llm_metrics.py` :

```python
from prometheus_client import Counter, Histogram, Gauge, Summary
import time

# ============================================================
# MÉTRIQUES GÉNÉRALES API
# ============================================================

# Compteur de prédictions par statut et humeur
PREDICTIONS_TOTAL = Counter(
    'booksync_predictions_total',
    'Nombre total de prédictions',
    ['status', 'mood', 'prediction_type']
)

# Histogramme de latence globale des prédictions
PREDICTION_LATENCY = Histogram(
    'booksync_prediction_latency_seconds',
    'Latence totale des prédictions en secondes',
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

# Gauge pour les requêtes actives
ACTIVE_REQUESTS = Gauge(
    'booksync_active_requests',
    'Nombre de requêtes de prédiction en cours'
)

# ============================================================
# MÉTRIQUES LLMOps - AZURE OPENAI
# ============================================================

# Latence des appels au LLM (chat completions)
LLM_LATENCY = Histogram(
    'booksync_llm_latency_seconds',
    'Latence des appels Azure OpenAI (chat)',
    ['model', 'operation'],
    buckets=[0.5, 1.0, 2.0, 3.0, 5.0, 10.0]
)

# Latence de génération des embeddings
EMBEDDING_LATENCY = Histogram(
    'booksync_embedding_latency_seconds',
    'Latence de génération des embeddings Azure OpenAI',
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0]
)

# Compteur de tokens consommés
TOKENS_TOTAL = Counter(
    'booksync_tokens_total',
    'Nombre total de tokens consommés',
    ['model', 'type']  # type: input, output
)

# Coût estimé (en USD)
ESTIMATED_COST = Counter(
    'booksync_estimated_cost_usd',
    'Coût estimé des appels API en USD',
    ['model']
)

# Erreurs LLM
LLM_ERRORS = Counter(
    'booksync_llm_errors_total',
    'Nombre total d\'erreurs LLM',
    ['model', 'error_type']
)

# ============================================================
# MÉTRIQUES LLMOps - RECHERCHE VECTORIELLE
# ============================================================

# Latence de recherche vectorielle
VECTOR_SEARCH_LATENCY = Histogram(
    'booksync_vector_search_latency_seconds',
    'Latence de recherche dans pgvector',
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0]
)

# Score de similarité moyen
SIMILARITY_SCORE = Summary(
    'booksync_similarity_score',
    'Score de similarité des résultats de recherche'
)

# Nombre de résultats retournés
SEARCH_RESULTS_COUNT = Histogram(
    'booksync_search_results_count',
    'Nombre de résultats de recherche vectorielle',
    buckets=[0, 1, 2, 5, 10, 20]
)

# ============================================================
# MÉTRIQUES LLMOps - QUALITÉ
# ============================================================

# Nombre de recommandations générées
RECOMMENDATIONS_COUNT = Histogram(
    'booksync_recommendations_count',
    'Nombre de recommandations générées par requête',
    buckets=[0, 1, 2, 3, 5, 10, 20]
)

# ============================================================
# FONCTIONS HELPER
# ============================================================

# Tarifs Azure OpenAI (à mettre à jour selon votre contrat)
PRICING = {
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},  # par 1K tokens
    "text-embedding-3-large": {"input": 0.00013, "output": 0},
}


def track_prediction(status: str, mood: str, prediction_type: str = "recommendation"):
    """Incrémenter le compteur de prédictions."""
    PREDICTIONS_TOTAL.labels(
        status=status,
        mood=mood,
        prediction_type=prediction_type
    ).inc()


def track_llm_call(model: str, operation: str, latency: float, input_tokens: int, output_tokens: int):
    """
    Tracker un appel LLM avec toutes ses métriques.

    Args:
        model: Nom du modèle (gpt-4o-mini, text-embedding-3-large)
        operation: Type d'opération (chat, embedding)
        latency: Temps de réponse en secondes
        input_tokens: Nombre de tokens en entrée
        output_tokens: Nombre de tokens en sortie
    """
    # Latence
    LLM_LATENCY.labels(model=model, operation=operation).observe(latency)

    # Tokens
    TOKENS_TOTAL.labels(model=model, type="input").inc(input_tokens)
    TOKENS_TOTAL.labels(model=model, type="output").inc(output_tokens)

    # Coût estimé
    if model in PRICING:
        cost = (input_tokens / 1000 * PRICING[model]["input"] +
                output_tokens / 1000 * PRICING[model]["output"])
        ESTIMATED_COST.labels(model=model).inc(cost)


def track_embedding(latency: float, tokens: int):
    """Tracker la génération d'un embedding."""
    EMBEDDING_LATENCY.observe(latency)
    TOKENS_TOTAL.labels(model="text-embedding-3-large", type="input").inc(tokens)

    # Coût embedding
    cost = tokens / 1000 * PRICING["text-embedding-3-large"]["input"]
    ESTIMATED_COST.labels(model="text-embedding-3-large").inc(cost)


def track_vector_search(latency: float, results_count: int, avg_similarity: float):
    """Tracker une recherche vectorielle."""
    VECTOR_SEARCH_LATENCY.observe(latency)
    SEARCH_RESULTS_COUNT.observe(results_count)
    if avg_similarity:
        SIMILARITY_SCORE.observe(avg_similarity)


def track_llm_error(model: str, error_type: str):
    """Tracker une erreur LLM."""
    LLM_ERRORS.labels(model=model, error_type=error_type).inc()


def track_recommendations(count: int):
    """Tracker le nombre de recommandations générées."""
    RECOMMENDATIONS_COUNT.observe(count)
```

### Étape 4.4 : Utiliser les métriques LLMOps dans les services

#### Dans `app/services/predict_service.py` :

```python
import time
from app.metrics.llm_metrics import (
    track_prediction,
    track_recommendations,
    track_vector_search,
    ACTIVE_REQUESTS,
    PREDICTION_LATENCY
)


class PredictService:

    async def predict(self, request: PredictRequest) -> PredictResponse:
        """Effectue une prédiction avec tracking des métriques LLMOps."""
        ACTIVE_REQUESTS.inc()
        start_time = time.time()

        try:
            # Recherche vectorielle avec métriques
            search_start = time.time()
            search_results = await self.vector_store.similarity_search(...)
            search_latency = time.time() - search_start

            # Tracker la recherche vectorielle
            avg_similarity = sum(r['similarity'] for r in search_results) / len(search_results) if search_results else 0
            track_vector_search(
                latency=search_latency,
                results_count=len(search_results),
                avg_similarity=avg_similarity
            )

            # Génération IA
            response = await self.synthesizer.generate_response(...)

            # Tracker le nombre de recommandations
            track_recommendations(len(response.serie_recomendees))

            # Tracker le succès
            total_latency = time.time() - start_time
            PREDICTION_LATENCY.observe(total_latency)
            track_prediction(
                status="success",
                mood=request.user_mood,
                prediction_type=request.prediction_type
            )

            return response

        except Exception as e:
            # Tracker l'erreur
            track_prediction(
                status="error",
                mood=request.user_mood,
                prediction_type=request.prediction_type
            )
            raise

        finally:
            ACTIVE_REQUESTS.dec()
```

#### Dans `app/services/synthesizer.py` :

```python
import time
from app.metrics.llm_metrics import track_llm_call, track_llm_error


class Synthesizer:

    async def generate_response(self, profile: dict, results: list) -> str:
        """Génère une réponse avec tracking LLMOps."""
        start_time = time.time()

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[...],
                max_tokens=200
            )

            # Extraire les métriques de la réponse OpenAI
            latency = time.time() - start_time
            usage = response.usage

            # Tracker l'appel LLM
            track_llm_call(
                model="gpt-4o-mini",
                operation="chat",
                latency=latency,
                input_tokens=usage.prompt_tokens,
                output_tokens=usage.completion_tokens
            )

            return response.choices[0].message.content

        except Exception as e:
            track_llm_error(model="gpt-4o-mini", error_type=type(e).__name__)
            raise
```

#### Dans `app/database/vector_store.py` :

```python
import time
from app.metrics.llm_metrics import track_embedding, track_llm_error


class VectorStore:

    async def get_embedding(self, text: str) -> list:
        """Génère un embedding avec tracking LLMOps."""
        start_time = time.time()

        try:
            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=text
            )

            latency = time.time() - start_time
            tokens = response.usage.total_tokens

            # Tracker l'embedding
            track_embedding(latency=latency, tokens=tokens)

            return response.data[0].embedding

        except Exception as e:
            track_llm_error(model="text-embedding-3-large", error_type=type(e).__name__)
            raise
```

### Étape 4.5 : Créer le docker-compose pour Prometheus + Grafana

Créer `docker-compose.monitoring.yml` :

```yaml
version: '3.8'

services:
  # Application BookSync
  api:
    build: .
    ports:
      - "3000:3000"
    environment:
      - API_KEY=${API_KEY}
      - USE_AZURE_OPENAI=${USE_AZURE_OPENAI}
      - AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT}
      - AZURE_OPENAI_KEY=${AZURE_OPENAI_KEY}
      - TIMESCALE_SERVICE_URL=${TIMESCALE_SERVICE_URL}
    networks:
      - monitoring

  # Prometheus - Collecte des métriques
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    networks:
      - monitoring

  # Grafana - Dashboard de visualisation
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
    depends_on:
      - prometheus
    networks:
      - monitoring

networks:
  monitoring:
    driver: bridge

volumes:
  prometheus_data:
  grafana_data:
```

### Étape 4.6 : Configuration Prometheus

Créer `monitoring/prometheus.yml` :

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'booksync-api'
    static_configs:
      - targets: ['api:3000']
    metrics_path: /metrics
    scrape_interval: 10s
```

### Étape 4.7 : Provisioning Grafana

Créer `monitoring/grafana/provisioning/datasources/datasource.yml` :

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false
```

Créer `monitoring/grafana/provisioning/dashboards/dashboard.yml` :

```yaml
apiVersion: 1

providers:
  - name: 'BookSync Dashboards'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    options:
      path: /etc/grafana/provisioning/dashboards
```

### Étape 4.8 : Dashboard Grafana LLMOps

Créer `monitoring/grafana/provisioning/dashboards/booksync-llmops.json` :

```json
{
  "dashboard": {
    "title": "BookSync API - LLMOps Dashboard",
    "tags": ["booksync", "llmops", "ai"],
    "timezone": "browser",
    "panels": [
      {
        "title": "Vue d'ensemble",
        "type": "row",
        "gridPos": {"x": 0, "y": 0, "w": 24, "h": 1}
      },
      {
        "title": "Requêtes actives",
        "type": "gauge",
        "gridPos": {"x": 0, "y": 1, "w": 4, "h": 4},
        "targets": [{"expr": "booksync_active_requests"}]
      },
      {
        "title": "Prédictions totales",
        "type": "stat",
        "gridPos": {"x": 4, "y": 1, "w": 4, "h": 4},
        "targets": [{"expr": "sum(booksync_predictions_total)"}]
      },
      {
        "title": "Taux de succès",
        "type": "stat",
        "gridPos": {"x": 8, "y": 1, "w": 4, "h": 4},
        "targets": [{
          "expr": "sum(booksync_predictions_total{status='success'}) / sum(booksync_predictions_total) * 100",
          "legendFormat": "%"
        }]
      },
      {
        "title": "Coût estimé (USD)",
        "type": "stat",
        "gridPos": {"x": 12, "y": 1, "w": 4, "h": 4},
        "targets": [{"expr": "sum(booksync_estimated_cost_usd)"}],
        "fieldConfig": {"defaults": {"unit": "currencyUSD"}}
      },
      {
        "title": "Tokens consommés",
        "type": "stat",
        "gridPos": {"x": 16, "y": 1, "w": 4, "h": 4},
        "targets": [{"expr": "sum(booksync_tokens_total)"}]
      },
      {
        "title": "Erreurs LLM",
        "type": "stat",
        "gridPos": {"x": 20, "y": 1, "w": 4, "h": 4},
        "targets": [{"expr": "sum(booksync_llm_errors_total)"}],
        "fieldConfig": {"defaults": {"thresholds": {"steps": [{"color": "green", "value": 0}, {"color": "red", "value": 1}]}}}
      },

      {
        "title": "Métriques LLM (Azure OpenAI)",
        "type": "row",
        "gridPos": {"x": 0, "y": 5, "w": 24, "h": 1}
      },
      {
        "title": "Latence LLM (GPT-4o-mini)",
        "type": "timeseries",
        "gridPos": {"x": 0, "y": 6, "w": 12, "h": 8},
        "targets": [
          {"expr": "histogram_quantile(0.50, rate(booksync_llm_latency_seconds_bucket{model='gpt-4o-mini'}[5m]))", "legendFormat": "p50"},
          {"expr": "histogram_quantile(0.95, rate(booksync_llm_latency_seconds_bucket{model='gpt-4o-mini'}[5m]))", "legendFormat": "p95"},
          {"expr": "histogram_quantile(0.99, rate(booksync_llm_latency_seconds_bucket{model='gpt-4o-mini'}[5m]))", "legendFormat": "p99"}
        ],
        "fieldConfig": {"defaults": {"unit": "s"}}
      },
      {
        "title": "Tokens par minute",
        "type": "timeseries",
        "gridPos": {"x": 12, "y": 6, "w": 12, "h": 8},
        "targets": [
          {"expr": "rate(booksync_tokens_total{type='input'}[1m]) * 60", "legendFormat": "Input tokens/min"},
          {"expr": "rate(booksync_tokens_total{type='output'}[1m]) * 60", "legendFormat": "Output tokens/min"}
        ]
      },

      {
        "title": "Métriques Embeddings",
        "type": "row",
        "gridPos": {"x": 0, "y": 14, "w": 24, "h": 1}
      },
      {
        "title": "Latence Embeddings",
        "type": "timeseries",
        "gridPos": {"x": 0, "y": 15, "w": 12, "h": 8},
        "targets": [
          {"expr": "histogram_quantile(0.50, rate(booksync_embedding_latency_seconds_bucket[5m]))", "legendFormat": "p50"},
          {"expr": "histogram_quantile(0.95, rate(booksync_embedding_latency_seconds_bucket[5m]))", "legendFormat": "p95"}
        ],
        "fieldConfig": {"defaults": {"unit": "s"}}
      },
      {
        "title": "Coût par modèle (USD/heure)",
        "type": "timeseries",
        "gridPos": {"x": 12, "y": 15, "w": 12, "h": 8},
        "targets": [
          {"expr": "rate(booksync_estimated_cost_usd{model='gpt-4o-mini'}[1h]) * 3600", "legendFormat": "GPT-4o-mini"},
          {"expr": "rate(booksync_estimated_cost_usd{model='text-embedding-3-large'}[1h]) * 3600", "legendFormat": "Embeddings"}
        ],
        "fieldConfig": {"defaults": {"unit": "currencyUSD"}}
      },

      {
        "title": "Recherche Vectorielle (pgvector)",
        "type": "row",
        "gridPos": {"x": 0, "y": 23, "w": 24, "h": 1}
      },
      {
        "title": "Latence recherche vectorielle",
        "type": "timeseries",
        "gridPos": {"x": 0, "y": 24, "w": 8, "h": 8},
        "targets": [
          {"expr": "histogram_quantile(0.50, rate(booksync_vector_search_latency_seconds_bucket[5m]))", "legendFormat": "p50"},
          {"expr": "histogram_quantile(0.95, rate(booksync_vector_search_latency_seconds_bucket[5m]))", "legendFormat": "p95"}
        ],
        "fieldConfig": {"defaults": {"unit": "s"}}
      },
      {
        "title": "Score de similarité moyen",
        "type": "gauge",
        "gridPos": {"x": 8, "y": 24, "w": 8, "h": 8},
        "targets": [{"expr": "booksync_similarity_score{quantile='0.5'}"}],
        "fieldConfig": {"defaults": {"min": 0, "max": 1, "thresholds": {"steps": [{"color": "red", "value": 0}, {"color": "yellow", "value": 0.5}, {"color": "green", "value": 0.7}]}}}
      },
      {
        "title": "Résultats par recherche",
        "type": "timeseries",
        "gridPos": {"x": 16, "y": 24, "w": 8, "h": 8},
        "targets": [{"expr": "histogram_quantile(0.5, rate(booksync_search_results_count_bucket[5m]))", "legendFormat": "Médiane résultats"}]
      },

      {
        "title": "Qualité des recommandations",
        "type": "row",
        "gridPos": {"x": 0, "y": 32, "w": 24, "h": 1}
      },
      {
        "title": "Recommandations par requête",
        "type": "timeseries",
        "gridPos": {"x": 0, "y": 33, "w": 12, "h": 8},
        "targets": [{"expr": "histogram_quantile(0.5, rate(booksync_recommendations_count_bucket[5m]))", "legendFormat": "Médiane"}]
      },
      {
        "title": "Distribution par humeur",
        "type": "piechart",
        "gridPos": {"x": 12, "y": 33, "w": 12, "h": 8},
        "targets": [{"expr": "sum by (mood) (booksync_predictions_total)", "legendFormat": "{{mood}}"}]
      },

      {
        "title": "Erreurs et Alertes",
        "type": "row",
        "gridPos": {"x": 0, "y": 41, "w": 24, "h": 1}
      },
      {
        "title": "Erreurs LLM par type",
        "type": "timeseries",
        "gridPos": {"x": 0, "y": 42, "w": 12, "h": 8},
        "targets": [{"expr": "sum by (error_type) (rate(booksync_llm_errors_total[5m]))", "legendFormat": "{{error_type}}"}]
      },
      {
        "title": "Erreurs HTTP",
        "type": "timeseries",
        "gridPos": {"x": 12, "y": 42, "w": 12, "h": 8},
        "targets": [{"expr": "sum by (status) (rate(http_requests_total{status=~'4..|5..'}[5m]))", "legendFormat": "HTTP {{status}}"}]
      }
    ]
  }
}
```

### Description des panneaux LLMOps

| Section | Panneaux | Métriques suivies |
|---------|----------|-------------------|
| **Vue d'ensemble** | 6 stats | Requêtes actives, prédictions, taux succès, coût, tokens, erreurs |
| **Métriques LLM** | 2 graphiques | Latence GPT-4o-mini (p50/p95/p99), tokens input/output |
| **Embeddings** | 2 graphiques | Latence embeddings, coût par modèle |
| **Recherche vectorielle** | 3 graphiques | Latence pgvector, score similarité, nb résultats |
| **Qualité** | 2 graphiques | Recommandations/requête, distribution par humeur |
| **Erreurs** | 2 graphiques | Erreurs LLM par type, erreurs HTTP |

### Étape 4.9 : Lancer le monitoring

```bash
# Démarrer tous les services
docker-compose -f docker-compose.monitoring.yml up -d

# Vérifier les services
docker-compose -f docker-compose.monitoring.yml ps

# Accéder aux interfaces
# API: http://localhost:3000
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3001 (admin/admin)
```

### Étape 4.10 : Structure finale du monitoring LLMOps

```
app/
├── metrics/
│   ├── __init__.py
│   └── llm_metrics.py      # Métriques LLMOps personnalisées

monitoring/
├── prometheus.yml
└── grafana/
    └── provisioning/
        ├── datasources/
        │   └── datasource.yml
        └── dashboards/
            ├── dashboard.yml
            └── booksync-llmops.json   # Dashboard LLMOps
```

### Résumé des métriques LLMOps implémentées

| Catégorie | Métrique | Type | Description |
|-----------|----------|------|-------------|
| **API** | `booksync_predictions_total` | Counter | Nombre de prédictions par statut/humeur |
| **API** | `booksync_prediction_latency_seconds` | Histogram | Latence totale des prédictions |
| **API** | `booksync_active_requests` | Gauge | Requêtes en cours |
| **LLM** | `booksync_llm_latency_seconds` | Histogram | Latence appels Azure OpenAI |
| **LLM** | `booksync_tokens_total` | Counter | Tokens consommés (input/output) |
| **LLM** | `booksync_estimated_cost_usd` | Counter | Coût estimé en USD |
| **LLM** | `booksync_llm_errors_total` | Counter | Erreurs LLM par type |
| **Embeddings** | `booksync_embedding_latency_seconds` | Histogram | Latence génération embeddings |
| **Vector** | `booksync_vector_search_latency_seconds` | Histogram | Latence recherche pgvector |
| **Vector** | `booksync_similarity_score` | Summary | Score de similarité moyen |
| **Qualité** | `booksync_recommendations_count` | Histogram | Nombre de recommandations/requête |

---

### Projets GitHub de référence pour LLMOps/MLOps

Ces projets open-source peuvent servir d'inspiration et de référence :

#### Projets MLOps avec FastAPI + Prometheus + Grafana

| Projet | Description | Lien |
|--------|-------------|------|
| **FastAPI-Prometheus-Grafana-MLOps** | MLOps complet pour monitoring ML avec FastAPI | [GitHub](https://github.com/BaraaZ95/FastAPI-Prometheus-Grafana-MLOPs) |
| **fastapi-prometheus-grafana** | Setup minimal FastAPI + Prometheus + Grafana | [GitHub](https://github.com/Kludex/fastapi-prometheus-grafana) |
| **ml-monitoring** | Exemple REST service ML avec Prometheus+Grafana | [GitHub](https://github.com/jeremyjordan/ml-monitoring) |
| **reco-model-monitoring** | Monitoring de modèle de recommandation | [GitHub](https://github.com/silverstone1903/reco-model-monitoring) |

#### Projets LLMOps (spécifique aux LLMs)

| Projet | Description | Lien |
|--------|-------------|------|
| **fastapi-observability** | Observabilité complète : Traces, Metrics, Logs avec OpenTelemetry | [GitHub](https://github.com/blueswen/fastapi-observability) |
| **mlops (dpleus)** | Plateforme MLOps avec prefect, mlflow, FastAPI | [GitHub](https://github.com/dpleus/mlops) |

#### Articles et tutoriels recommandés

- [From Prompts to Metrics: Building Observable LLM Agents](https://engineering.teknasyon.com/from-prompts-to-metrics-building-observable-llm-agents-using-fastapi-opentelemetry-prometheus-359d3132d92b) - Guide complet pour rendre observable un agent LLM avec FastAPI, OpenTelemetry, Prometheus et Grafana
- [Getting Started: Monitoring a FastAPI App with Grafana and Prometheus](https://dev.to/ken_mwaura1/getting-started-monitoring-a-fastapi-app-with-grafana-and-prometheus-a-step-by-step-guide-3fbn) - Tutoriel étape par étape

#### Ce qu'on peut apprendre de ces projets

1. **Structure docker-compose** : Comment organiser les services Prometheus/Grafana
2. **Métriques custom** : Quelles métriques tracker pour un modèle IA
3. **Dashboards Grafana** : Exemples de visualisations pertinentes
4. **OpenTelemetry** : Alternative/complément à Prometheus pour le tracing

---

## Récapitulatif des fichiers à créer/modifier

### Nouveaux fichiers

| Fichier | Description | Priorité |
|---------|-------------|----------|
| `app/middleware/__init__.py` | Init package middleware | C9 |
| `app/middleware/auth.py` | Middleware authentification API Key | C9 |
| `app/metrics/__init__.py` | Init package metrics | C11 |
| `app/metrics/llm_metrics.py` | Métriques LLMOps (tokens, latence, coût) | C11 |
| `tests/conftest.py` | Fixtures pytest partagées | C12 |
| `tests/routes/test_predict_routes.py` | Tests endpoints API | C12 |
| `tests/models/test_models.py` | Tests modèles Pydantic | C12 |
| `tests/middleware/test_auth.py` | Tests authentification | C12 |
| `tests/services/test_predict_service.py` | Tests services | C12 |
| `.github/workflows/test.yml` | Workflow tests pour PR | C13 |
| `docker-compose.monitoring.yml` | Stack Prometheus + Grafana | C11 |
| `monitoring/prometheus.yml` | Config scraping Prometheus | C11 |
| `monitoring/grafana/provisioning/datasources/datasource.yml` | Source Prometheus | C11 |
| `monitoring/grafana/provisioning/dashboards/dashboard.yml` | Config dashboards | C11 |
| `monitoring/grafana/provisioning/dashboards/booksync-llmops.json` | Dashboard LLMOps | C11 |

### Fichiers modifiés

| Fichier | Modification | Priorité |
|---------|--------------|----------|
| `.env` | Ajouter `API_KEY` | C9 |
| `requirements.txt` | Ajouter `prometheus-fastapi-instrumentator`, `prometheus-client` | C11 |
| `app/main.py` | Instrumenter Prometheus, doc Swagger auth | C9, C11 |
| `app/routes/predict_routes.py` | Ajouter `Depends(verify_api_key)` | C9 |
| `app/services/predict_service.py` | Ajouter métriques LLMOps | C11 |
| `app/services/synthesizer.py` | Tracker tokens et latence LLM | C11 |
| `app/database/vector_store.py` | Tracker latence embeddings | C11 |
| `.github/workflows/deploy.yml` | Ajouter job `test` avant déploiement | C13 |

### Côté Django (optionnel mais recommandé)

| Fichier | Description |
|---------|-------------|
| `services/booksync_api.py` | Service pour appeler l'API BookSync avec API Key |
| `settings.py` | Ajouter `BOOKSYNC_API_URL` et `BOOKSYNC_API_KEY` |

---

## Checklist finale

- [ ] **1. Authentification API**
  - [ ] Créer `app/middleware/auth.py`
  - [ ] Modifier les routes
  - [ ] Ajouter `API_KEY` dans `.env`
  - [ ] Tester avec curl

- [ ] **2. Tests à 80%**
  - [ ] Créer `tests/conftest.py`
  - [ ] Créer tests routes
  - [ ] Créer tests modèles
  - [ ] Créer tests middleware
  - [ ] Créer tests services
  - [ ] Vérifier couverture >= 80%

- [ ] **3. Tests dans CI/CD**
  - [ ] Modifier `deploy.yml`
  - [ ] Créer `test.yml` pour PR
  - [ ] Vérifier pipeline sur GitHub

- [ ] **4. Dashboard monitoring**
  - [ ] Ajouter prometheus-fastapi-instrumentator
  - [ ] Créer métriques custom
  - [ ] Créer docker-compose monitoring
  - [ ] Configurer Prometheus
  - [ ] Configurer Grafana
  - [ ] Tester le dashboard

---

*Document créé le 18 janvier 2026*
*Projet : BookSync API Agent - Certification BC3*
