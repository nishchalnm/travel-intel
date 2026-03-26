import sys
sys.path.insert(0, ".")

from dotenv import load_dotenv
load_dotenv()

from ingestion.sources.gnews import GNewsExtractor

extractor = GNewsExtractor()

result = extractor.extract(
    city_slug="barcelona",
    display_name="Barcelona"
)

print(f"\nTotal articles fetched: {len(result)}\n")
for row in result:
    print(f"{row['published_at'][:10]} | {row['sentiment_hint']:8} | {row['title'][:80]}")