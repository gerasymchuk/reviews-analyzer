from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.response import AnalysisResponse, CollectResponse
from app.models.review import Review
from app.services.scraper import scrape_reviews, ScrapeRequest
from app.services.preprocess import preprocess_reviews
from app.services.analyzer import analyze_reviews
from app.services.metrics import get_metrics
import httpx
import csv
import io


router = APIRouter()

async def _scrape_or_raise(request: ScrapeRequest) -> list[Review]:
    try:
        reviews = await scrape_reviews(request)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f'App Store returned {e.response.status_code}')
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail='Failed to connect to App Store')

    if not reviews:
        raise HTTPException(status_code=404, detail=f'No reviews found for app {request.app_id}')

    return reviews

@router.post("/collect")
async def collect(request: ScrapeRequest) -> CollectResponse:
    reviews = await _scrape_or_raise(request)

    return CollectResponse(
        app_id=request.app_id,
        total=len(reviews),
        reviews=reviews
    )

@router.post("/analyse")
async def analyze(request: ScrapeRequest) -> AnalysisResponse:
    reviews = await _scrape_or_raise(request)
    preprocessed_reviews = preprocess_reviews(reviews)

    try:
        analysis = await analyze_reviews(preprocessed_reviews)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Analysis failed: {type(e).__name__}: {e}")

    metrics = get_metrics(preprocessed_reviews, analysis.sentiments)

    return AnalysisResponse(
        app_id=request.app_id,
        metrics=metrics,
        insights=analysis.insights
    )

@router.post("/download", response_class=StreamingResponse)
async def download(request: ScrapeRequest) -> StreamingResponse:
    reviews = await _scrape_or_raise(request)

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=["title", "content", "rating"])
    writer.writeheader()
    for review in reviews:
        writer.writerow(review.model_dump())

    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=reviews.csv"},
    )

