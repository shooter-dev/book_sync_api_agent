#!/bin/sh
# Script de rollback automatique pour BookSync API Agent
# Usage : ./rollback_deployment.sh <IMAGE_TAG_PRECEDENT>
# Ce script est à supprimer (voir docs/_A_SUPPRIMER.txt)

set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <IMAGE_TAG_PRECEDENT>"
  exit 1
fi

IMAGE_TAG_PRECEDENT=$1
REGISTRY=booksyncrepo.azurecr.io
IMAGE=api-booksync
RESOURCE_GROUP=vplatevoetRG
CONTAINER_APP=api-booksync

# Mise à jour du container avec l'image précédente
az containerapp update \
  --name $CONTAINER_APP \
  --resource-group $RESOURCE_GROUP \
  --image $REGISTRY/$IMAGE:$IMAGE_TAG_PRECEDENT

echo "Rollback effectué vers l'image : $IMAGE_TAG_PRECEDENT"
