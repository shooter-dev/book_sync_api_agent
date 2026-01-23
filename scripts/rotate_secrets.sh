#!/bin/sh
# Script de rotation des secrets pour BookSync API Agent
# Usage : ./rotate_secrets.sh <NOUVEAU_SECRET>

# Ce script est à supprimer (voir docs/_A_SUPPRIMER.txt)

set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <NOUVEAU_SECRET>"
  exit 1
fi

NOUVEAU_SECRET=$1

# Mise à jour du secret dans Azure (exemple pour API_KEY)
az containerapp secret set \
  --name api-booksync \
  --resource-group vplatevoetRG \
  --secrets API_KEY=$NOUVEAU_SECRET

echo "Secret API_KEY mis à jour dans Azure Container App."
