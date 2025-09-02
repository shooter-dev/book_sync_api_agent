from pydantic import BaseModel
from typing import List, Optional


class RecommendedSerie(BaseModel):
    """Modèle pour une série recommandée."""
    title: str
    id_series: str
    responce_IA: str


class PredictResponse(BaseModel):
    """Modèle pour la réponse de prédiction au format demandé."""
    
    serie_recomendees: List[RecommendedSerie]
    status: str
    responce_IA_global: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "serie_recomendees": [
                    {
                        "title": "Kaguya-sama: Love Is War",
                        "id_series": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                        "responce_IA": "Parfait pour vos goûts romance avec beaucoup d'humour"
                    },
                    {
                        "title": "Toradora!",
                        "id_series": "f1e2d3c4-b5a6-9870-5432-1098765fedcba",
                        "responce_IA": "Romance moderne avec des personnages attachants"
                    }
                ],
                "status": "success",
                "responce_IA_global": "Voici mes recommandations basées sur votre profil et vos préférences romance"
            }
        }