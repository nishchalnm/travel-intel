import httpx
from pydantic import BaseModel
from loguru import logger
from ingestion.sources.base import BaseExtractor


class DailyWeather(BaseModel):
    city_slug: str
    display_name: str
    date: str
    temp_max_c: float
    temp_min_c: float
    precipitation_mm: float
    windspeed_max_kmh: float
    weathercode: int
    description: str          # human-readable, derived from weathercode


# WMO weather codes → human readable
# https://open-meteo.com/en/docs#weathervariables
WMO_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 48: "Icy fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail",
}


class OpenMeteoExtractor(BaseExtractor):
    source_name = "open_meteo"
    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    def _fetch(self, city_slug: str, display_name: str,
               lat: float, lon: float, **kwargs) -> list[dict]:

        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": [
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "windspeed_10m_max",
                "weathercode"
            ],
            "timezone": "auto",
            "forecast_days": 7
        }

        logger.debug(f"[open_meteo] GET forecast for {display_name}")
        response = httpx.get(self.BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        daily = data["daily"]
        records = []

        for i, date in enumerate(daily["time"]):
            code = daily["weathercode"][i]
            record = DailyWeather(
                city_slug=city_slug,
                display_name=display_name,
                date=date,
                temp_max_c=daily["temperature_2m_max"][i],
                temp_min_c=daily["temperature_2m_min"][i],
                precipitation_mm=daily["precipitation_sum"][i] or 0.0,
                windspeed_max_kmh=daily["windspeed_10m_max"][i],
                weathercode=code,
                description=WMO_CODES.get(code, "Unknown")
            )
            records.append(record.model_dump())

        return records