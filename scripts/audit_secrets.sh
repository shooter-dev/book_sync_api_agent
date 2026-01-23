#!/bin/sh
# Script d'audit de sécurité des secrets pour BookSync API Agent
# Usage : ./audit_secrets.sh

set -e

# Vérification des secrets dans le code source
if grep -r --exclude-dir=.git --exclude='*.md' --exclude='*.yml' --exclude='*.env' 'API_KEY=' .; then
  echo "[ALERTE] Des secrets sont présents en clair dans le code source !"
else
  echo "[OK] Aucun secret en clair détecté dans le code source."
fi

# Vérification des permissions sur les fichiers sensibles
find . -type f \( -name '*.env' -o -name 'alertmanager.yml' -o -name 'prometheus.yml' \) -exec ls -l {} \;

# Ce script est à supprimer (voir docs/_A_SUPPRIMER.txt)
