from enum import Enum
from pydantic import BaseModel, Field

class SentimentLabel(str, Enum):
    negative = "negative"
    neutral = "neutral"
    positive = "positive"

class Priority(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"

class Review(BaseModel):
    title: str = Field(..., description='Title of the review')
    content: str = Field(..., description='Main content of the review')
    rating: int = Field(..., ge=1, le=5, description='Rating score of the review from 1 to 5')

class SentimentResult(BaseModel):
    review_index: int = Field(..., description="0-based index of the review in the provided list")
    sentiment: SentimentLabel = Field(..., description="Overall sentiment of the review (negative, neutral or positive).")

class Insight(BaseModel):
    topic: str = Field(..., description="Feedback topic that best matches the insight")
    priority: Priority = Field(..., description="Priority level based on frequency and user impact")
    recommendation: str = Field(..., description="Actionable suggestion on how to address this")
    keywords: list[str] = Field(default_factory=list, description="Common words/phrases from reviews related to this insight")


class AppInsights(BaseModel):
    negative_keywords: list[str] = Field(default_factory=list, description="Most frequent keywords across negative reviews")
    insights: list[Insight] = Field(..., description="Key insights extracted from the reviews")

class AnalysisResult(BaseModel):
    sentiments: list[SentimentResult]
    insights: AppInsights
