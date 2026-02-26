from enum import Enum
from pydantic import BaseModel, Field

class SentimentLabel(str, Enum):
    negative = "negative"
    neutral = "neutral"
    positive = "positive"
    mixed = "mixed"

class Priority(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"

class Category(str, Enum):
    bug = "bug"
    performance = "performance"
    ui_ux = "ui_ux"
    feature_request = "feature_request"
    pricing = "pricing"
    stability = "stability"
    security = "security"
    other = "other"

class InsightType(str, Enum):
    complaint = "complaint"
    praise = "praise"
    suggestion = "suggestion"
    question = "question"

class Review(BaseModel):
    title: str = Field(..., description='Title of the review')
    content: str = Field(..., description='Main content of the review')
    rating: int = Field(..., ge=1, le=5, description='Rating score of the review from 1 to 5')

class SentimentResult(BaseModel):
    sentiment: SentimentLabel = Field(..., description="Overall sentiment of the review (negative, neutral, positive, or mixed).")
    summary: str = Field(..., description="Brief summary of the review sentiment")
    topics: list[Category] = Field(..., description="Main topics mentioned in the review")

class Insight(BaseModel):
    category: Category = Field(..., description="Feedback category that best matches the insight")
    priority: Priority = Field(..., description="Priority level based on frequency and user impact")
    insight_type: InsightType = Field(..., description="Type of insight: complaint, praise, suggestion, or question")
    detail: str = Field(..., description="Concise description of the insight")
    mentions_count: int = Field(...,ge=1, description="How many reviews mention this")


class AppInsights(BaseModel):
    overall_sentiment: SentimentLabel = Field(...,description="Dominant sentiment across all reviews")
    insights: list[Insight] = Field(..., description="Key insights extracted from the reviews")
