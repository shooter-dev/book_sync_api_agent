#!/bin/bash
# =============================================================================
# Script de rollback pour BookSync API Agent
# =============================================================================
# Ce script permet de restaurer une version anterieure de l'application
# deployee sur Azure Container Apps.
#
# Usage:
#   ./rollback.sh                          # Affiche les dernieres images disponibles
#   ./rollback.sh <IMAGE_TAG>              # Rollback vers une image specifique
#   ./rollback.sh --latest-stable          # Rollback vers la derniere image stable
#   ./rollback.sh --previous               # Rollback vers l'image precedente
#
# Prerequis:
#   - Azure CLI installe et connecte (az login)
#   - Acces au Resource Group et Container App
# =============================================================================

set -e

# =============================================================================
# Configuration
# =============================================================================
REGISTRY="booksyncrepo.azurecr.io"
IMAGE_NAME="api-booksync"
RESOURCE_GROUP="vplatevoetRG"
CONTAINER_APP="api-booksync"
HEALTH_ENDPOINT="/predict/health"
MAX_HEALTH_RETRIES=10
HEALTH_RETRY_INTERVAL=15

# Couleurs pour les messages
ROUGE='\033[0;31m'
VERT='\033[0;32m'
JAUNE='\033[1;33m'
BLEU='\033[0;34m'
NC='\033[0m' # Pas de couleur

# =============================================================================
# Fonctions utilitaires
# =============================================================================

afficher_aide() {
    # Affiche l'aide du script avec les options disponibles
    echo -e "${BLEU}=== Script de Rollback BookSync API ===${NC}"
    echo ""
    echo "Usage:"
    echo "  $0                          Affiche les dernieres images disponibles"
    echo "  $0 <IMAGE_TAG>              Rollback vers une image specifique (SHA du commit)"
    echo "  $0 --latest-stable          Rollback vers la derniere image stable connue"
    echo "  $0 --previous               Rollback vers l'image precedente"
    echo "  $0 --list                   Liste les 10 dernieres images disponibles"
    echo "  $0 --help                   Affiche cette aide"
    echo ""
    echo "Exemples:"
    echo "  $0 abc123def456             Rollback vers le commit abc123def456"
    echo "  $0 --previous               Revient a la version precedente"
    echo ""
}

verifier_prerequis() {
    # Verifie que Azure CLI est installe et connecte
    echo -e "${BLEU}[INFO]${NC} Verification des prerequis..."

    if ! command -v az &> /dev/null; then
        echo -e "${ROUGE}[ERREUR]${NC} Azure CLI n'est pas installe."
        echo "Installez-le avec: brew install azure-cli (macOS) ou voir https://docs.microsoft.com/cli/azure/install-azure-cli"
        exit 1
    fi

    # Verifie la connexion Azure
    if ! az account show &> /dev/null; then
        echo -e "${ROUGE}[ERREUR]${NC} Vous n'etes pas connecte a Azure."
        echo "Connectez-vous avec: az login"
        exit 1
    fi

    echo -e "${VERT}[OK]${NC} Prerequis verifies."
}

lister_images_disponibles() {
    # Liste les dernieres images disponibles dans Azure Container Registry
    # Retourne les 10 dernieres images triees par date
    echo -e "${BLEU}[INFO]${NC} Recuperation des images disponibles dans ACR..."

    # Recupere les tags avec leurs dates de creation
    IMAGES=$(az acr repository show-tags \
        --name booksyncrepo \
        --repository "$IMAGE_NAME" \
        --orderby time_desc \
        --top 10 \
        --output table 2>/dev/null)

    if [ -z "$IMAGES" ]; then
        echo -e "${ROUGE}[ERREUR]${NC} Aucune image trouvee dans le registre."
        exit 1
    fi

    echo -e "${VERT}[OK]${NC} Images disponibles (10 dernieres):"
    echo "$IMAGES"
}

obtenir_image_actuelle() {
    # Recupere le tag de l'image actuellement deployee
    # Retourne le tag de l'image en cours d'execution
    IMAGE_ACTUELLE=$(az containerapp show \
        --name "$CONTAINER_APP" \
        --resource-group "$RESOURCE_GROUP" \
        --query "properties.template.containers[0].image" \
        --output tsv 2>/dev/null)

    # Extrait le tag de l'image complete
    TAG_ACTUEL=$(echo "$IMAGE_ACTUELLE" | sed 's/.*://')
    echo "$TAG_ACTUEL"
}

