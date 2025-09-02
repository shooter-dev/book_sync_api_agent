# 📚 BookSync API Agent

API FastAPI intelligente pour la recommandation personnalisée de mangas et livres basée sur les profils utilisateurs et la recherche vectorielle.

## 🎯 Objectif

Cette API sert de point d'entrée pour un agent IA capable de recommander des œuvres littéraires personnalisées en s'appuyant sur :

- Le profil utilisateur (âge, genre, préférences)
- L'historique de lecture
- La collection d'œuvres possédées mais non lues
- L'humeur actuelle de l'utilisateur
- Un système de recherche vectorielle avec embeddings

![Questionnaire](docs/images/questionnaire.png)

## 🚀 Installation

### Prérequis
- Python 3.10+
- PostgreSQL (pour la base de données vectorielle)
- OpenAI API Key ou Azure OpenAI
- Git

### Setup

```bash
# Cloner le repository
git clone https://github.com/shooter-dev/book_sync_api_agent.git
cd book_sync_api_agent

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Sur Windows : venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt
```

### Configuration

Créer un fichier `.env` à la racine du projet :

```env
# Base de données PostgreSQL
DATABASE_URL=postgresql://user:password@localhost:5432/booksync

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_DEFAULT_MODEL=gpt-4
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=500

# Azure OpenAI (optionnel)
USE_AZURE_OPENAI=false
AZURE_OPENAI_API_KEY=your_azure_api_key
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_AZURE_ENDPOINT=https://your-endpoint.openai.azure.com
AZURE_OPENAI_DEFAULT_MODEL=gpt-4
```

## 🏃‍♂️ Lancement de l'API

```bash
# Démarrer le serveur
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# L'API sera accessible sur: http://localhost:8000
# Documentation Swagger: http://localhost:8000/docs
```

![API Documentation](docs/images/api_doc.png)

## 🔧 Fonctionnalités

### Endpoints Principaux

- **POST `/predict/`** : Recommandations personnalisées basées sur le profil
- **POST `/predict/test`** : Endpoint de test pour débugger
- **POST `/predict/raw`** : Test avec JSON brut
- **GET `/predict/health`** : Vérification de santé du service

### Système de Recommandation

L'agent utilise :
1. **Analyse du profil utilisateur** : âge, genre, préférences, humeur
2. **Recherche vectorielle** : similarité sémantique avec la base de données
3. **Filtrage intelligent** : évite les doublons avec la collection existante
4. **Personnalisation** : adaptation selon le type de prédiction demandée

## 📊 Exemple d'Utilisation

### Payload JSON

```json
{
  "user_age": "22",
  "user_genre": "Homme",
  "genre_preference": "Manga",
  "category_preference": "Romance",
  "user_comment": "je cherche quelque chose de léger",
  "prediction_type": "collection",
  "collection": {
    "Hunter X Hunter": {
      "volumes": {
        "4": "10150f42-3336-41d8-9243-68a95336d0a5",
        "3": "63462427-e172-4642-b26d-efc70731bd29"
      },
      "id_series": "a2e0ddcf-71c6-406c-aadc-ccbac2d3f668"
    }
  },
  "read": {
    "One Piece": {
      "volumes": {
        "1": "ad4493ad-1310-404b-ace2-91f3dd4f489a"
      },
      "id_series": "a02cf154-af6c-4f08-9a7a-32f7bc229ac8"
    }
  },
  "user_mood": "Énervé"
}
```

### Réponse Structurée

```json
{
  "answer": "Basé sur votre profil et vos préférences...",
  "thought_process": [
    "Profil: Homme de 22 ans",
    "Préférences: Manga - Romance",
    "Humeur: Énervé",
    "Question générée: Recommandez-moi des Manga dans la catégorie Romance.",
    "Recherche effectuée avec 5 résultats",
    "Similarité moyenne: 0.823",
    "Contexte suffisant pour répondre"
  ],
  "enough_context": true,
  "sources_count": 5,
  "recommended_series": [
    {
      "title": "Kaguya-sama: Love Is War",
      "genre": "Romance",
      "category": "Seinen",
      "similarity_score": 0.856,
      "reason": "Recommandé car correspond à votre préférence pour le Romance et style seinen dynamique"
    }
  ],
  "avg_similarity": 0.823
}
```

