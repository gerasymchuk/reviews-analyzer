from pydantic import BaseModel
from app.models.review import Review, AppInsights
from app.models.metrics import MetricsResult


class CollectResponse(BaseModel):
    app_id: str
    total: int
    reviews: list[Review]

class AnalysisResponse(BaseModel):
    app_id: str
    metrics: MetricsResult
    insights: AppInsights