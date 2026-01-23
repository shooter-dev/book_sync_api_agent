#!/bin/sh
# Script de test de performance pour BookSync API Agent
# Usage : ./scripts/perf_test.sh <URL_API> <API_KEY>

# Ce script est à supprimer (voir docs/_A_SUPPRIMER.txt)

set -e

if [ -z "$1" ] || [ -z "$2" ]; then
  echo "Usage: $0 <URL_API> <API_KEY>"
  exit 1
fi

URL_API=$1
API_KEY=$2

# Test de charge avec Apache Benchmark (ab)
ab -n 500 -c 20 -H "X-API-Key: $API_KEY" -p perf_payload.json -T application/json $URL_API/predict/ > perf_report.txt

echo "Test de performance terminé. Rapport : perf_report.txt"
