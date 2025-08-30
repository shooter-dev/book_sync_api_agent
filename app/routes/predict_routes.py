from fastapi import APIRouter, HTTPException
from app.services.predict_service import PredictService
from app.models.predict_request import PredictRequest
from app.models.predict_response import PredictResponse

router = APIRouter(
    prefix="/predict",
    tags=["prediction"]
)

predict_service = PredictService()


@router.post("/", response_model=PredictResponse)
async def predict(request: PredictRequest):
    """
    Endpoint pour effectuer des prédictions basées sur la recherche vectorielle.
    
    Cette route permet de poser des questions sur le contenu des mangas/livres
    et obtenir des réponses basées sur les données vectorisées en base.
    
    Args:
        request: La requête contenant la question et les paramètres de recherche
        
    Returns:
        PredictResponse: La réponse synthétisée avec les métadonnées
        
    Example:
        ```json
        {
            "question": "Que se passe-t-il dans le volume 1 de 008 Apprenti espion?",
            "limit": 5,
            "metadata_filter": {"serie_title": "008 Apprenti espion"}
        }
        ```
    """
    try:
        response = await predict_service.predict(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la prédiction: {str(e)}")


@router.get("/health")
async def health_check():
    """
    Endpoint de vérification de santé pour le service de prédiction.
    """
    return {"status": "healthy", "service": "predict"}