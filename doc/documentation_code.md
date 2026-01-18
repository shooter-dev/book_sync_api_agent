# Documentation du Code - Book Sync API Agent

## Table des matières
1. [Vue d'ensemble du projet](#vue-densemble-du-projet)
2. [Architecture de l'application](#architecture-de-lapplication)
3. [Modèles de données](#modèles-de-données)
4. [Services](#services)
5. [Routes API](#routes-api)
6. [Configuration](#configuration)

## Vue d'ensemble du projet

Le **Book Sync API Agent** est une API FastAPI conçue pour fournir des recommandations personnalisées de mangas et de livres. Le système utilise une combinaison de recherche vectorielle et d'intelligence artificielle (OpenAI/Azure) pour analyser le profil utilisateur et générer des recommandations intelligentes.

### Technologies principales
- **FastAPI**: Framework web pour les APIs REST
- **PostgreSQL + Timescale Vector**: Base de données avec support vectoriel
- **OpenAI/Azure OpenAI**: Génération de réponses personnalisées
- **Pydantic**: Validation et sérialisation des données
- **Instructor**: Intégration avec les modèles d'IA

## Architecture de l'application

### Structure du projet
```
app/
├── main.py                 # Point d'entrée FastAPI
├── models/                 # Modèles de données Pydantic
│   ├── predict_request.py  # Requête de prédiction
│   └── predict_response.py # Réponse de prédiction
├── routes/                 # Routes API
│   └── predict_routes.py   # Routes de prédiction
└── services/               # Logique métier
    └── predict_service.py  # Service de prédiction
```

### Flux de données
1. **Réception** de la requête utilisateur via les routes FastAPI
2. **Validation** des données avec les modèles Pydantic
3. **Traitement** par le service de prédiction
4. **Recherche vectorielle** dans la base de données
5. **Génération** de recommandations par IA
6. **Retour** de la réponse structurée

## Modèles de données

### PredictRequest (`app/models/predict_request.py`)

Modèle Pydantic définissant la structure des requêtes de prédiction.

#### Champs
- `user_age`: Âge de l'utilisateur (int) - Permet d'adapter les recommandations selon l'âge
- `user_genre`: Genre de l'utilisateur (str) - Pour la personnalisation des réponses
- `preferences`: Préférences de lecture (str) - Centres d'intérêt et goûts littéraires
- `mood`: Humeur actuelle (str) - Pour des recommandations contextuelles
- `collection`: Collection personnelle (dict) - Mangas/livres possédés avec notes

#### Utilisation
```python
from app.models.predict_request import PredictRequest

request = PredictRequest(
    user_age=25,
    user_genre="féminin",
    preferences="fantasy, romance, aventure",
    mood="détendu",
    collection={"One Piece": {"rating": 5, "comment": "Excellent"}}
)
```

### PredictResponse (`app/models/predict_response.py`)

Modèle Pydantic définissant la structure des réponses de prédiction.

#### Champs
- `serie_recomendees`: Liste des séries recommandées (list)
- `answer`: Réponse textuelle générée par l'IA (str)
- `thought_process`: Détail du raisonnement de l'IA (list)
- `enough_context`: Indicateur de suffisance d'information (bool)
- `sources_count`: Nombre de sources utilisées (int)
- `avg_similarity`: Score de similarité moyen (float)

## Services

### PredictService (`app/services/predict_service.py`)

Classe principale contenant la logique métier pour les prédictions.

#### Méthodes principales
- `predict(request: PredictRequest) -> PredictResponse`:
  - Méthode principale orchestrant le processus de recommandation
  - Valide les données utilisateur
  - Appelle les différents composants (VectorStore, Synthesizer)
  - Génère la réponse finale

#### Flux de traitement
1. **Analyse** du profil utilisateur
2. **Extraction** des mots-clés et préférences
3. **Recherche** vectorielle dans la base de données
4. **Synthèse** des résultats par l'IA
5. **Formatage** de la réponse structurée

## Routes API

### `/predict/` (POST)
- **Description**: Endpoint principal pour les recommandations personnalisées
- **Corps**: `PredictRequest`
- **Retour**: `PredictResponse`
- **Utilisation**: Générer des recommandations basées sur le profil utilisateur

### `/predict/test` (POST)
- **Description**: Endpoint de test pour le débogage
- **Corps**: dict
- **Retour**: dict avec statut et types de données
- **Utilisation**: Valider le format des requêtes pendant le développement

### `/predict/raw` (POST)
- **Description**: Endpoint acceptant du JSON brut sans validation
- **Corps**: JSON brut
- **Retour**: `PredictResponse` de test
- **Utilisation**: Tester des formats personnalisés ou débogage

### `/predict/health` (GET)
- **Description**: Vérification de santé du service
- **Retour**: dict avec statut "healthy"
- **Utilisation**: Monitoring et diagnostic du système

## Configuration

### Variables d'environnement (`.env`)

#### Configuration Azure OpenAI
```
AZURE_OPENAI_ENDPOINT=https://app-booksync.openai.azure.com/
AZURE_OPENAI_KEY=votre_clé_api
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-large
USE_AZURE_OPENAI=true
```

#### Configuration base de données
```
TIMESCALE_SERVICE_URL=postgres://user:password@host:5432/database
DB_NAME=booksync
DB_USER=booksyncadmin
DB_PASSWORD=votre_mot_de_passe
DB_HOST=bdd-booksync.postgres.database.azure.com
DB_PORT=5432
```

### Dépendances principales (requirements.txt)
- `fastapi[standard]`: Framework web avec support uvicorn
- `pydantic`: Validation et sérialisation
- `openai`: Client OpenAI pour les appels API
- `anthropic`: Alternative OpenAI (Anthropic Claude)
- `psycopg`: Driver PostgreSQL
- `timescale-vector`: Extension PostgreSQL pour les vecteurs
- `instructor`: Simplification des appels aux modèles d'IA
- `python-dotenv`: Gestion des variables d'environnement

## Guide d'utilisation

### Démarrage du serveur
```bash
# Activation de l'environnement virtuel
source venv/Scripts/activate  # Windows
source venv/bin/activate      # Linux/Mac

# Démarrage du serveur
uvicorn app.main:app --reload --port 8001
```

### Exemple d'appel API
```bash
curl -X POST "http://localhost:8001/predict/" \
  -H "Content-Type: application/json" \
  -d '{
    "user_age": 25,
    "user_genre": "féminin",
    "preferences": "fantasy, romance, aventure",
    "mood": "détendu",
    "collection": {
      "One Piece": {"rating": 5, "comment": "Excellent"},
      "Naruto": {"rating": 4, "comment": "Bon début"}
    }
  }'
```

### Bonnes pratiques
1. **Validation**: Toujours valider les requêtes avec les modèles Pydantic
2. **Gestion d'erreurs**: Utiliser les try/catch et retourner des HTTPException appropriées
3. **Documentation**: Maintenir les docstrings à jour pour toutes les fonctions
4. **Monitoring**: Utiliser l'endpoint `/health` pour vérifier l'état du service
5. **Sécurité**: Ne jamais exposer les clés API dans le code (utiliser les variables d'environnement)

## Architecture technique détaillée

### VectorStore
Composant responsable de la recherche vectorielle dans TimescaleDB:
- **Embeddings**: Transformation du texte en vecteurs numériques
- **Similarité**: Calcul des scores de similarité cosinus
- **Indexation**: Recherche efficace dans les espaces vectoriels

### Synthesizer
Composant de génération de réponses par IA:
- **Prompt engineering**: Construction des requêtes optimales
- **Context management**: Gestion du contexte pour les réponses cohérentes
- **Response formatting**: Mise en forme des réponses structurées

### Pipeline de traitement
1. **Input validation** → Vérification des données utilisateur
2. **Feature extraction** → Extraction des caractéristiques importantes
3. **Vector search** → Recherche des contenus similaires
4. **AI synthesis** → Génération de recommandations personnalisées
5. **Output formatting** → Formatage de la réponse finale

Cette documentation couvre les aspects principaux du code. Pour plus de détails sur des implémentations spécifiques, consultez les fichiers source correspondants.