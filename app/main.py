from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from .routes.predict_routes import router as predict_router


app = FastAPI(
    title="Book Sync API Agent",
    description="API pour la recommandation personnalisée de mangas et livres",
    version="1.0.0"
)

# Configuration de Prometheus pour le monitoring
instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    excluded_handlers=["/metrics"]
)
instrumentator.instrument(app).expose(app, endpoint="/metrics")

app.include_router(router=predict_router)