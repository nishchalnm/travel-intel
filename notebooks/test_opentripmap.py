import sys
sys.path.insert(0, ".")

from dotenv import load_dotenv
load_dotenv()

from ingestion.sources.opentripmap import OpenTripMapExtractor

extractor = OpenTripMapExtractor()

result = extractor.extract(
    city_slug="tokyo",
    display_name="Tokyo",
    lat=35.6762,
    lon=139.6503
)

print(f"\nTotal POIs fetched: {len(result)}\n")
for row in result[:5]:     # print first 5 only
    print(row)