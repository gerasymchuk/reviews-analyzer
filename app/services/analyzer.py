from pydantic_ai import Agent
from app.core.llm import get_model
from app.models.review import SentimentResult, AppInsights, AnalysisResult
from app.models.review import Review
from app.core.config import settings
import asyncio
import logging

logger = logging.getLogger(__name__)

MODEL_SETTINGS = {"temperature": 0.0}
_model = get_model()

sentiment_agent = Agent(
    model=_model,
    output_type=list[SentimentResult],
    retries=3,
    instructions=
        """
        You are a sentiment classifier for mobile app reviews.
        For each review provided, determine its sentiment:
        positive, neutral, or negative.
        Consider both the review text and the rating.
        Return exactly one result per review, in the same order as the input.
        Include the 0-based index of each review in your response.
        """
)

insights_agent = Agent(
    model=_model,
    output_type=AppInsights,
    retries=3,
    instructions=
        """
        You are an expert product analyst specializing in mobile app feedback.
        You will receive a batch of user reviews (each with a rating and text).

        Your task is to produce structured insights:
        1. **negative_keywords** — extract the most frequent words and short
           phrases that appear across reviews marked with sentiment: negative. Focus on
           concrete nouns and verbs that describe problems (e.g. "crash",
           "battery drain", "slow loading"), not generic words like "bad" or
           "terrible".

        2. **insights** — identify the key feedback themes. For each insight:
           - **topic**: a concise label for the theme (e.g. "App crashes on
             startup", "Subscription pricing concerns").
           - **priority**: high if the issue is mentioned frequently or has
             severe user impact; medium if moderately common; low if rare or
             minor.
           - **recommendation**: a specific, actionable suggestion for the
             development team to address the issue.
           - **keywords**: representative words/phrases from the reviews that
             relate to this theme.
        Group similar complaints into a single insight rather than listing each review separately. Aim for 3–7 distinct insights depending on the diversity of the feedback. Prioritize issues that affect user retention and satisfaction the most.
        """
)

def format_reviews_for_prompt(reviews: list[Review], offset: int = 0) -> str:
    parts = []
    for i, r in enumerate(reviews):
        global_idx = i + offset
        parts.append(f"[{global_idx}] Rating: {r.rating}/5 | Title: {r.title}\n{r.content}")
    return "\n---\n".join(parts)

def chunk_reviews(reviews: list[Review], chunk_size: int) -> list[list[Review]]:
    return [reviews[i:i+chunk_size] for i in range(0, len(reviews), chunk_size)]

async def analyze_sentiment(reviews: list[Review], offset: int = 0) -> list[SentimentResult]:
    result = await sentiment_agent.run(format_reviews_for_prompt(reviews, offset), model_settings=MODEL_SETTINGS)
    return result.output

def format_reviews_for_insights(reviews: list[Review], sentiments: list[SentimentResult]) -> str:
    sentiment_map = {s.review_index: s.sentiment.value for s in sentiments}
    parts = []
    for i, r in enumerate(reviews):
        label = sentiment_map.get(i, "unknown")
        parts.append(
            f"[{i}] Rating: {r.rating}/5 | Sentiment: {label} | Title: {r.title}\n{r.content}"
        )
    return "\n---\n".join(parts)

async def analyze_reviews(reviews: list[Review]) -> AnalysisResult:
    reviews_chunks = chunk_reviews(reviews, settings.chunk_size)

    tasks = []
    offset = 0
    for chunk in reviews_chunks:
        tasks.append(analyze_sentiment(chunk, offset=offset))
        offset += len(chunk)

    chunk_results = await asyncio.gather(*tasks, return_exceptions=True)

    all_sentiments: list[SentimentResult] = []
    for result in chunk_results:
        if isinstance(result, Exception):
            logger.error("Chunk failed: %s", result)
            continue
        all_sentiments.extend(result)

    if not all_sentiments:
        raise RuntimeError("All sentiment chunks failed — cannot proceed to insights")

    if len(all_sentiments) < len(reviews):
        logger.warning("Sentiment coverage: %d/%d reviews", len(all_sentiments), len(reviews))

    prompt = format_reviews_for_insights(reviews, all_sentiments)
    result = await insights_agent.run(prompt, model_settings=MODEL_SETTINGS)
    return AnalysisResult(sentiments=all_sentiments, insights=result.output)
