#!/usr/bin/env python3
"""
Script pour créer un message vocal d'alerte de consommation de tokens Claude Code
Utilise la synthèse vocale intégrée de macOS (say command)
"""

import subprocess
import sys
from datetime import datetime

def create_voice_alert(message_type="warning", custom_message=None):
    """
    Crée et joue un message vocal d'alerte
    
    Args:
        message_type (str): Type d'alerte ('warning', 'critical', 'info')
        custom_message (str): Message personnalisé optionnel
    """
    
    # Messages prédéfinis
    messages = {
        "warning": "Attention ! Vos tokens Claude Code sont bientôt épuisés. Il vous reste moins de 20 pour cent de votre allocation.",
        "critical": "Alerte critique ! Consommation de vos tokens Claude Code terminée. Votre bloc de facturation est épuisé.",
        "info": "Information : Votre consommation de tokens Claude Code est actuellement à 50 pour cent.",
        "custom": custom_message or "Message d'alerte tokens Claude Code."
    }
    
    # Sélection du message
    message = messages.get(message_type, messages["warning"])
    
    # Configuration de la voix (française)
    voice_options = [
        "-v", "Amélie",  # Voix française féminine
        "-r", "180"      # Vitesse de parole (mots par minute)
    ]
    
    try:
        # Affichage du message
        print(f"🔊 Message vocal: {message}")
        print(f"⏰ Heure: {datetime.now().strftime('%H:%M:%S')}")
        
        # Commande say pour macOS
        cmd = ["say"] + voice_options + [message]
        
        # Exécution de la commande
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Message vocal joué avec succès")
        else:
            print(f"❌ Erreur lors de la lecture: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("⏱️ Timeout: Message vocal trop long")
    except FileNotFoundError:
        print("❌ Commande 'say' non trouvée. Ce script nécessite macOS.")
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")

def check_token_usage_and_alert():
    """
    Vérifie l'utilisation des tokens via ccusage et déclenche une alerte si nécessaire
    """
    try:
        # Exécution de ccusage blocks pour obtenir les données actuelles
        result = subprocess.run(
            ["npx", "ccusage@latest", "blocks", "--json"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            
            # Recherche du bloc actif
            for block in data.get("blocks", []):
                if block.get("status") == "active":
                    percentage = block.get("percentage", 0)
                    
                    if percentage >= 95:
                        create_voice_alert("critical")
                    elif percentage >= 80:
                        create_voice_alert("warning")
                    else:
                        print(f"ℹ️ Utilisation actuelle: {percentage}% - Pas d'alerte nécessaire")
                    break
            else:
                print("ℹ️ Aucun bloc actif trouvé")
                
    except subprocess.TimeoutExpired:
        print("⏱️ Timeout lors de la vérification ccusage")
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        alert_type = sys.argv[1]
        custom_msg = sys.argv[2] if len(sys.argv) > 2 else None
        create_voice_alert(alert_type, custom_msg)
    else:
        # Mode automatique: vérification et alerte conditionnelle
        check_token_usage_and_alert()