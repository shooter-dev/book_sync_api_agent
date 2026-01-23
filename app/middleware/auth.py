"""
Module d'authentification par API Key.

Ce module gère la vérification des clés API pour sécuriser
les endpoints de l'API de recommandation.
"""

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
import os

# Configuration de l'en-tête pour la clé API
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_api_key():
    """
    Récupère la clé API depuis les variables d'environnement.

    Returns:
        str: La clé API configurée ou None si non définie
    """
    return os.getenv("API_KEY")


async def verify_api_key(api_key: str = Security(api_key_header)):
    """
    Vérifie que la clé API fournie est valide.

    Cette fonction est utilisée comme dépendance FastAPI pour protéger
    les endpoints. Elle compare la clé fournie dans l'en-tête X-API-Key
    avec la clé configurée dans les variables d'environnement.

    Args:
        api_key: La clé API fournie dans l'en-tête de la requête

    Returns:
        str: La clé API si elle est valide

    Raises:
        HTTPException: 401 si la clé est manquante ou invalide
    """
    expected_key = get_api_key()

    # Si aucune clé n'est configurée, on refuse l'accès
    if not expected_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API Key non configurée sur le serveur"
        )

    # Si aucune clé n'est fournie dans la requête
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API manquante. Ajoutez l'en-tête X-API-Key.",
            headers={"WWW-Authenticate": "ApiKey"}
        )

    # Si la clé ne correspond pas
    if api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API invalide",
            headers={"WWW-Authenticate": "ApiKey"}
        )

    return api_key
