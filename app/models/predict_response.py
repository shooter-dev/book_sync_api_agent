from pydantic import BaseModel
from typing import List, Optional


class PredictResponse(BaseModel):
    """Modèle pour la réponse de prédiction/recherche."""
    
    answer: str
    thought_process: List[str]
    enough_context: bool
    sources_count: int
    avg_similarity: Optional[float] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "Dans le volume 1 de 008 Apprenti espion, nous suivons les aventures de...",
                "thought_process": [
                    "Recherche effectuée avec 3 résultats",
                    "Similarité moyenne: 0.854",
                    "Contexte suffisant pour répondre"
                ],
                "enough_context": True,
                "sources_count": 3,
                "avg_similarity": 0.854
            }
        }