import httpx
import os
from pydantic import BaseModel
from loguru import logger
from ingestion.sources.base import BaseExtractor


class POI(BaseModel):
    city_slug: str
    display_name: str
    poi_name: str
    category: str
    kinds: str              # comma-separated tags e.g. "museums,cultural"
    rating: float | None
    lat: float
    lon: float


class OpenTripMapExtractor(BaseExtractor):
    source_name = "opentripmap"
    BASE_URL = "https://api.opentripmap.com/0.1/en/places"

    def __init__(self):
        self.api_key = os.getenv("OPENTRIPMAP_API_KEY")
        if not self.api_key:
            raise ValueError("OPENTRIPMAP_API_KEY not set in environment")

    def _fetch(self, city_slug: str, display_name: str,
               lat: float, lon: float, **kwargs) -> list[dict]:

        # Step 1 — get top POIs within 10km radius of city center
        params = {
            "apikey": self.api_key,
            "lat": lat,
            "lon": lon,
            "radius": 10000,
            "limit": 20,
            "rate": 3,
            "kinds": "interesting_places,tourist_facilities,accomodations",
            "format": "json"
        }

        logger.debug(f"[opentripmap] Fetching POIs for {display_name}")
        response = httpx.get(
            f"{self.BASE_URL}/radius",
            params=params,
            timeout=15
        )
        response.raise_for_status()
        places = response.json()

        if not places:
            logger.warning(f"[opentripmap] No POIs returned for {display_name}")
            return []

        # Step 2 — enrich each POI with detail call
        records = []
        for place in places:
            xid = place.get("xid")
            if not xid:
                continue
            detail = self._get_detail(xid)
            if not detail:
                continue

            poi = POI(
                city_slug=city_slug,
                display_name=display_name,
                poi_name=detail.get("name") or place.get("name", "Unknown"),
                category=detail.get("kinds", "").split(",")[0],
                kinds=detail.get("kinds", ""),
                rating=place.get("rate"),
                lat=place.get("point", {}).get("lat", lat),
                lon=place.get("point", {}).get("lon", lon),
            )
            records.append(poi.model_dump())

        return records

    def _get_detail(self, xid: str) -> dict | None:
        try:
            response = httpx.get(
                f"{self.BASE_URL}/xid/{xid}",
                params={"apikey": self.api_key},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning(f"[opentripmap] Detail fetch failed for {xid}: {e}")
            return None