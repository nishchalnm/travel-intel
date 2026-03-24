import httpx
from pydantic import BaseModel
from loguru import logger
from ingestion.sources.base import BaseExtractor


class CountryInfo(BaseModel):
    city_slug: str
    display_name: str
    country_name: str
    country_code: str
    region: str
    subregion: str
    capital: str | None
    population: int
    currencies: str        # e.g. "USD, EUR"
    languages: str         # e.g. "English, French"
    timezones: str


class RestCountriesExtractor(BaseExtractor):
    source_name = "restcountries"
    BASE_URL = "https://restcountries.com/v3.1/alpha/{code}"

    def _fetch(self, city_slug: str, display_name: str,
               country: str, **kwargs) -> list[dict]:
        url = self.BASE_URL.format(code=country.lower())
        logger.debug(f"[restcountries] GET {url}")

        response = httpx.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()[0]

        validated = CountryInfo(
            city_slug=city_slug,
            display_name=display_name,
            country_name=data.get("name", {}).get("common", ""),
            country_code=country,
            region=data.get("region", ""),
            subregion=data.get("subregion", ""),
            capital=data.get("capital", [None])[0],
            population=data.get("population", 0),
            currencies=", ".join(data.get("currencies", {}).keys()),
            languages=", ".join(data.get("languages", {}).values()),
            timezones=", ".join(data.get("timezones", []))
        )
        return [validated.model_dump()]