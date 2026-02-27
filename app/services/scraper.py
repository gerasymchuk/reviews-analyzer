import asyncio
import httpx
import logging
import random
from app.models.review import Review
from app.models.request import ScrapeRequest

logger = logging.getLogger(__name__)

REVIEWS_URL = "https://itunes.apple.com/{country}/rss/customerreviews/id={app_id}/page={page}/sortby=mostrecent/json"
PER_PAGE = 50

def sample_reviews(reviews: list[Review], k: int) -> list[Review]:
    if len(reviews) <= k:
        return reviews
    return random.sample(reviews, k=k)

async def fetch_page(client: httpx.AsyncClient, app_id: str, page: int, country: str) -> list[Review]:
    url = REVIEWS_URL.format(country=country, app_id=app_id, page=page)
    response = await client.get(url)
    response.raise_for_status()
    data = response.json()

    entries = data.get("feed", {}).get("entry", [])
    if not entries:
        logger.debug("Page %d: no entries", page)
        return []

    return [
        Review(
            title = entry["title"]["label"],
            content = entry["content"]["label"],
            rating = int(entry["im:rating"]["label"])
        )
        for entry in entries
        if "im:rating" in entry
    ]

async def scrape_reviews(request: ScrapeRequest) -> list[Review]:
    total_pages = request.max_reviews // PER_PAGE

    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = [
            fetch_page(client, request.app_id, page=p, country=request.country)
            for p in range(1, total_pages + 1)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    reviews: list[Review] = []
    for i, result in enumerate(results, start=1):
        if isinstance(result, Exception):
            logger.warning("Page %d failed: %s", i, result)
            break
        if not result:
            logger.info("Page %d empty, stopping", i)
            break
        reviews.extend(result)
        if len(result) < PER_PAGE:
            logger.info("Page %d has %d reviews (< %d), last page", i, len(result), PER_PAGE)
            break
    logger.info("Scraped %d reviews total for app %s", len(reviews), request.app_id)

    reviews = sample_reviews(reviews, k = request.sample_size)

    return reviews