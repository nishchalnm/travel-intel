import sys
sys.path.insert(0, ".")

import yaml
from dotenv import load_dotenv
from loguru import logger

from ingestion.sources.restcountries import RestCountriesExtractor
from ingestion.sources.open_meteo import OpenMeteoExtractor
from ingestion.sources.opentripmap import OpenTripMapExtractor
from ingestion.sources.gnews import GNewsExtractor
from ingestion.loaders.motherduck import MotherDuckLoader

load_dotenv()


def load_cities() -> dict:
    with open("config/cities.yml") as f:
        return yaml.safe_load(f)["cities"]


def run_pipeline():
    logger.info("=== Travel Intel Pipeline Starting ===")

    cities = load_cities()
    loader = MotherDuckLoader()

    extractors = [
        ("restcountries", RestCountriesExtractor(),  "bronze", "restcountries"),
        ("open_meteo",    OpenMeteoExtractor(),       "bronze", "weather"),
        ("opentripmap",   OpenTripMapExtractor(),     "bronze", "pois"),
        ("gnews",         GNewsExtractor(),           "bronze", "news"),
    ]

    for source_name, extractor, schema, table in extractors:
        all_records = []

        for city_slug, city_config in cities.items():
            try:
                records = extractor.extract(
                    city_slug=city_slug,
                    **city_config      # passes display_name, lat, lon, country etc
                )
                all_records.extend(records)
                loader.log_pipeline_run(
                    source=source_name,
                    city_slug=city_slug,
                    rows_extracted=len(records),
                    status="success"
                )

            except Exception as e:
                logger.error(
                    f"[pipeline] Failed {source_name} for {city_slug}: {e}"
                )
                loader.log_pipeline_run(
                    source=source_name,
                    city_slug=city_slug,
                    rows_extracted=0,
                    status="failed",
                    error=str(e)
                )

        # Load all cities for this source in one shot
        loader.load(all_records, schema=schema, table=table)

    logger.info("=== Pipeline Complete ===")


if __name__ == "__main__":
    run_pipeline()