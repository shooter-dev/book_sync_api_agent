from pydantic import BaseModel
from typing import List, Optional


class RecommendedSeries(BaseModel):
    """Modèle pour une série recommandée."""
    title: str
    genre: Optional[str] = None
    category: Optional[str] = None
    similarity_score: Optional[float] = None
    reason: Optional[str] = None


class PredictResponse(BaseModel):
    """Modèle pour la réponse de prédiction/recherche."""
    
    answer: str
    thought_process: List[str]
    enough_context: bool
    sources_count: int
    recommended_series: List[RecommendedSeries] = []
    avg_similarity: Optional[float] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "Basé sur votre profil et vos préférences, voici mes recommandations...",
                "thought_process": [
                    "Profil: Homme de 33 ans",
                    "Préférences: Global Manga - Action",
                    "Recherche effectuée avec 3 résultats",
                    "Similarité moyenne: 0.854"
                ],
                "enough_context": True,
                "sources_count": 3,
                "recommended_series": [
                    {
                        "title": "Attack on Titan",
                        "genre": "Action",
                        "category": "Seinen",
                        "similarity_score": 0.89,
                        "reason": "Correspond à vos préférences d'action avec un style mature"
                    }
                ],
                "avg_similarity": 0.854
            }
        }