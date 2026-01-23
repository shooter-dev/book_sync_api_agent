# Documentation : Sécurité et rotation des secrets

Ce guide explique, étape par étape, comment gérer, auditer et faire tourner les secrets (API keys, credentials Azure) pour BookSync API Agent, de A à Z.

---

# Rotation et gestion des secrets Azure

## 1. Pourquoi ?
- Pour éviter qu’un secret compromis ne permette un accès non autorisé à l’infrastructure.
- Pour répondre aux exigences de sécurité MLOps/E3.

## 2. Comment faire ?

### a. Régénérer les clés du registre Azure
1. Va dans Azure Portal > Registres de conteneurs > bookSyncRepo > Accès clés
2. Clique sur "Régénérer" pour la clé principale ou secondaire
3. Copie la nouvelle clé

### b. Mettre à jour le secret GitHub
1. Va dans GitHub > Settings > Secrets and variables > Actions
2. Modifie le secret `AZURE_CREDENTIALS` avec la nouvelle clé

### c. Relancer un déploiement
- Pousse un commit sur `main` pour relancer le pipeline CI/CD

## 3. Preuves pour la certification
- Prends une capture d’écran de la rotation dans Azure
- Prends une capture d’écran de la mise à jour du secret dans GitHub

---

**Explique à l’oral pourquoi la rotation est importante et comment tu l’as faite.**
