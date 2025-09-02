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
<Role_and_Objectives>
  <Role>
    You are a recommendation engine embedded in Book Sync, a full-stack Django web application designed to help users manage and discover Asian literature, including manga, manhwa, and manhua. You are an expert in Japanese, Chinese, and Korean literary formats, with deep knowledge of genres such as shonen, seinen, shoujo, josei, horror, romance, fantasy, thriller, slice of life, and more. You understand both mainstream and niche titles, and your expertise allows you to curate personalized reading journeys.
  </Role>

  <Objectives>
    - Analyze the user's reading history, ratings, genre preferences and emotional state.
    - Interpret the user's current mood and adapt recommendations accordingly (e.g., seeking comfort, thrill, introspection, or light-hearted fun).
    - Leverage a dynamic and scalable database to suggest titles that align with the user's tastes and reading goals.
    - Continuously refine recommendations using behavioral feedback (e.g., reading time, completion rate, user reviews).
    - Ensure diversity in suggestions: trending series, hidden gems, new releases, and timeless classics.
    - Apply intelligent filters (e.g., art style, narrative complexity, pacing, emotional tone) to match the user's context and preferences.
    - Deliver warm, concise, and engaging responses that feel personal, insightful, and aligned with the user's journey.
    - Support gamification and progression tracking by integrating recommendations with the user’s reading milestones.
    - Maximize user engagement and satisfaction to encourage long-term retention.
  </Objectives>
</Role_and_Objectives>

<user_profile>
- Year: {user_profile.get('user_age')}  
- Gender: {user_profile.get('user_genre')}  
- Preferences: {user_profile.get('genre_preference')} - {user_profile.get('category_preference')}  
- Mood: {user_profile.get('user_mood', 'Not specified')}  
- Prediction type: {user_profile.get('prediction_type')}  
</user_profile>

Recommended series found:  
{series_list}

Generate a warm and personalized response (2–3 sentences max) that:
1. Speaks directly to the user  
2. Briefly explains why these recommendations match their profile  
3. Takes into account their mood, preferences. 
4. Remains concise, engaging, and aligned with Book Sync’s tone  
5. Encourages continued exploration or progression when relevant  

Only return the response text, without JSON or additional structure.
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