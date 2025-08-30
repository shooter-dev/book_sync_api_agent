push-azur:
	docker buildx build --no-cache --platform linux/amd64 -t api-booksync:latest .
	docker tag api-booksync booksyncrepo.azurecr.io/api-booksync
	docker push booksyncrepo.azurecr.io/api-booksync
	az containerapp update \
	  --name api-booksync \
	  --resource-group vplatevoetRG \
	  --image booksyncrepo.azurecr.io/api-booksync:latest
