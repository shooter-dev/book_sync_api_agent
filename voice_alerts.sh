#!/bin/bash

# Script de messages vocaux d'alerte pour ccusage
# Utilise la synthèse vocale native de macOS

# Configuration
VOICE="Amélie"  # Voix française
RATE="180"      # Vitesse de parole

# Fonction pour jouer un message vocal
play_voice_message() {
    local message="$1"
    local urgency="${2:-normal}"
    
    echo "🔊 $(date '+%H:%M:%S') - $message"
    
    case $urgency in
        "urgent")
            # Message urgent: répété 2 fois avec pause
            say -v "$VOICE" -r "$RATE" "$message"
            sleep 1
            say -v "$VOICE" -r "$RATE" "Je répète: $message"
            ;;
        "critical")
            # Message critique: voix plus lente et forte
            say -v "$VOICE" -r "150" "$message"
            ;;
        *)
            # Message normal
            say -v "$VOICE" -r "$RATE" "$message"
            ;;
    esac
}

# Messages prédéfinis
case "${1:-check}" in
    "finished"|"fini")
        play_voice_message "Alerte critique ! Consommation de vos tokens Claude Code terminée. Votre bloc de facturation est épuisé." "critical"
        ;;
    "warning"|"attention")
        play_voice_message "Attention ! Vos tokens Claude Code sont bientôt épuisés. Il vous reste moins de vingt pour cent de votre allocation." "urgent"
        ;;
    "50percent")
        play_voice_message "Information : Votre consommation de tokens Claude Code est actuellement à cinquante pour cent."
        ;;
    "80percent")
        play_voice_message "Avertissement : Vous avez consommé quatre-vingts pour cent de vos tokens Claude Code." "urgent"
        ;;
    "custom")
        if [ -n "$2" ]; then
            play_voice_message "$2"
        else
            echo "❌ Usage: $0 custom 'votre message'"
            exit 1
        fi
        ;;
    "check")
        # Vérification automatique avec ccusage
        echo "🔍 Vérification de l'utilisation des tokens..."
        
        if command -v npx >/dev/null 2>&1; then
            # Récupération du pourcentage d'utilisation actuel
            CURRENT_USAGE=$(npx ccusage@latest blocks 2>/dev/null | grep "elapsed" | grep -oE "[0-9]+\.[0-9]+%" | head -1 | sed 's/%//')
            
            if [ -n "$CURRENT_USAGE" ]; then
                echo "📊 Utilisation actuelle: ${CURRENT_USAGE}%"
                
                # Conversion en nombre entier
                USAGE_INT=$(echo "$CURRENT_USAGE" | cut -d. -f1)
                
                if [ "$USAGE_INT" -ge 95 ]; then
                    play_voice_message "Alerte critique ! Vos tokens Claude Code sont presque épuisés à ${CURRENT_USAGE} pour cent !" "critical"
                elif [ "$USAGE_INT" -ge 80 ]; then
                    play_voice_message "Attention ! Vous avez consommé ${CURRENT_USAGE} pour cent de vos tokens Claude Code." "urgent"
                elif [ "$USAGE_INT" -ge 50 ]; then
                    play_voice_message "Information : Vous avez consommé ${CURRENT_USAGE} pour cent de vos tokens Claude Code."
                else
                    echo "✅ Utilisation normale (${CURRENT_USAGE}%) - Pas d'alerte vocale nécessaire"
                fi
            else
                echo "❌ Impossible de récupérer les données d'utilisation"
                play_voice_message "Impossible de vérifier l'état de vos tokens Claude Code."
            fi
        else
            echo "❌ npx non trouvé. Installation de Node.js requise."
        fi
        ;;
    "test")
        echo "🧪 Test des messages vocaux..."
        play_voice_message "Test du système d'alerte vocale Claude Code. Message reçu cinq sur cinq."
        ;;
    "help"|*)
        cat << EOF
🔊 Messages Vocaux ccusage - Aide

Usage: $0 [COMMANDE] [MESSAGE_OPTIONNEL]

Commandes disponibles:
  check       - Vérification automatique et alerte conditionnelle (défaut)
  fini        - Message de consommation terminée
  attention   - Message d'avertissement (< 20% restant)
  50percent   - Message à 50% de consommation
  80percent   - Message à 80% de consommation
  custom "msg"- Message personnalisé
  test        - Test du système vocal
  help        - Affiche cette aide

Exemples:
  $0                                    # Vérification automatique
  $0 fini                              # Alerte consommation terminée
  $0 custom "Pause déjeuner dans 5 minutes"  # Message personnalisé

Configuration:
  Voix: $VOICE
  Vitesse: $RATE mots/minute
  
Dépendances: macOS avec commande 'say', npx pour ccusage
EOF
        ;;
esac