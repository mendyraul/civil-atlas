from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router, router as world_router
from app.core.config import settings
from app.services.atlas import get_data_version

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=settings.app_description,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def healthcheck() -> dict[str, object]:
    return {
        "status": "ok",
        "database": "available",
        "data": get_data_version(),
        "api_version": settings.app_version,
    }


app.include_router(world_router, prefix="/api/v1")
app.include_router(api_router, prefix="/api")
