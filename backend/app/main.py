from fastapi import FastAPI, HTTPException, Request
from app.api.editor import router as editor_router
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


def _ready_payload() -> dict[str, object]:
    return {
        "status": "ok",
        "database": "available",
        "data": get_data_version(),
        "api_version": settings.app_version,
    }


@app.get("/health/live")
def liveness() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready")
def readiness() -> dict[str, object]:
    try:
        return _ready_payload()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="database is unavailable") from exc


@app.get("/health")
def healthcheck() -> dict[str, object]:
    return readiness()


app.include_router(world_router, prefix="/api/v1")
app.include_router(api_router, prefix="/api")


@app.middleware("http")
async def private_editor_headers(request: Request, call_next):
    response = await call_next(request)
    if request.url.path == "/editor" or request.url.path.startswith("/editor/"):
        response.headers["Cache-Control"] = "no-store"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
    return response


app.include_router(editor_router)
