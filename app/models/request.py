from pydantic import BaseModel, Field, field_validator
from app.core.config import settings

class ScrapeRequest(BaseModel):
    app_id: str = Field(..., description="Apple App Store app ID, e.g. '284882215' or 'id284882215'")
    country: str = Field(default=settings.default_country,description="Two-letter country code")
    max_reviews: int = Field(default=settings.max_reviews, ge=50, le=settings.max_reviews)

    @field_validator("app_id")
    @classmethod
    def normalize_app_id(cls, v: str) -> str:
        cleaned = v.strip().removeprefix("id")
        if not cleaned.isdigit():
            raise ValueError(f"Invalid app ID: '{v}'. Expected numeric ID like '284882215' or 'id284882215'")
        return cleaned