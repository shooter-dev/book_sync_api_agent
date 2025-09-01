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