import os

from pydantic import BaseModel


class StorageContract(BaseModel):
    provider: str = "s3_compatible"
    access_key_id: str = "civil-atlas-dev"
    secret_access_key: str = "civil-atlas-dev-secret"
    endpoint: str = "http://localhost:9000"
    public_base_url: str | None = None
    region: str = "us-east-1"
    use_path_style: bool = True
    signed_url_ttl_seconds: int = 900
    raw_bucket: str = "raw-sources"
    normalized_bucket: str = "normalized-sources"
    derived_bucket: str = "derived-tiles"
    exports_bucket: str = "exports"
    raw_prefix: str = "sources"
    normalized_prefix: str = "imports"
    derived_prefix: str = "geometries"
    exports_prefix: str = "exports"


class Settings(BaseModel):
    app_env: str = "development"
    app_name: str = "Civil Atlas API"
    app_version: str = "0.1.0"
    app_description: str = (
        "Backend API for the Civil Atlas historical civilization MVP."
    )
    cors_origins: list[str] = ["http://localhost:3000"]
    database_url: str = "postgresql+psycopg://civil_atlas:civil_atlas@localhost:5432/civil_atlas"
    editorial_api_key: str | None = None
    editor_ui_enabled: bool = False
    storage: StorageContract = StorageContract()


def _bool_from_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _int_from_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _list_from_env(name: str, default: list[str]) -> list[str]:
    value = os.getenv(name)
    if value is None:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


runtime_env = os.getenv("APP_ENV", "development").strip().lower()
database_url = os.getenv("DATABASE_URL")
if runtime_env in {"staging", "production"}:
    required = {
        "DATABASE_URL": database_url,
        "CORS_ORIGINS": os.getenv("CORS_ORIGINS"),
        "EDITORIAL_API_KEY": os.getenv("EDITORIAL_API_KEY"),
        "S3_ACCESS_KEY_ID": os.getenv("S3_ACCESS_KEY_ID"),
        "S3_SECRET_ACCESS_KEY": os.getenv("S3_SECRET_ACCESS_KEY"),
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise RuntimeError(
            f"{runtime_env} configuration is missing required settings: {', '.join(missing)}"
        )


settings = Settings(
    app_env=runtime_env,
    cors_origins=_list_from_env("CORS_ORIGINS", ["http://localhost:3000"]),
    database_url=os.getenv(
        "DATABASE_URL", Settings.model_fields["database_url"].default
    ).replace("postgresql://", "postgresql+psycopg://", 1),
    editorial_api_key=os.getenv("EDITORIAL_API_KEY"),
    editor_ui_enabled=_bool_from_env("EDITOR_UI_ENABLED", False),
    storage=StorageContract(
        access_key_id=os.getenv(
            "S3_ACCESS_KEY_ID", StorageContract.model_fields["access_key_id"].default
        ),
        secret_access_key=os.getenv(
            "S3_SECRET_ACCESS_KEY", StorageContract.model_fields["secret_access_key"].default
        ),
        endpoint=os.getenv("S3_ENDPOINT", StorageContract.model_fields["endpoint"].default),
        public_base_url=os.getenv("S3_PUBLIC_BASE_URL"),
        region=os.getenv("S3_REGION", StorageContract.model_fields["region"].default),
        use_path_style=_bool_from_env("S3_USE_PATH_STYLE", True),
        signed_url_ttl_seconds=_int_from_env("S3_SIGNED_URL_TTL_SECONDS", 900),
        raw_bucket=os.getenv("S3_BUCKET_RAW", StorageContract.model_fields["raw_bucket"].default),
        normalized_bucket=os.getenv(
            "S3_BUCKET_NORMALIZED", StorageContract.model_fields["normalized_bucket"].default
        ),
        derived_bucket=os.getenv(
            "S3_BUCKET_DERIVED", StorageContract.model_fields["derived_bucket"].default
        ),
        exports_bucket=os.getenv(
            "S3_BUCKET_EXPORTS", StorageContract.model_fields["exports_bucket"].default
        ),
        raw_prefix=os.getenv("S3_PREFIX_RAW", StorageContract.model_fields["raw_prefix"].default),
        normalized_prefix=os.getenv(
            "S3_PREFIX_NORMALIZED", StorageContract.model_fields["normalized_prefix"].default
        ),
        derived_prefix=os.getenv(
            "S3_PREFIX_DERIVED", StorageContract.model_fields["derived_prefix"].default
        ),
        exports_prefix=os.getenv(
            "S3_PREFIX_EXPORTS", StorageContract.model_fields["exports_prefix"].default
        ),
    )
)
