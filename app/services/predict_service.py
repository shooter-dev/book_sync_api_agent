import logging
from typing import Optional, Dict, Any, List

from app.database.vector_store import VectorStore
from app.services.synthesizer import Synthesizer
from app.models.predict_request import PredictRequest
from app.models.predict_response import PredictResponse, RecommendedSeries


class PredictService:
    """Service pour gérer les prédictions basées sur la recherche vectorielle."""
    
    def __init__(self):
        self.vector_store = VectorStore()
        self.synthesizer = Synthesizer()
    
    def _generate_smart_question(self, request: PredictRequest) -> str:
        """
        Génère une question intelligente basée sur le profil utilisateur.
        """
        try:
            # Accéder directement aux objets (plus besoin de JSON parsing)
            collection_data = request.collection if request.collection else {}
            read_data = request.read if request.read else {}
            
            # Si une question spécifique est fournie, l'utiliser
            if request.question:
                return request.question
            
            # Générer une question basée sur le type de prédiction et le profil
            if request.prediction_type == "collection":
                # Questions basées sur la collection existante
                collection_titles = list(collection_data.keys())
                read_titles = list(read_data.keys())
                
                if collection_titles:
                    if request.user_mood.lower() == "comique":
                        return f"Quels sont les moments les plus drôles dans {collection_titles[0]} ? Recommandez-moi des séries similaires avec beaucoup d'humour."
                    else:
                        return f"Basé sur ma collection de {', '.join(collection_titles[:3])}, quelles nouvelles séries du genre {request.category_preference} me recommanderiez-vous ?"
                else:
                    return f"Je suis un {request.user_genre} de {request.user_age} ans qui aime le {request.genre_preference} dans la catégorie {request.category_preference}. Que me recommandez-vous ?"
            
            elif request.prediction_type == "recommendation":
                mood_context = f"Je suis d'humeur {request.user_mood.lower()}" if request.user_mood else ""
                return f"Recommandez-moi des mangas {request.category_preference} adaptés à un {request.user_genre} de {request.user_age} ans. {mood_context}."
            
            # Question par défaut
            return f"Recommandez-moi des {request.genre_preference} dans la catégorie {request.category_preference}."
            
        except Exception as e:
            logging.warning(f"Erreur lors de la génération de la question: {e}")
            return f"Recommandez-moi des {request.genre_preference} dans la catégorie {request.category_preference}."
    
    def _build_metadata_filter(self, request: PredictRequest) -> Optional[Dict[str, Any]]:
        """
        Construit un filtre de métadonnées basé sur le profil utilisateur.
        """
        filters = {}
        
        # Filtre existant s'il est fourni
        if request.metadata_filter:
            filters.update(request.metadata_filter)
        
        # Ajouter des filtres basés sur les préférences
        if request.category_preference and request.category_preference != "Global":
            filters["categorie"] = request.category_preference
        
        # Si pas de filtre spécifique, utiliser les préférences de genre
        if not filters and request.genre_preference and request.genre_preference != "Global Manga":
            filters["genre"] = request.genre_preference
        
        return filters if filters else None
    
    def _extract_recommended_series(self, search_results, request: PredictRequest) -> List[RecommendedSeries]:
        """
        Extrait une liste de séries recommandées à partir des résultats de recherche.
        """
        recommended_series = []
        
        if search_results.empty:
            return recommended_series
        
        for _, row in search_results.iterrows():
            try:
                metadata = row.get('metadata', {})
                if isinstance(metadata, dict):
                    serie_title = metadata.get('serie_title', 'Titre inconnu')
                    genre = metadata.get('genre', 'Genre inconnu')
                    category = metadata.get('categorie', 'Catégorie inconnue')
                    similarity = row.get('similarity', 0.0)
                    
                    # Générer une raison personnalisée
                    reason = self._generate_recommendation_reason(serie_title, genre, category, request)
                    
                    recommended_series.append(RecommendedSeries(
                        title=serie_title,
                        genre=genre,
                        category=category,
                        similarity_score=round(float(similarity), 3) if similarity else None,
                        reason=reason
                    ))
            except Exception as e:
                logging.warning(f"Erreur lors de l'extraction de la série: {e}")
                continue
        
        return recommended_series
    
    def _generate_recommendation_reason(self, title: str, genre: str, category: str, request: PredictRequest) -> str:
        """
        Génère une raison personnalisée pour la recommandation.
        """
        reasons = []
        
        if genre and genre.lower() in request.category_preference.lower():
            reasons.append(f"correspond à votre préférence pour le {genre}")
        
        if request.user_mood.lower() == "comique" and any(word in genre.lower() for word in ["comique", "comédie", "humour"]):
            reasons.append("parfait pour votre humeur comique")
        elif request.user_mood.lower() == "action" and "action" in genre.lower():
            reasons.append("idéal pour votre envie d'action")
        
        if "seinen" in category.lower() and int(request.user_age) >= 16:
            reasons.append("adapté à un public mature")
        elif "shonen" in category.lower():
            reasons.append("style shonen dynamique")
        
        if not reasons:
            reasons.append(f"recommandé pour les amateurs de {genre}")
        
        return f"Recommandé car {' et '.join(reasons[:2])}"
    
    def _perform_contextual_search(self, request: PredictRequest, question: str, metadata_filter: Optional[Dict[str, Any]]):
        """
        Effectue une recherche vectorielle adaptée au contexte utilisateur.
        """
        base_limit = request.limit or 5
        
        if request.prediction_type == "collection":
            # Pour les recommandations basées sur la collection
            return self._search_for_collection_recommendations(request, question, metadata_filter, base_limit)
        elif request.prediction_type == "recommendation":
            # Pour les recommandations générales
            return self._search_for_general_recommendations(request, question, metadata_filter, base_limit)
        else:
            # Recherche standard
            return self.vector_store.search(
                query_text=question,
                limit=base_limit,
                metadata_filter=metadata_filter,
                return_dataframe=True
            )
    
    def _search_for_collection_recommendations(self, request: PredictRequest, question: str, metadata_filter: Optional[Dict[str, Any]], limit: int):
        """
        Recherche adaptée aux recommandations basées sur la collection existante.
        """
        collection_data = request.collection if request.collection else {}
        read_data = request.read if request.read else {}
        
        # Récupérer plus de résultats pour filtrer ceux de la collection existante
        extended_limit = limit * 3
        
        search_results = self.vector_store.search(
            query_text=question,
            limit=extended_limit,
            metadata_filter=metadata_filter,
            return_dataframe=True
        )
        
        if search_results.empty:
            return search_results
        
        # Filtrer les séries déjà possédées ou lues pour éviter les doublons
        owned_series = set(collection_data.keys()) if collection_data else set()
        read_series = set(read_data.keys()) if read_data else set()
        existing_series = owned_series.union(read_series)
        
        if existing_series and 'metadata' in search_results.columns:
            # Filtrer les séries déjà connues
            mask = ~search_results.apply(
                lambda row: any(series in str(row.get('metadata', {})) for series in existing_series), 
                axis=1
            )
            filtered_results = search_results[mask]
            
            # Prendre les meilleurs résultats après filtrage
            return filtered_results.head(limit) if not filtered_results.empty else search_results.head(limit)
        
        return search_results.head(limit)
    
    def _search_for_general_recommendations(self, request: PredictRequest, question: str, metadata_filter: Optional[Dict[str, Any]], limit: int):
        """
        Recherche pour des recommandations générales basées sur les préférences.
        """
        # Ajuster la recherche selon l'humeur
        enhanced_question = question
        if request.user_mood.lower() == "comique":
            enhanced_question = f"manga drôle humour comédie {question}"
        elif "action" in request.category_preference.lower():
            enhanced_question = f"manga action combat aventure {question}"
        elif "romance" in request.category_preference.lower():
            enhanced_question = f"manga romance amour relation {question}"
        
        return self.vector_store.search(
            query_text=enhanced_question,
            limit=limit,
            metadata_filter=metadata_filter,
            return_dataframe=True
        )
    
    async def predict(self, request: PredictRequest) -> PredictResponse:
        """
        Effectue une prédiction basée sur le profil utilisateur et ses préférences.
        
        Args:
            request: La requête de prédiction contenant le profil utilisateur
            
        Returns:
            PredictResponse: La réponse synthétisée avec les métadonnées
        """
        try:
            # Générer une question intelligente basée sur le profil
            generated_question = self._generate_smart_question(request)
            
            # Construire les filtres de métadonnées
            metadata_filter = self._build_metadata_filter(request)
            
            # Effectuer une recherche vectorielle adaptée au contexte utilisateur
            search_results = self._perform_contextual_search(request, generated_question, metadata_filter)
            
            # Générer la réponse synthétisée
            synthesizer_response = self.synthesizer.generate_response(
                question=generated_question,
                context=search_results
            )
            
            # Calculer les métadonnées
            sources_count = len(search_results) if not search_results.empty else 0
            avg_similarity = (
                search_results['similarity'].mean() 
                if not search_results.empty and 'similarity' in search_results.columns 
                else None
            )
            
            # Extraire la liste des séries recommandées
            recommended_series = self._extract_recommended_series(search_results, request)
            
            # Enrichir le thought_process avec les informations du profil
            enriched_thought_process = [
                f"Profil: {request.user_genre} de {request.user_age} ans",
                f"Préférences: {request.genre_preference} - {request.category_preference}",
                f"Humeur: {request.user_mood}",
                f"Question générée: {generated_question}",
                *synthesizer_response.thought_process
            ]
            
            # Construire la réponse finale
            return PredictResponse(
                answer=synthesizer_response.answer,
                thought_process=enriched_thought_process,
                enough_context=synthesizer_response.enough_context,
                sources_count=sources_count,
                recommended_series=recommended_series,
                avg_similarity=avg_similarity
            )
            
        except Exception as e:
            logging.error(f"Erreur lors de la prédiction: {e}")
            return PredictResponse(
                answer="Une erreur s'est produite lors du traitement de votre demande.",
                thought_process=[f"Erreur: {str(e)}"],
                enough_context=False,
                sources_count=0,
                recommended_series=[],
                avg_similarity=None
            )