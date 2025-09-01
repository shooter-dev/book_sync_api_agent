# 📚 Book Sync API

API pour la synchronisation de livres avec recherche vectorielle et prédictions IA.

## 🚀 Installation

### Prérequis
- Python 3.13+
- Node.js (pour ccusage)

### Setup
```bash
# Cloner le repository
git clone [repository-url]
cd api

# Activer l'environnement virtuel
source .venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

## 🏃‍♂️ Lancement de l'API

```bash
# Démarrer le serveur
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# L'API sera accessible sur: http://localhost:8000
# Documentation Swagger: http://localhost:8000/docs
```

## 🧪 Tests

### Lancement des Tests

#### Script Principal (Recommandé)
```bash
# Tous les tests avec rapports complets
./run_tests.sh

# Tests par type
./run_tests.sh --unit          # Tests unitaires seulement
./run_tests.sh --integration   # Tests d'intégration seulement
./run_tests.sh --api          # Tests API seulement

# Options utiles
./run_tests.sh --clean --open  # Nettoie et ouvre les rapports
./run_tests.sh --no-html       # Pas de rapports HTML
./run_tests.sh --verbose       # Sortie détaillée
```

#### Commandes pytest Directes
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

### 📊 Rapports de Tests

Après exécution des tests, les rapports suivants sont générés :

#### 1. **Coverage HTML** (Couverture de Code)
- **Fichier** : `htmlcov/index.html`
- **Contenu** : Couverture détaillée par fichier avec lignes non testées
- **Ouverture** : Double-clic ou `open htmlcov/index.html`

#### 2. **Test Report HTML** (Résultats des Tests)
- **Fichier** : `tests/reports/report.html`
- **Contenu** : Résultats détaillés, temps d'exécution, logs d'erreur
- **Ouverture** : Double-clic ou `open tests/reports/report.html`

#### 3. **Coverage XML** 
- **Fichier** : `coverage.xml`
- **Usage** : Intégration CI/CD, outils externes

#### 4. **Documentation Tests**
- **Fichier** : `TESTS.md`
- **Contenu** : Guide complet des tests avec exemples
- **Format** : Markdown avec navigation

### 🎯 Marqueurs de Tests

Les tests sont organisés par marqueurs :

```python
@pytest.mark.unit         # Tests unitaires
@pytest.mark.integration  # Tests d'intégration  
@pytest.mark.api          # Tests d'endpoints API
@pytest.mark.slow         # Tests longs
```

### 📈 Métriques de Couverture

- **Couverture actuelle** : 39%
- **Objectif minimum** : 80%
- **Objectif recommandé** : 90%+

## 📋 Accès aux Rapports

### Dans votre App/Finder :
1. Naviguez vers : `Cours → projet_fil_rouge → api`
2. Ouvrez les fichiers :
   - `htmlcov/index.html` → Couverture de code
   - `tests/reports/report.html` → Résultats des tests
   - `TESTS.md` → Documentation complète

### Ouverture Automatique :
```bash
# Ouvre automatiquement les rapports après les tests
./run_tests.sh --open

# Ou manuellement
open htmlcov/index.html
open tests/reports/report.html
```

## 🔧 Configuration

- **pytest.ini** : Configuration des tests
- **requirements.txt** : Dépendances (avec pytest, pytest-cov, pytest-html)
- **.gitignore** : Exclut les rapports générés du versioning

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

## 🛠️ Développement

### Structure du Projet
```
api/
├── app/                    # Code source
│   ├── routes/            # Endpoints API
│   ├── services/          # Logique métier
│   ├── models/            # Modèles Pydantic
│   └── config/            # Configuration
├── tests/                 # Tests
├── htmlcov/              # Rapports de couverture
├── tests/reports/        # Rapports de tests
└── TESTS.md              # Documentation des tests
```

### Commandes Utiles
```bash
# Lancer l'API
python -m uvicorn app.main:app --reload

# Tests complets
./run_tests.sh --clean --open

# Vérification ccusage
npx ccusage@latest

