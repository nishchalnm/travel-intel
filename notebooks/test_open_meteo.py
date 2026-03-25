import sys
sys.path.insert(0, ".")

from ingestion.sources.open_meteo import OpenMeteoExtractor

extractor = OpenMeteoExtractor()

result = extractor.extract(
    city_slug="bangkok",
    display_name="Bangkok",
    lat=13.7563,
    lon=100.5018
)

for row in result:
    print(row)