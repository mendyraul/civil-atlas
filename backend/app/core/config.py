from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "Civil Atlas API"
    app_version: str = "0.1.0"
    app_description: str = (
        "Backend API for the Civil Atlas historical civilization MVP."
    )
    cors_origins: list[str] = ["http://localhost:3000"]


settings = Settings()
