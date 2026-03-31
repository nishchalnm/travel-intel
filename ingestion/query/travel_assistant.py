import duckdb
import os
import ollama
from dotenv import load_dotenv

load_dotenv()

def get_city_context(city_slug: str) -> dict | None:
    token = os.getenv("MOTHERDUCK_TOKEN")
    conn = duckdb.connect(f"md:travel_intel?motherduck_token={token}")
    result = conn.execute("""
        SELECT * FROM gold.gold_city_intelligence
        WHERE city_slug = ?
    """, [city_slug]).fetchdf()
    conn.close()
    if result.empty:
        return None
    return result.iloc[0].to_dict()

def build_prompt(context: dict, question: str) -> str:
    return f"""You are a travel intelligence assistant. Answer the user's question using only the data provided below. Be concise and specific.

CITY DATA:
- City: {context['display_name']} ({context['country_name']}, {context['region']})
- Currency: {context['currencies']} | Language: {context['languages']} | Timezone: {context['primary_timezone']}
- Population: {context['population']:,}

WEATHER (next 7 days):
- Avg high: {context['avg_temp_max_c']}°C | Avg low: {context['avg_temp_min_c']}°C
- Rainy days: {context['rainy_days']} out of 7 | Total rainfall: {context['total_precipitation_mm']}mm
- Avg wind: {context['avg_windspeed_kmh']} km/h

TOP ATTRACTIONS:
{context['top_pois']}

RECENT NEWS SENTIMENT ({context['article_count']} articles):
- Positive: {context['positive_count']} | Negative: {context['negative_count']} | Neutral: {context['neutral_count']}
- Recent headlines: {context['headlines_concat']}


USER QUESTION: {question}

Answer:"""

def ask(city_slug: str, question: str):
    context = get_city_context(city_slug)
    if not context:
        print(f"No data found for city: {city_slug}")
        return
    prompt = build_prompt(context, question)
    response = ollama.chat(
        model="llama3.2",
        messages=[{"role": "user", "content": prompt}]
    )
    print(f"\n[{context['display_name']}] {question}")
    print("-" * 60)
    print(response["message"]["content"])

if __name__ == "__main__":
    ask("bangkok", "Should I visit Bangkok this week?")
    ask("barcelona", "Is Barcelona safe to travel to right now?")
    ask("london",   "What's the travel situation in London?")