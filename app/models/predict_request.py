from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal, Union



class PredictRequest(BaseModel):
    """Modèle pour la requête de prédiction/recherche."""
    
    user_age: str = Field(..., description="Âge de l'utilisateur")
    user_genre: str = Field(..., description="Genre de l'utilisateur")
    genre_preference: str = Field(..., description="Préférence de genre (ex: Global Manga)")
    category_preference: str = Field(..., description="Préférence de catégorie (ex: Action)")
    user_comment: str = Field("", description="Commentaires de l'utilisateur")
    prediction_type: Literal["collection", "recommendation"] = Field(..., description="Type de prédiction demandée")
    collection: Optional[Union[Dict[str, Any], str]] = Field(None, description="Collection de l'utilisateur")
    read: Optional[Union[Dict[str, Any], str]] = Field(None, description="Volumes lus par l'utilisateur")
    user_mood: str = Field(..., description="Humeur/état d'esprit de l'utilisateur")
    
    # Anciens champs optionnels pour compatibilité
    question: Optional[str] = Field(None, description="Question spécifique de l'utilisateur")
    limit: Optional[int] = Field(5, description="Nombre maximum de résultats à retourner", ge=1, le=20)
    metadata_filter: Optional[Dict[str, Any]] = Field(None, description="Filtres de métadonnées")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_age": "33",
                "user_genre": "Homme",
                "genre_preference": "Global Manga",
                "category_preference": "Action",
                "user_comment": "",
                "prediction_type": "collection",
                "collection": {
                    "Hunter X Hunter": {
                        "volumes": {
                            "4": "10150f42-3336-41d8-9243-68a95336d0a5",
                            "3": "63462427-e172-4642-b26d-efc70731bd29",
                            "2": "d599cf3b-35ac-4805-be09-f0323e03307a",
                            "1": "dfc2c186-6eca-47c8-84b2-cad1b99f1275"
                        },
                        "id_series": "a2e0ddcf-71c6-406c-aadc-ccbac2d3f668"
                    },
                    "Ash & Eli": {
                        "volumes": {
                            "1": "9ed92b95-8042-4f99-ad24-b2321b4bf351"
                        },
                        "id_series": "796e3ab1-ac95-40a6-9419-138d6f9c6cb1"
                    }
                },
                "read": {
                    "Hunter X Hunter": {
                        "volumes": {
                            "3": "63462427-e172-4642-b26d-efc70731bd29",
                            "2": "d599cf3b-35ac-4805-be09-f0323e03307a",
                            "1": "dfc2c186-6eca-47c8-84b2-cad1b99f1275"
                        },
                        "id_series": "a2e0ddcf-71c6-406c-aadc-ccbac2d3f668"
                    },
                    "One Piece": {
                        "volumes": {
                            "1": "ad4493ad-1310-404b-ace2-91f3dd4f489a"
                        },
                        "id_series": "a02cf154-af6c-4f08-9a7a-32f7bc229ac8"
                    },
                    "The Eminence in Shadow": {
                        "volumes": {
                            "5": "5cfb1581-e895-4326-98cf-bcfa3c772d36"
                        },
                        "id_series": "8d557b7b-b4a9-449f-b081-51362e80b5f9"
                    }
                },
                "user_mood": "Comique"
            }
        }