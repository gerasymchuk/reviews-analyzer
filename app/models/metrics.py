from pydantic import BaseModel, Field
from app.models.review import SentimentLabel

class RatingDistribution(BaseModel):
    star: int = Field(..., ge=1, le=5)
    count: int
    percentage: float

class MetricsResult(BaseModel):
    total_reviews: int
    average_rating: float
    rating_distribution: list[RatingDistribution]
    sentiment_distribution: dict[SentimentLabel, int]