from fastapi import APIRouter, HTTPException, Request
from app.services.predict_service import PredictService
from app.models.predict_request import PredictRequest
from app.models.predict_response import PredictResponse

router = APIRouter(
    prefix="/predict",
    tags=["prediction"]
)

predict_service = PredictService()


@router.post("/test")
async def predict_test(request: dict):
    """Test endpoint pour débugger"""
    return {"status": "ok", "received": request, "types": {k: str(type(v)) for k, v in request.items()}}

@router.post("/raw", response_model=PredictResponse)
async def predict_raw(request: Request):
    """Test avec JSON brut"""
    try:
        import json
        body = await request.body()
        data = json.loads(body)
        
        return PredictResponse(
            answer=f"Test réussi avec JSON brut! Collection: {list(data.get('collection', {}).keys())}",
            thought_process=["JSON brut reçu", f"User: {data.get('user_age')}"],
            enough_context=True,
            sources_count=0,
            avg_similarity=None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@router.post("/", response_model=PredictResponse)
async def predict(request: PredictRequest):
    """
    Endpoint pour effectuer des prédictions et recommandations personnalisées.
    
    Cette route utilise le profil utilisateur pour générer des recommandations
    intelligentes ou répondre à des questions spécifiques sur les mangas/livres.
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