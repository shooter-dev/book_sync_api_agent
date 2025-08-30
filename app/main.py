from fastapi import FastAPI
from .routes.product_routes import router as products_router
from .routes.predict_routes import router as predict_router

app = FastAPI(
    title="Book Sync API Agent",
    description="API pour la synchronisation de livres et la recherche vectorielle",
    version="1.0.0"
)

app.include_router(router=products_router)
app.include_router(router=predict_router)