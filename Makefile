.PHONY: fix-code tests pre-comit push-azur rollback rollback-previous rollback-list

VENV_PYTHON = .venv/bin/python
SRC = app tests

# Configuration Azure
REGISTRY = booksyncrepo.azurecr.io
IMAGE = api-booksync
RESOURCE_GROUP = vplatevoetRG
CONTAINER_APP = api-booksync


fix-code:
	@echo "Running code fixes..."
	$(VENV_PYTHON) -m black $(SRC) --line-length=120

	$(VENV_PYTHON) -m isort $(SRC)

	$(VENV_PYTHON) -m ruff check $(SRC) --line-length=120 --fix

tests-code:
	@echo "Checking code..."
	$(VENV_PYTHON) -m black --check $(SRC) --line-length=120

	$(VENV_PYTHON) -m isort --check-only $(SRC)

	$(VENV_PYTHON) -m ruff check $(SRC) --line-length=120

tests:
	@echo "Running tests..."
	$(VENV_PYTHON) -m pytest tests


pre-comit:
	@echo "Running pre-commit checks..."

	make fix-code

	make tests-code

	make tests

push-azur:
	@echo "Build et deploiement vers Azure..."
	docker buildx build --no-cache --platform linux/amd64 -t $(IMAGE):latest .
	docker tag $(IMAGE) $(REGISTRY)/$(IMAGE)
	docker push $(REGISTRY)/$(IMAGE)
	az containerapp update \
	  --name $(CONTAINER_APP) \
	  --resource-group $(RESOURCE_GROUP) \
	  --image $(REGISTRY)/$(IMAGE):latest

# =============================================================================
# Commandes de Rollback
# =============================================================================

rollback-list:
	@echo "Liste des images disponibles dans ACR..."
	@az acr repository show-tags \
		--name booksyncrepo \
		--repository $(IMAGE) \
		--orderby time_desc \
		--top 10 \
		--output table

rollback-current:
	@echo "Image actuellement deployee:"
	@az containerapp show \
		--name $(CONTAINER_APP) \
		--resource-group $(RESOURCE_GROUP) \
		--query "properties.template.containers[0].image" \
		--output tsv

rollback-previous:
	@echo "Rollback vers la version precedente..."
	@./scripts/rollback.sh --previous

rollback:
	@echo "Lancement du script de rollback interactif..."
	@./scripts/rollback.sh

# Rollback vers une version specifique
# Usage: make rollback-to TAG=abc123def456
rollback-to:
ifndef TAG
	$(error TAG n est pas defini. Usage: make rollback-to TAG=<sha_commit>)
endif
	@echo "Rollback vers la version: $(TAG)"
	@./scripts/rollback.sh $(TAG)

# Verification de sante de l'application
health-check:
	@echo "Verification de la sante de l'application..."
	@APP_URL=$$(az containerapp show \
		--name $(CONTAINER_APP) \
		--resource-group $(RESOURCE_GROUP) \
		--query "properties.configuration.ingress.fqdn" \
		--output tsv) && \
	echo "URL: https://$$APP_URL/predict/health" && \
	curl -s -o /dev/null -w "HTTP Code: %{http_code}\n" "https://$$APP_URL/predict/health"
