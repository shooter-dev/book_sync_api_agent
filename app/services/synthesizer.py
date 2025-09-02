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

    def generate_global_response(self, recommended_series: List, user_profile: dict) -> str:
        """
        Génère une réponse globale personnalisée pour l'utilisateur.
        """
        print("=== DEBUT generate_global_response ===")
        print(f"Séries recommandées: {len(recommended_series)}")
        print(f"Profil utilisateur: {user_profile.get('user_genre')} {user_profile.get('user_age')} ans")
        
        try:
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
            
            # Construire la liste des séries recommandées
            series_list = ""
            if recommended_series:
                for i, serie in enumerate(recommended_series, 1):
                    series_list += f"{i}. {serie.title}\n"
            else:
                series_list = "Aucune série trouvée dans la base de données."
            
            # Prompt pour générer une réponse globale personnalisée
            prompt = f"""
Profil utilisateur:
- Âge: {user_profile.get('user_age')} ans
- Genre: {user_profile.get('user_genre')}
- Préférences: {user_profile.get('genre_preference')} - {user_profile.get('category_preference')}
- Humeur: {user_profile.get('user_mood', 'Non spécifiée')}
- Type de prédiction: {user_profile.get('prediction_type')}

Séries recommandées trouvées:
{series_list}

Génère une réponse personnalisée et chaleureuse (2-3 phrases maximum) qui:
1. S'adresse directement à l'utilisateur
2. Explique brièvement pourquoi ces recommandations correspondent à son profil
3. Prend en compte son humeur et ses préférences
4. Reste concise et engageante

Réponse uniquement le texte, sans format JSON ni structure supplémentaire.
"""
            
            print('--------------------------------------------------------------')
            print(prompt)
            print('--------------------------------------------------------------')
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=200
            )
            
            global_response = response.choices[0].message.content.strip()
            print(f"Réponse globale générée: {global_response}")
            
            return global_response
            
        except Exception as e:
            logging.error(f"Erreur lors de la génération de la réponse globale: {e}")
            return f"Voici mes recommandations basées sur votre profil {user_profile.get('user_genre')} de {user_profile.get('user_age')} ans avec des préférences pour le {user_profile.get('category_preference')}."