#!/bin/bash
# Script pour envoyer 100 requêtes POST totalement différentes à /predict/
# Génère des valeurs aléatoires et des variations de structure

URL="http://localhost:8000/predict/"
API_KEY="azerty@&123"

user_genres=(homme femme autre)
genre_preferences=(roman manga bd fantasy thriller)
category_preferences=(aventure action comedie drame science-fiction)
prediction_types=(recommendation forecast analysis)
user_moods=(heureux triste enerve fatigue motive)

for i in {1..100}; do
  age=$((RANDOM % 70 + 10))
  genre=${user_genres[$((RANDOM % ${#user_genres[@]}))]}
  gpref=${genre_preferences[$((RANDOM % ${#genre_preferences[@]}))]}
  catpref=${category_preferences[$((RANDOM % ${#category_preferences[@]}))]}
  ptype=${prediction_types[$((RANDOM % ${#prediction_types[@]}))]}
  mood=${user_moods[$((RANDOM % ${#user_moods[@]}))]}

  # Ajout de variations sur collection et read
  if (( RANDOM % 2 )); then
    collection="\"collection\": {\"serie_$i\": {\"volumes\": [$i, $((i+1))]}}"
  else
    collection=""
  fi
  if (( RANDOM % 2 )); then
    read="\"read\": {\"serie_$((i+50))\": {\"volumes\": [$((i+2)), $((i+3))]}}"
  else
    read=""
  fi

  # Construction du JSON
  json="{\"user_age\": \"$age\", \"user_genre\": \"$genre\", \"genre_preference\": \"$gpref\", \"category_preference\": \"$catpref\", \"prediction_type\": \"$ptype\", \"user_mood\": \"$mood\""
  if [ -n "$collection" ]; then
    json+=" , $collection"
  fi
  if [ -n "$read" ]; then
    json+=" , $read"
  fi
  json+="}"

  echo "Envoi requête $i/100 : $json"
  curl -X POST "$URL" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $API_KEY" \
    -d "$json"
  sleep 1

done