obtenir_image_precedente() {
    # Recupere le tag de l'image precedente (avant l'actuelle)
    # Retourne le tag de la deuxieme image la plus recente
    echo -e "${BLEU}[INFO]${NC} Recherche de l'image precedente..."

    # Liste les 2 dernieres images
    IMAGES=$(az acr repository show-tags \
        --name booksyncrepo \
        --repository "$IMAGE_NAME" \
        --orderby time_desc \
        --top 2 \
        --output tsv 2>/dev/null)

    # Prend la deuxieme ligne (image precedente)
    IMAGE_PRECEDENTE=$(echo "$IMAGES" | sed -n '2p')

    if [ -z "$IMAGE_PRECEDENTE" ]; then
        echo -e "${ROUGE}[ERREUR]${NC} Impossible de trouver l'image precedente."
        exit 1
    fi

    echo "$IMAGE_PRECEDENTE"
}

sauvegarder_etat_actuel() {
    # Sauvegarde l'etat actuel avant le rollback pour pouvoir annuler si necessaire
    # Cree un fichier de backup avec le tag de l'image actuelle
    local TAG_ACTUEL
    TAG_ACTUEL=$(obtenir_image_actuelle)

    # Cree le repertoire de backup si necessaire
    BACKUP_DIR="$(dirname "$0")/.rollback_backups"
    mkdir -p "$BACKUP_DIR"

    # Sauvegarde le tag avec timestamp
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    echo "$TAG_ACTUEL" > "$BACKUP_DIR/backup_$TIMESTAMP.txt"

    echo -e "${BLEU}[INFO]${NC} Etat actuel sauvegarde: $TAG_ACTUEL"
    echo -e "${BLEU}[INFO]${NC} Fichier de backup: $BACKUP_DIR/backup_$TIMESTAMP.txt"
}

executer_rollback() {
    # Execute le rollback vers l'image specifiee
    # Parametres:
    #   $1 - Tag de l'image cible
    local IMAGE_TAG=$1

    echo -e "${JAUNE}[ROLLBACK]${NC} Demarrage du rollback vers: $IMAGE_TAG"

    # Sauvegarde l'etat actuel
    sauvegarder_etat_actuel

    # Mise a jour du Container App avec l'image cible
    echo -e "${BLEU}[INFO]${NC} Mise a jour du Container App..."
    az containerapp update \
        --name "$CONTAINER_APP" \
        --resource-group "$RESOURCE_GROUP" \
        --image "$REGISTRY/$IMAGE_NAME:$IMAGE_TAG" \
        --output none

    echo -e "${VERT}[OK]${NC} Container App mis a jour avec l'image: $IMAGE_TAG"
}

verifier_health() {
    # Verifie que l'application repond correctement apres le rollback
    # Effectue plusieurs tentatives avec un delai entre chaque
    # Retourne 0 si l'application est saine, 1 sinon
    echo -e "${BLEU}[INFO]${NC} Verification de la sante de l'application..."

    # Recupere l'URL du Container App
    APP_URL=$(az containerapp show \
        --name "$CONTAINER_APP" \
        --resource-group "$RESOURCE_GROUP" \
        --query "properties.configuration.ingress.fqdn" \
        --output tsv 2>/dev/null)

    if [ -z "$APP_URL" ]; then
        echo -e "${JAUNE}[AVERTISSEMENT]${NC} Impossible de recuperer l'URL de l'application."
        return 1
    fi

    HEALTH_URL="https://$APP_URL$HEALTH_ENDPOINT"
    echo -e "${BLEU}[INFO]${NC} URL de health check: $HEALTH_URL"

    # Boucle de verification avec retries
    for i in $(seq 1 $MAX_HEALTH_RETRIES); do
        echo -e "${BLEU}[INFO]${NC} Tentative $i/$MAX_HEALTH_RETRIES..."

        # Effectue la requete de health check
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" --max-time 10 2>/dev/null || echo "000")

        if [ "$HTTP_CODE" = "200" ]; then
            echo -e "${VERT}[OK]${NC} Application en bonne sante (HTTP $HTTP_CODE)"
            return 0
        fi

        echo -e "${JAUNE}[AVERTISSEMENT]${NC} Health check echoue (HTTP $HTTP_CODE), attente de ${HEALTH_RETRY_INTERVAL}s..."
        sleep $HEALTH_RETRY_INTERVAL
    done

    echo -e "${ROUGE}[ERREUR]${NC} L'application ne repond pas apres $MAX_HEALTH_RETRIES tentatives."
    return 1
}

