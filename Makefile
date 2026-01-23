.PHONY: fix-code tests pre-comit

VENV_PYTHON = .venv/bin/python
SRC = app tests


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
	docker buildx build --no-cache --platform linux/amd64 -t api-booksync:latest .
	docker tag api-booksync booksyncrepo.azurecr.io/api-booksync
	docker push booksyncrepo.azurecr.io/api-booksync
	az containerapp update \
	  --name api-booksync \
	  --resource-group vplatevoetRG \
	  --image booksyncrepo.azurecr.io/api-booksync:latest
