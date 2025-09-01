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
