from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class PredictRequest(BaseModel):
    """Modèle pour la requête de prédiction/recherche."""
    
    question: str = Field(..., description="La question de l'utilisateur", min_length=1)
    limit: Optional[int] = Field(5, description="Nombre maximum de résultats à retourner", ge=1, le=20)
    metadata_filter: Optional[Dict[str, Any]] = Field(None, description="Filtres de métadonnées")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "Que se passe-t-il dans le volume 1 de 008 Apprenti espion?",
                "limit": 5,
                "metadata_filter": {"serie_title": "008 Apprenti espion"}
            }
        }