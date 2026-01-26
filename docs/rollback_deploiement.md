# Documentation : Rollback et Restauration des Deploiements

Ce guide explique comment restaurer une version anterieure ou annuler un deploiement defectueux pour BookSync API Agent.

---

## Table des matieres

1. [Vue d'ensemble](#1-vue-densemble)
2. [Rollback automatique (CI/CD)](#2-rollback-automatique-cicd)
3. [Rollback manuel via GitHub Actions](#3-rollback-manuel-via-github-actions)
4. [Rollback via script local](#4-rollback-via-script-local)
5. [Rollback via Makefile](#5-rollback-via-makefile)
6. [Rollback via Azure CLI](#6-rollback-via-azure-cli)
7. [Verification post-rollback](#7-verification-post-rollback)
8. [Bonnes pratiques](#8-bonnes-pratiques)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Vue d'ensemble

Le systeme de rollback de BookSync API Agent fonctionne a plusieurs niveaux :

| Niveau | Methode | Quand l'utiliser |
|--------|---------|------------------|
| Automatique | CI/CD health check | Deploiement echoue automatiquement |
| Semi-automatique | GitHub Actions workflow | Intervention manuelle rapide |
| Manuel | Script local / Makefile | Controle total sur le processus |
| Urgence | Azure CLI direct | Situation critique |

**Architecture du rollback :**

```
Deploiement sur main
        |
        v
   Health Check
        |
   +----+----+
   |         |
  OK       ECHEC
   |         |
   v         v
  FIN    Rollback automatique
              |
         +----+----+
         |         |
        OK       ECHEC
         |         |
         v         v
        FIN    Alerte (intervention manuelle)
```

---

## 2. Rollback automatique (CI/CD)

Le workflow `.github/workflows/deploy.yml` inclut un systeme de rollback automatique :

### Fonctionnement

1. **Sauvegarde** : Avant chaque deploiement, l'image actuelle est sauvegardee
2. **Deploiement** : La nouvelle image est deployee
3. **Health Check** : 10 tentatives de verification sur `/predict/health`
4. **Rollback** : Si le health check echoue, rollback automatique vers la version precedente

### Configuration

Les parametres du health check sont definis dans `deploy.yml` :

```yaml
MAX_RETRIES=10           # Nombre de tentatives
RETRY_INTERVAL=15        # Secondes entre chaque tentative
HEALTH_ENDPOINT=/predict/health
```

### Logs

Les logs du rollback automatique sont visibles dans :
- GitHub Actions > Build and Deploy to Azure Container App > Job "build-and-deploy"
- Etapes "Health Check post-deploiement" et "Rollback automatique si echec"

---

## 3. Rollback manuel via GitHub Actions

Pour declencher un rollback manuellement depuis GitHub :

### Procedure

1. Aller sur GitHub > **Actions** > **Rollback Deployment**
2. Cliquer sur **Run workflow**
3. Selectionner les options :
   - `rollback_type` :
     - `previous` : Revient a la version precedente
     - `specific` : Deploie une version specifique (necessite `image_tag`)
     - `latest_stable` : Identique a previous
   - `image_tag` : Tag de l'image (SHA du commit, requis si `specific`)
   - `skip_health_check` : Ignorer la verification (non recommande)
4. Cliquer sur **Run workflow**

### Exemple

Pour revenir a la version precedente :
```
rollback_type: previous
```

Pour deployer une version specifique :
```
rollback_type: specific
image_tag: a1b2c3d4e5f6
```

### Artefacts

Chaque rollback cree un artefact `rollback-backup-{run_number}` contenant le tag de l'image precedente, permettant d'annuler le rollback si necessaire.

---

## 4. Rollback via script local

Le script `scripts/rollback.sh` permet un controle total sur le processus de rollback.

### Prerequis

- Azure CLI installe (`brew install azure-cli` sur macOS)
- Connexion Azure (`az login`)
- Script executable (`chmod +x scripts/rollback.sh`)

### Commandes disponibles

```bash
# Afficher l'aide
./scripts/rollback.sh --help

# Lister les images disponibles
./scripts/rollback.sh --list

# Afficher l'etat actuel
./scripts/rollback.sh

# Rollback vers la version precedente
./scripts/rollback.sh --previous

# Rollback vers une version specifique
./scripts/rollback.sh abc123def456

# Annuler le dernier rollback
./scripts/rollback.sh --cancel
```

### Fonctionnalites

- Verification des prerequis Azure
- Sauvegarde automatique de l'etat actuel
- Health check post-rollback
- Possibilite d'annuler le rollback
- Messages colores pour une meilleure lisibilite

### Exemple de session

```bash
$ ./scripts/rollback.sh --previous

[INFO] Verification des prerequis...
[OK] Prerequis verifies.
[INFO] Recherche de l'image precedente...
[INFO] Image precedente trouvee: a1b2c3d4
[INFO] Image actuelle: e5f6g7h8
[INFO] Image cible: a1b2c3d4

[ATTENTION] Vous allez effectuer un rollback de:
  e5f6g7h8 -> a1b2c3d4

Confirmer le rollback ? (oui/non): oui

[ROLLBACK] Demarrage du rollback vers: a1b2c3d4
[INFO] Etat actuel sauvegarde: e5f6g7h8
[INFO] Mise a jour du Container App...
[OK] Container App mis a jour avec l'image: a1b2c3d4

[INFO] Verification de la sante de l'application...
[INFO] URL de health check: https://api-booksync.azurecontainerapps.io/predict/health
[INFO] Tentative 1/10...
[OK] Application en bonne sante (HTTP 200)

=== ROLLBACK REUSSI ===
L'application est maintenant sur la version: a1b2c3d4
```

---

## 5. Rollback via Makefile

Le Makefile fournit des raccourcis pour les operations courantes :

```bash
# Lister les images disponibles
make rollback-list

# Afficher l'image actuellement deployee
make rollback-current

# Rollback vers la version precedente (interactif)
make rollback-previous

# Rollback interactif complet
make rollback

# Rollback vers une version specifique
make rollback-to TAG=abc123def456

# Verifier la sante de l'application
make health-check
```

### Exemple

```bash
$ make rollback-list

Liste des images disponibles dans ACR...
Result
--------
e5f6g7h8
a1b2c3d4
9z8y7x6w
...

$ make rollback-to TAG=a1b2c3d4
```

---

## 6. Rollback via Azure CLI

En cas d'urgence, utilisez directement Azure CLI :

```bash
# Lister les images disponibles
az acr repository show-tags \
  --name booksyncrepo \
  --repository api-booksync \
  --orderby time_desc \
  --top 10

# Voir l'image actuelle
az containerapp show \
  --name api-booksync \
  --resource-group vplatevoetRG \
  --query "properties.template.containers[0].image"

# Rollback vers une version specifique
az containerapp update \
  --name api-booksync \
  --resource-group vplatevoetRG \
  --image booksyncrepo.azurecr.io/api-booksync:<TAG>
```

---

## 7. Verification post-rollback

Apres tout rollback, verifiez que l'application fonctionne correctement :

### Health Check

```bash
# Via Makefile
make health-check

# Via curl
curl -s https://api-booksync.azurecontainerapps.io/predict/health

# Reponse attendue
{"status": "healthy", ...}
```

### Tests fonctionnels

```bash
# Test de l'endpoint de prediction
curl -X POST https://api-booksync.azurecontainerapps.io/predict/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <API_KEY>" \
  -d '{"user_profile": {...}}'
```

### Logs Azure

```bash
# Voir les logs du Container App
az containerapp logs show \
  --name api-booksync \
  --resource-group vplatevoetRG \
  --follow
```

---

## 8. Bonnes pratiques

### Avant le rollback

- Identifier clairement la cause du probleme
- Verifier que la version cible est stable
- Communiquer avec l'equipe si necessaire

### Pendant le rollback

- Ne pas interrompre le processus
- Surveiller les logs en temps reel
- Noter l'heure et la version

### Apres le rollback

- Verifier le health check
- Tester les fonctionnalites critiques
- Documenter l'incident

### Tracabilite

- Les images sont taggees avec le SHA du commit Git
- Permet de retrouver exactement le code source
- Historique conserve dans ACR pendant 30 jours minimum

---

## 9. Troubleshooting

### Le rollback echoue avec "Image not found"

**Cause** : L'image a ete supprimee du registre ACR.

**Solution** :
1. Lister les images disponibles : `make rollback-list`
2. Choisir une image existante
3. Si aucune image stable n'existe, rebuilder depuis Git

### Le health check echoue apres rollback

**Cause** : L'application met du temps a demarrer ou il y a un probleme de configuration.

**Solution** :
1. Verifier les logs : `az containerapp logs show --name api-booksync --resource-group vplatevoetRG`
2. Verifier les variables d'environnement
3. Tester manuellement l'endpoint de sante

### Azure CLI non connecte

**Cause** : Session Azure expiree.

**Solution** :
```bash
az login
az account set --subscription "<SUBSCRIPTION_ID>"
```

### Permissions insuffisantes

**Cause** : Compte Azure sans droits sur le Container App.

**Solution** :
- Verifier les roles RBAC sur le Resource Group
- Contacter l'administrateur Azure

---

## Ressources

- [Azure Container Apps Documentation](https://docs.microsoft.com/azure/container-apps/)
- [Azure CLI Reference](https://docs.microsoft.com/cli/azure/containerapp)
- [GitHub Actions Workflows](https://docs.github.com/actions/using-workflows)
