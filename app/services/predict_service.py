import logging
from typing import Optional, Dict, Any

from app.database.vector_store import VectorStore
from app.services.synthesizer import Synthesizer
from app.models.predict_request import PredictRequest
from app.models.predict_response import PredictResponse


class PredictService:
    """Service pour gérer les prédictions basées sur la recherche vectorielle."""
    
    def __init__(self):
        self.vector_store = VectorStore()
        self.synthesizer = Synthesizer()
    
    async def predict(self, request: PredictRequest) -> PredictResponse:
        """
        Effectue une prédiction basée sur la question de l'utilisateur.
        
        Args:
            request: La requête de prédiction contenant la question et les paramètres
            
        Returns:
            PredictResponse: La réponse synthétisée avec les métadonnées
        """
        try:
            # Effectuer la recherche vectorielle
            search_results = self.vector_store.search(
                query_text=request.question,
                limit=request.limit,
                metadata_filter=request.metadata_filter,
                return_dataframe=True
            )
            
            # Générer la réponse synthétisée
            synthesizer_response = self.synthesizer.generate_response(
                question=request.question,
                context=search_results
            )
            
            # Calculer les métadonnées
            sources_count = len(search_results) if not search_results.empty else 0
            avg_similarity = (
                search_results['similarity'].mean() 
                if not search_results.empty and 'similarity' in search_results.columns 
                else None
            )
            
            # Construire la réponse finale
            return PredictResponse(
                answer=synthesizer_response.answer,
                thought_process=synthesizer_response.thought_process,
                enough_context=synthesizer_response.enough_context,
                sources_count=sources_count,
                avg_similarity=avg_similarity
            )
            
        except Exception as e:
            logging.error(f"Erreur lors de la prédiction: {e}")
            return PredictResponse(
                answer="Une erreur s'est produite lors du traitement de votre demande.",
                thought_process=[f"Erreur: {str(e)}"],
                enough_context=False,
                sources_count=0,
                avg_similarity=None
            )