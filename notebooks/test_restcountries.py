import sys
sys.path.insert(0, ".")

from ingestion.sources.restcountries import RestCountriesExtractor

extractor = RestCountriesExtractor()

result = extractor.extract(
    city_slug="new-york-city",
    display_name="New York City",
    country="US"
)

print(result)