# Aide sur les tests
./run_tests.sh --help
```

## 📖 Documentation

- **TESTS.md** : Guide complet des tests
- **Swagger UI** : http://localhost:8000/docs (quand l'API tourne)
- **Rapports HTML** : Générés automatiquement après les tests
=======
# API Agent – BookSync

## Objectif

Ce projet expose une API FastAPI qui sert de point d’entrée pour un agent intelligent capable de recommander des œuvres littéraires personnalisées. L’agent s’appuie sur :

- Le profil utilisateur premium  
- L’historique de lecture  
- La collection d’œuvres possédées mais non lues  
- Un questionnaire a remplir

![questionnaire](images/questionnaire.png)
---

## Rôle de FastAPI

FastAPI agit comme **interface entre les données utilisateur et le moteur de recommandation IA**. Elle reçoit les informations via un endpoint `/predict/`, les valide avec Pydantic, les structure, puis les transmet à l’agent IA pour générer une prédiction.

---

Installation & Démarrage
Prérequis
Assure-toi d’avoir installé :

* Python 3.10 ou plus

* pip ou poetry

* Git

* Un environnement virtuel (recommandé)

## installation du démarrage

# Clone du dépôt
git clone https://github.com/shooter-dev/book_sync_api_agent.git
cd book_sync_api_agent

# Création d’un environnement virtuel
python -m venv venv
source venv/bin/activate  # Sur Windows : venv\Scripts\activate

# Installation des dépendances
pip install -r requirements.txt

---

## Configuration des variables d’environnement
Crée un fichier .env à la racine du projet :
```console
URL_API_PREDICTION=http://127.0.0.1:8001/predict/
DATABASE_URL=postgresql://user:password@localhost:5432/booksync
```
---
## Démarrage du serveur FastAPI

```console
uvicorn app.main:app --reload --port 8001
```
* Le serveur démarre sur http://127.0.0.1:8001

* Les endpoints sont disponibles via Swagger : http://127.0.0.1:8001/docs

![api_doc](images/api_doc.png)
---
## Données attendues

L’API reçoit un payload JSON contenant :
```console
- `user_age`, `user_genre` : données démographiques  
- `genre_preference`, `category_preference` : préférences déclarées  
- `user_comment` : remarques libres  
- `prediction_type` : type de recommandation souhaitée (`collection` ou `proposition`)  
- `collection` : œuvres possédées (volumes + ID de série)  
- `read` : œuvres déjà lues  
- *(optionnel)* `user_mood` : humeur du moment  
```
---

## 🧪 Exemple de payload JSON

```json
{
  "user_age": 35,
  "user_genre": "Homme",
  "genre_preference": ["Manga", "Manhwa"],
  "category_preference": ["Seinen", "Action", "Romance"],
  "user_comment": "je veux rigoler",
  "prediction_type": "proposition",
  "user_mood": "Comique",
  "collection": {
    "Prison School": {
      "volumes": {
        "4": "c606eeda-6d05-45d7-9184-0a0514182259",
        "3": "576711ba-3134-46b2-985b-1dcaa2fc9beb",
        "2": "05f35d2a-aac7-4f13-a18e-158e9142472a",
        "1": "3eb05a53-273b-438d-ab7b-4fbdb7cddb59"
      },
      "id_series": "346bd876-64cd-43e1-b11b-e876a67949bd"
    },
    "Raw Hero": {
      "volumes": {
        "3": "4ec0fa9d-f194-4c98-bb56-73129f2d41cf",
        "2": "038c7a25-90e9-430f-90a8-b518b2ab7308",
        "1": "e11f446e-f8cb-4a3a-b2ae-30d1c3d66d46"
      },
      "id_series": "e26e24bd-7dd3-4e42-837f-db32ec4a819a"
    }
  },
  "read": {
    "Raw Hero": {
      "volumes": {
        "2": "038c7a25-90e9-430f-90a8-b518b2ab7308",
        "1": "e11f446e-f8cb-4a3a-b2ae-30d1c3d66d46"
      },
      "id_series": "e26e24bd-7dd3-4e42-837f-db32ec4a819a"
    }
  }
} 
```

## Lancement des tests unitaires :

  Tests

  Lancement des Tests

  Script Principal (Recommandé)

  # Tous les tests avec rapports complets
  ./run_tests.sh

  # Tests par type
  ./run_tests.sh --unit          # Tests unitaires seulement
  ./run_tests.sh --integration   # Tests d'intégration seulement
  ./run_tests.sh --api          # Tests API seulement

  # Options utiles
  ./run_tests.sh --clean --open  # Nettoie et ouvre les rapports
  ./run_tests.sh --no-html       # Pas de rapports HTML
  ./run_tests.sh --verbose       # Sortie détaillée

  Commandes pytest Directes

  # Tests basiques
  pytest

  # Tests avec couverture
  pytest --cov=app --cov-report=html

  # Tests par marqueur
  pytest -m unit
  pytest -m integration
  pytest -m api

  Rapports de Tests

  Après exécution des tests, les rapports suivants sont générés :

  1. Coverage HTML (Couverture de Code)

  - Fichier : htmlcov/index.html
  - Contenu : Couverture détaillée par fichier avec lignes non testées
  - Ouverture : Double-clic ou open htmlcov/index.html

  2. Test Report HTML (Résultats des Tests)

  - Fichier : tests/reports/report.html
  - Contenu : Résultats détaillés, temps d'exécution, logs d'erreur
  - Ouverture : Double-clic ou open tests/reports/report.html

  3. Coverage XML

  - Fichier : coverage.xml
  - Usage : Intégration CI/CD, outils externes

  4. Documentation Tests

  - Fichier : TESTS.md
  - Contenu : Guide complet des tests avec exemples
  - Format : Markdown avec navigation

  Marqueurs de Tests

  Les tests sont organisés par marqueurs :

  @pytest.mark.unit         # Tests unitaires
  @pytest.mark.integration  # Tests d'intégration  
  @pytest.mark.api          # Tests d'endpoints API
  @pytest.mark.slow         # Tests longs

  Métriques de Couverture

  - Couverture actuelle : 39%
  - Objectif minimum : 80%
  - Objectif recommandé : 90%+

  Accès aux Rapports

  Dans votre App/Finder :

  1. Naviguez vers : Cours → projet_fil_rouge → api
  2. Ouvrez les fichiers :
    - htmlcov/index.html → Couverture de code
    - tests/reports/report.html → Résultats des tests
    - TESTS.md → Documentation complète

  Ouverture Automatique :

  # Ouvre automatiquement les rapports après les tests
  ./run_tests.sh --open

  # Ou manuellement
  open htmlcov/index.html
  open tests/reports/report.html

  🔧 Configuration

  - pytest.ini : Configuration des tests
  - requirements.txt : Dépendances (avec pytest, pytest-cov, pytest-html)
  - .gitignore : Exclut les rapports générés du versioning

  Surveillance des Coûts IA

  ccusage (Monitoring Claude Code)

  # Rapport quotidien
  npx ccusage@latest daily

  # Rapport mensuel  
  npx ccusage@latest monthly

  # Surveillance en temps réel
  npx ccusage@latest blocks --live

  # Alertes vocales (macOS)
  ./voice_alerts.sh fini      # Alerte tokens épuisés
  ./voice_alerts.sh check     # Vérification automatique

  🛠️ Développement

  Structure du Projet

  api/
  ├── app/                    # Code source
  │   ├── routes/            # Endpoints API
  │   ├── services/          # Logique métier
  │   ├── models/            # Modèles Pydantic
  │   └── config/            # Configuration
  ├── tests/                 # Tests
  ├── htmlcov/              # Rapports de couverture
  ├── tests/reports/        # Rapports de tests
  └── TESTS.md              # Documentation des tests

  Commandes Utiles

  # Lancer l'API
  python -m uvicorn app.main:app --reload

  # Tests complets
  ./run_tests.sh --clean --open

  # Vérification ccusage
  npx ccusage@latest

  # Aide sur les tests
  ./run_tests.sh --help

  Documentation

  - TESTS.md : Guide complet des tests
  - Rapports HTML : Générés automatiquement après les tests



