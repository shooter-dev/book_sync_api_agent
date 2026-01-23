from fastapi import APIRouter, HTTPException, Request, Depends
from app.models.predict_request import PredictRequest
from app.models.predict_response import PredictResponse
from app.services.predict_service import PredictService
from app.middleware.auth import verify_api_key

router = APIRouter(prefix="/predict", tags=["prediction"])

# Instance du service (initialisée de manière paresseuse pour éviter les problèmes de tests)
_predict_service = None


def get_predict_service():
    """
    Retourne l'instance du service de prédiction.
    Utilise une initialisation paresseuse pour éviter les problèmes
    lors des tests unitaires.
    """
    global _predict_service
    if _predict_service is None:
        _predict_service = PredictService()
    return _predict_service


@router.post("/test", dependencies=[Depends(verify_api_key)])
async def predict_test(request: dict):
    """
    Endpoint de test pour le débogage et la validation des données.

    Permet de vérifier la structure et les types de données envoyés par le client.
    Utile pendant le développement pour s'assurer que les requêtes sont correctement formatées.

    Args:
        request (dict): Dictionnaire contenant les données de test à valider

    Returns:
        dict: Statut de la requête, données reçues et types de chaque champ
    """
    return {"status": "ok", "received": request, "types": {k: str(type(v)) for k, v in request.items()}}


@router.post("/raw", response_model=PredictResponse, dependencies=[Depends(verify_api_key)])
async def predict_raw(request: Request):
    """
    Endpoint de test acceptant du JSON brut sans validation de schéma.

    Cet endpoint permet d'envoyer des données JSON directement sans passer par
    la validation Pydantic. Utile pour tester des formats de données personnalisés
    ou pour le débogage lorsque le schéma PredictRequest n'est pas adapté.

    Args:
        request (Request): Objet Request FastAPI contenant le JSON brut

    Returns:
        PredictResponse: Réponse de test formatée avec les informations de base

    Raises:
        HTTPException: Erreur 500 si le JSON ne peut être parsé ou traité
    """
    try:
        import json

        body = await request.body()
        data = json.loads(body)

        return PredictResponse(
            answer=f"Test réussi avec JSON brut! Collection: {list(data.get('collection', {}).keys())}",
            thought_process=["JSON brut reçu", f"User: {data.get('user_age')}"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@router.post("/", response_model=PredictResponse, dependencies=[Depends(verify_api_key)])
async def predict(
    request: PredictRequest,
    predict_service: PredictService = Depends(get_predict_service)
):
    """
    Endpoint principal pour les predictions et recommandations personnalisees.

    Cette route est le coeur du systeme de recommandation. Elle analyse le profil utilisateur
    (age, genre, preferences, humeur, collection personnelle) pour generer des recommandations
    intelligentes de mangas et de livres en utilisant:
    - La recherche vectorielle pour trouver des contenus similaires
    - L'IA (OpenAI/Azure) pour personnaliser les reponses
    - L'analyse de la collection existante de l'utilisateur

    Le processus inclut:
    1. Validation des donnees utilisateur via Pydantic
    2. Recherche vectorielle dans la base de donnees Timescale Vector
    3. Generation de recommandations personnalisees par IA
    4. Formatage de la reponse avec details et sources

    Args:
        request (PredictRequest): Objet contenant le profil complet de l'utilisateur
            - user_age: Age de l'utilisateur pour adapter les recommandations
            - user_genre: Genre pour la personnalisation
            - preferences: Preferences de lecture et centres d'interet
            - mood: Humeur actuelle pour les recommandations contextuelles
            - collection: Collection personnelle avec notes et commentaires
        predict_service (PredictService): Service de prediction injecte via Depends

    Returns:
        PredictResponse: Reponse structuree contenant:
            - serie_recomendees: Liste des recommandations detaillees
            - answer: Reponse textuelle generee par IA
            - thought_process: Detail du raisonnement de l'IA
            - enough_context: Indicateur de suffisance d'information
            - sources_count: Nombre de sources utilisees
            - avg_similarity: Score de similarite moyen

    Raises:
        HTTPException: Erreur 500 en cas de probleme lors du traitement de la prediction
    """
    try:
        response = await predict_service.predict(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la prédiction: {str(e)}")


@router.get("/health")
async def health_check():
    """
    Endpoint de surveillance de l'état de santé du service de prédiction.

    Utilisé pour le monitoring et le diagnostic du système. Cet endpoint
    permet de vérifier rapidement si le service de prédiction est opérationnel
    sans effectuer de traitement complexe.

    Returns:
        dict: Statut de santé du service
            - status: "healthy" si le service fonctionne correctement
            - service: Nom du service vérifié ("predict")

    Usage:
        GET /predict/health
        Réponse typique: {"status": "healthy", "service": "predict"}

    Monitoring:
        - Intégrer avec des systèmes de monitoring pour les alertes
        - Vérifier la disponibilité avant d'autres opérations
        - Utiliser dans les load balancers pour health checks
    """
    return {"status": "healthy", "service": "predict"}
