import logging
import os
from typing import List
import pandas as pd
from pydantic import BaseModel

from app.config.settings import get_settings
from openai import OpenAI, AzureOpenAI


class SynthesizerResponse(BaseModel):
    """Modèle de réponse du Synthesizer."""
    answer: str
    thought_process: List[str]
    enough_context: bool


class Synthesizer:
    """Service pour synthétiser des réponses basées sur le contexte récupéré."""

    @staticmethod
    def generate_response(question: str, context: pd.DataFrame, user_profile: dict = None) -> SynthesizerResponse:
        print("=== DEBUT generate_response ===")
        print(f"Question: {question}")
        print(f"Context shape: {context.shape if not context.empty else 'EMPTY'}")
        """
        Génère une réponse basée sur la question et le contexte fourni.
        
        Args:
            question: La question de l'utilisateur
            context: DataFrame contenant le contexte pertinent de la recherche vectorielle
            
        Returns:
            SynthesizerResponse: La réponse synthétisée avec le processus de réflexion
        """
        settings = get_settings()
        
        # Vérifier si Azure OpenAI doit être utilisé
        use_azure = os.getenv("USE_AZURE_OPENAI", "false").lower() == "true"
        
        if use_azure:
            client = AzureOpenAI(
                api_key=settings.azure_openai.api_key,
                api_version=settings.azure_openai.api_version,
                azure_endpoint=settings.azure_openai.azure_endpoint
            )
            model = settings.azure_openai.default_model
        else:
            client = OpenAI(api_key=settings.openai.api_key)
            model = settings.openai.default_model

        # Traitement du contexte
        if context.empty:
            context_text = "Aucun contexte spécifique trouvé dans la base de données."
        else:
            # Construire le contexte à partir du DataFrame
            context_text = ""
            for _, row in context.iterrows():
                context_text += f"Source (similarité: {row.get('similarity', 0):.3f}):\n"
                context_text += f"{row.get('content', '')}\n\n"

        profile_text = ""

        if user_profile:
            profile_text = f"""
            PROFIL UTILISATEUR:
            - Âge: {user_profile.get('user_age', 'Non spécifié')}
            - Genre: {user_profile.get('user_genre', 'Non spécifié')}
            - Préférence genre: {user_profile.get('genre_preference', 'Non spécifié')}
            - Préférence catégorie: {user_profile.get('category_preference', 'Non spécifié')}
            - Humeur actuelle: {user_profile.get('user_mood', 'Non spécifié')}
            - Type de prédiction: {user_profile.get('prediction_type', 'Non spécifié')}
            - Collection actuelle: {user_profile.get('collection', 'Aucune')}
            - Déjà lu: {user_profile.get('read', 'Rien')}
            """

        # Prompt système
        system_prompt = """
        Tu es un assistant spécialisé dans les recommandations de mangas et livres basées sur les profils utilisateurs.
        
        Tu reçois des données structurées contenant :
        - Le profil utilisateur (âge, genre, préférences de genre/catégorie, humeur)
        - La collection actuelle de l'utilisateur (séries possédées avec leurs volumes)
        - Les volumes déjà lus par l'utilisateur
        - Le type de prédiction demandée (collection ou recommendation)
        
        Ton rôle est de :
        1. Analyser le profil et les habitudes de lecture de l'utilisateur
        2. Utiliser le contexte fourni pour faire des recommandations pertinentes
        3. Tenir compte de l'humeur actuelle de l'utilisateur pour adapter tes suggestions
        4. Éviter de recommander ce que l'utilisateur a déjà lu
        
        Réponds de manière personnalisée en expliquant pourquoi tes recommandations correspondent au profil de l'utilisateur.
        Si le contexte n'est pas suffisant, dis-le clairement.
        
        IMPORTANT: Formate ta réponse sous forme de liste de séries avec pour chaque série :
        - Nom de la série
        - Raison de la recommandation basée sur le profil utilisateur
        - Correspondance avec l'humeur/préférences actuelles"""


        # Prompt utilisateur
        user_prompt = f"""
        Question: {question}
        {profile_text}
        Contexte disponible:
        {context_text}
        
        Utilise les informations du profil utilisateur pour faire des recommandations personnalisées. 
        Même sans contexte spécifique de la base de données, utilise tes connaissances générales sur les mangas pour recommander des séries adaptées au profil."""


        print('--------------------------------------------------------------')
        print(system_prompt)
        print('--------------------------------------------------------------')

        try:
            # Générer la réponse
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=settings.openai.temperature,
                max_tokens=settings.openai.max_tokens or 500
            )

            answer = response.choices[0].message.content

            # Évaluer si le contexte est suffisant (basé sur la similarité moyenne)
            avg_similarity = context['similarity'].mean() if 'similarity' in context.columns else 0
            enough_context = avg_similarity > 0.7  # Seuil de similarité

            # Processus de réflexion
            thought_process = [
                f"Recherche effectuée avec {len(context)} résultats",
                f"Similarité moyenne: {avg_similarity:.3f}",
                f"Contexte {'suffisant' if enough_context else 'insuffisant'} pour répondre"
            ]

            return SynthesizerResponse(
                answer=answer,
                thought_process=thought_process,
                enough_context=enough_context
            )

        except Exception as e:
            logging.error(f"Erreur lors de la génération de la réponse: {e}")
            return SynthesizerResponse(
                answer="Une erreur s'est produite lors de la génération de la réponse.",
                thought_process=[f"Erreur: {str(e)}"],
                enough_context=False
            )