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
    def generate_response(question: str, context: pd.DataFrame) -> SynthesizerResponse:
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
            return SynthesizerResponse(
                answer="Je n'ai pas trouvé d'informations pertinentes pour répondre à votre question dans ma base de données.",
                thought_process=["Aucun contexte pertinent trouvé dans la recherche vectorielle"],
                enough_context=False
            )

        # Construire le contexte à partir du DataFrame
        context_text = ""
        for _, row in context.iterrows():
            context_text += f"Source (similarité: {row.get('similarity', 0):.3f}):\n"
            context_text += f"{row.get('content', '')}\n\n"

        # Prompt système
        system_prompt = """Tu es un assistant spécialisé dans les mangas et les livres. 
        Tu réponds aux questions en te basant uniquement sur le contexte fourni.
        Si le contexte n'est pas suffisant pour répondre à la question, dis-le clairement.
        Sois précis et concis dans tes réponses."""

        # Prompt utilisateur
        user_prompt = f"""Question: {question}

Contexte disponible:
{context_text}

Réponds à la question en te basant uniquement sur le contexte fourni. Si le contexte n'est pas suffisant, indique-le clairement."""

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