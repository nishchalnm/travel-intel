import httpx
import os
from datetime import datetime, timedelta
from pydantic import BaseModel
from loguru import logger
from ingestion.sources.base import BaseExtractor


class NewsArticle(BaseModel):
    city_slug: str
    display_name: str
    title: str
    description: str | None
    source_name: str
    published_at: str
    url: str
    sentiment_hint: str     # "positive", "negative", "neutral" — simple keyword check


NEGATIVE_KEYWORDS = {
    "attack", "crime", "murder", "protest", "flood", "earthquake",
    "storm", "terror", "explosion", "riot", "warning", "danger",
    "scam", "fraud", "death", "killed", "arrested"
}

POSITIVE_KEYWORDS = {
    "festival", "opening", "celebration", "award", "tourism",
    "record", "growth", "beautiful", "safe", "improved"
}


def _infer_sentiment(text: str) -> str:
    lowered = text.lower()
    if any(k in lowered for k in NEGATIVE_KEYWORDS):
        return "negative"
    if any(k in lowered for k in POSITIVE_KEYWORDS):
        return "positive"
    return "neutral"


class GNewsExtractor(BaseExtractor):
    source_name = "gnews"
    BASE_URL = "https://gnews.io/api/v4/search"

    def __init__(self):
        self.api_key = os.getenv("GNEWS_API_KEY")
        if not self.api_key:
            raise ValueError("GNEWS_API_KEY not set in environment")

    def _fetch(self, city_slug: str, display_name: str, **kwargs) -> list[dict]:
        # Search news from last 7 days for this city
        from_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")

        params = {
            "q": f'"{display_name}" travel OR tourism OR safety',
            "lang": "en",
            "max": 10,
            "from": from_date,
            "apikey": self.api_key
        }

        logger.debug(f"[gnews] Searching news for {display_name}")
        response = httpx.get(self.BASE_URL, params=params, timeout=15)
        response.raise_for_status()

        articles = response.json().get("articles", [])

        if not articles:
            logger.warning(f"[gnews] No articles found for {display_name}")
            return []

        records = []
        for article in articles:
            title = article.get("title", "")
            description = article.get("description", "")
            text_for_sentiment = f"{title} {description}"

            record = NewsArticle(
                city_slug=city_slug,
                display_name=display_name,
                title=title,
                description=description,
                source_name=article.get("source", {}).get("name", "Unknown"),
                published_at=article.get("publishedAt", ""),
                url=article.get("url", ""),
                sentiment_hint=_infer_sentiment(text_for_sentiment)
            )
            records.append(record.model_dump())

        return records