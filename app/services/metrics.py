from collections import Counter
from app.models.review import Review, SentimentResult, SentimentLabel
from app.models.metrics import MetricsResult, RatingDistribution

def _calc_avg_rating(reviews: list[Review]) -> float:
    if not reviews:
        return 0.0
    total = len(reviews)
    return sum(r.rating for r in reviews) / total

def _calc_rating_distribution(reviews: list[Review]) -> list[RatingDistribution]:
    total = len(reviews)
    rating_counts = Counter(r.rating for r in reviews)
    return [
        RatingDistribution(
            star=star,
            count=rating_counts.get(star, 0),
            percentage=round(rating_counts.get(star, 0) / total * 100, 1) if total else 0.0)
        for star in range(5, 0, -1)
    ]

def _calc_sentiment_distribution(sentiments: list[SentimentResult]) -> dict[SentimentLabel, int]:
    sentiment_counts: dict[SentimentLabel, int] = {
        label: 0 for label in SentimentLabel
    }
    for s in sentiments:
        sentiment_counts[s.sentiment] += 1

    return sentiment_counts

def get_metrics(reviews: list[Review], sentiments: list[SentimentResult]) -> MetricsResult:
    return MetricsResult(
        total_reviews=len(reviews),
        average_rating=round(_calc_avg_rating(reviews), 2),
        rating_distribution=_calc_rating_distribution(reviews),
        sentiment_distribution=_calc_sentiment_distribution(sentiments)
    )