## 🧪 Tests

### Lancement des Tests

```bash
# Script principal (recommandé)
./run_tests.sh

# Tests par type
./run_tests.sh --unit          # Tests unitaires seulement
./run_tests.sh --integration   # Tests d'intégration seulement
./run_tests.sh --api          # Tests API seulement

# Options utiles
./run_tests.sh --clean --open  # Nettoie et ouvre les rapports
./run_tests.sh --verbose       # Sortie détaillée
```

### Commandes pytest Directes

```bash
# Tests basiques
pytest

# Tests avec couverture
pytest --cov=app --cov-report=html

# Tests par marqueur
pytest -m unit
pytest -m integration
pytest -m api
```

### Rapports Générés

- **`htmlcov/index.html`** : Couverture de code détaillée
- **`tests/reports/report.html`** : Résultats des tests
- **`coverage.xml`** : Couverture pour CI/CD
- **`TESTS.md`** : Documentation complète des tests

## 📊 Surveillance des Coûts IA

### ccusage (Monitoring Claude Code)

```bash
# Rapport quotidien
npx ccusage@latest daily

# Rapport mensuel  
npx ccusage@latest monthly

# Surveillance en temps réel
npx ccusage@latest blocks --live

# Alertes vocales (macOS)
./voice_alerts.sh fini      # Alerte tokens épuisés
./voice_alerts.sh check     # Vérification automatique
```

## 🏗️ Architecture

### Structure du Projet

```
book_sync_api_agent/
├── app/
│   ├── main.py                    # Point d'entrée FastAPI
│   ├── routes/
│   │   └── predict_routes.py      # Endpoints de prédiction
│   ├── services/
│   │   ├── predict_service.py     # Logique de prédiction
│   │   ├── synthesizer.py         # Agent IA de synthèse
│   │   └── similarity_search.py   # Recherche vectorielle
│   ├── models/
│   │   ├── predict_request.py     # Modèles de requête
│   │   └── predict_response.py    # Modèles de réponse
│   ├── database/
│   │   └── vector_store.py        # Interface base vectorielle
│   └── config/
│       └── settings.py            # Configuration
├── tests/                         # Tests automatisés
├── data/                          # Données d'entraînement
├── images/                        # Assets documentation
└── requirements.txt               # Dépendances Python
```

### Flux de Données

1. **Réception** : FastAPI reçoit le payload JSON via `/predict/`
2. **Validation** : Pydantic valide et structure les données
3. **Génération de Question** : Le service génère une question intelligente basée sur le profil
4. **Recherche Vectorielle** : Similarité sémantique dans la base de données
5. **Synthèse IA** : L'agent IA analyse le profil et génère des recommandations
6. **Formatage** : Réponse structurée avec métadonnées et recommandations

## 🛠️ Développement

### Commandes Utiles

```bash
# Lancer l'API en mode développement
uvicorn app.main:app --reload --port 8000

# Tests complets avec rapports
./run_tests.sh --clean --open

# Vérification de l'utilisation des tokens
npx ccusage@latest

# Linting et formatage du code
black app/
isort app/
flake8 app/
```

### Variables d'Environnement

- **`USE_AZURE_OPENAI`** : `true` pour utiliser Azure OpenAI, `false` pour OpenAI standard
- **`DATABASE_URL`** : URL de connexion PostgreSQL
- **`OPENAI_*`** : Configuration OpenAI
- **`AZURE_OPENAI_*`** : Configuration Azure OpenAI

## 📈 Métriques

- **Couverture de tests** : 39% (objectif : 80%+)
- **Performance** : < 2s par recommandation
- **Précision** : Basée sur la similarité vectorielle (seuil : 0.7)

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Commit les changements (`git commit -m 'Ajouter nouvelle fonctionnalité'`)
4. Push la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. Créer une Pull Request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 📞 Support

- **Documentation** : [Swagger UI](http://localhost:8000/docs) quand l'API est en cours d'exécution
- **Tests** : Voir `TESTS.md` pour la documentation complète des tests
- **Issues** : Utiliser GitHub Issues pour les bugs et demandes de fonctionnalités