annuler_rollback() {
    # Annule le rollback en restaurant l'image sauvegardee
    # Utilise le dernier fichier de backup
    BACKUP_DIR="$(dirname "$0")/.rollback_backups"

    # Trouve le dernier fichier de backup
    DERNIER_BACKUP=$(ls -t "$BACKUP_DIR"/backup_*.txt 2>/dev/null | head -1)

    if [ -z "$DERNIER_BACKUP" ]; then
        echo -e "${ROUGE}[ERREUR]${NC} Aucun backup trouve pour annuler le rollback."
        exit 1
    fi

    TAG_PRECEDENT=$(cat "$DERNIER_BACKUP")

    echo -e "${JAUNE}[ANNULATION]${NC} Annulation du rollback, retour vers: $TAG_PRECEDENT"

    az containerapp update \
        --name "$CONTAINER_APP" \
        --resource-group "$RESOURCE_GROUP" \
        --image "$REGISTRY/$IMAGE_NAME:$TAG_PRECEDENT" \
        --output none

    echo -e "${VERT}[OK]${NC} Rollback annule, application restauree vers: $TAG_PRECEDENT"
}

# =============================================================================
# Script principal
# =============================================================================

main() {
    # Point d'entree principal du script
    # Gere les differentes options et execute le rollback

    # Affiche l'aide si demande
    if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
        afficher_aide
        exit 0
    fi

    # Verifie les prerequis Azure
    verifier_prerequis

    # Traitement des options
    case "$1" in
        --list)
            # Liste les images disponibles
            lister_images_disponibles
            exit 0
            ;;
        --previous)
            # Rollback vers l'image precedente
            IMAGE_CIBLE=$(obtenir_image_precedente)
            echo -e "${BLEU}[INFO]${NC} Image precedente trouvee: $IMAGE_CIBLE"
            ;;
        --latest-stable)
            # Rollback vers la deuxieme image (supposee stable)
            IMAGE_CIBLE=$(obtenir_image_precedente)
            echo -e "${BLEU}[INFO]${NC} Image stable trouvee: $IMAGE_CIBLE"
            ;;
        --cancel)
            # Annule le dernier rollback
            annuler_rollback
            exit 0
            ;;
        "")
            # Aucun argument: affiche les images disponibles
            echo -e "${BLEU}[INFO]${NC} Image actuellement deployee: $(obtenir_image_actuelle)"
            echo ""
            lister_images_disponibles
            echo ""
            echo -e "${JAUNE}[INFO]${NC} Pour effectuer un rollback, utilisez: $0 <IMAGE_TAG>"
            exit 0
            ;;
        *)
            # Argument fourni: utilise comme tag d'image
            IMAGE_CIBLE=$1
            ;;
    esac

    # Affiche l'image actuelle
    TAG_ACTUEL=$(obtenir_image_actuelle)
    echo -e "${BLEU}[INFO]${NC} Image actuelle: $TAG_ACTUEL"
    echo -e "${BLEU}[INFO]${NC} Image cible: $IMAGE_CIBLE"

    # Confirmation avant rollback
    echo ""
    echo -e "${JAUNE}[ATTENTION]${NC} Vous allez effectuer un rollback de:"
    echo "  $TAG_ACTUEL -> $IMAGE_CIBLE"
    echo ""
    read -p "Confirmer le rollback ? (oui/non): " CONFIRMATION

    if [ "$CONFIRMATION" != "oui" ]; then
        echo -e "${BLEU}[INFO]${NC} Rollback annule par l'utilisateur."
        exit 0
    fi

    # Execute le rollback
    executer_rollback "$IMAGE_CIBLE"

    # Verifie la sante de l'application
    echo ""
    if verifier_health; then
        echo ""
        echo -e "${VERT}=== ROLLBACK REUSSI ===${NC}"
        echo -e "L'application est maintenant sur la version: $IMAGE_CIBLE"
    else
        echo ""
        echo -e "${ROUGE}=== ROLLBACK ECHOUE ===${NC}"
        echo -e "L'application ne repond pas correctement."
        echo ""
        read -p "Voulez-vous annuler le rollback et revenir a la version precedente ? (oui/non): " ANNULER

        if [ "$ANNULER" = "oui" ]; then
            annuler_rollback
            verifier_health
        else
            echo -e "${JAUNE}[AVERTISSEMENT]${NC} Rollback conserve malgre l'echec du health check."
            echo "Vous pouvez annuler manuellement avec: $0 --cancel"
        fi
    fi
}

# Execution du script principal
main "$@"
