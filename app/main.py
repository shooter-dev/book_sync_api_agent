from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import make_asgi_app

from .routes.predict_routes import router as predict_router
from .metrics.llm_metrics import (
    total_operations,
    total_operations2,
    force_all_metrics
)


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
# instrumentator.instrument(app).expose(app, endpoint="/metrics")  # Désactivé pour éviter double exposition
app.mount("/metrics", make_asgi_app())

app.include_router(router=predict_router)

# Initialisation explicite de toutes les metriques au demarrage
# pour garantir leur visibilite dans Grafana
force_all_metrics()
