from fastapi import FastAPI
from .routes.predict_routes import router as predict_router

app = FastAPI(
    title="Book Sync API Agent",
    description="API pour la recommandation personnalisée de mangas et livres",
    version="1.0.0"
)

app.include_router(router=predict_router)