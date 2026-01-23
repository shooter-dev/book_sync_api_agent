# Documentation : Rollback et gestion des erreurs de déploiement

Ce guide explique comment restaurer une version antérieure ou annuler un déploiement défectueux pour BookSync API Agent.

---

## 1. Rollback automatique via script

Utiliser le script `scripts/rollback_deployment.sh` pour revenir à une image précédente en cas d'échec du déploiement ou de health check :

```bash
./scripts/rollback_deployment.sh <IMAGE_TAG_PRECEDENT>
```

- Remplace `<IMAGE_TAG_PRECEDENT>` par le tag de l'image Docker à restaurer (visible dans Azure Container Registry ou dans l'historique des déploiements).
- Le script met à jour le container Azure avec l'image spécifiée.

## 2. Procédure manuelle de restauration

1. Identifier le tag de l'image stable à restaurer.
2. Lancer le script rollback ou utiliser la commande Azure CLI :
   ```bash
   az containerapp update --name api-booksync --resource-group vplatevoetRG --image booksyncrepo.azurecr.io/api-booksync:<IMAGE_TAG_PRECEDENT>
   ```
3. Vérifier le health check sur `/predict/health`.
4. Noter l'incident et la version restaurée dans le journal d'exploitation.

## 3. Gestion des erreurs de déploiement

- Surveiller les alertes Prometheus et les notifications CI/CD.
- En cas d'échec, déclencher le rollback et informer l'équipe.
- Documenter chaque incident et la solution apportée.

---

**Bonnes pratiques** :
- Toujours tester le health check après rollback.
- Garder un historique des images déployées et restaurées.
- Automatiser le déclenchement du rollback dans le pipeline CI/CD si possible.

---

# Ce fichier est à supprimer (voir docs/_A_SUPPRIMER.txt)
