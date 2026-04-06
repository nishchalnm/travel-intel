import sys
sys.path.insert(0, ".")

import os
import duckdb
import ollama
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

app = FastAPI(title="Travel Intel API")

CITIES = {
    "new_york":  "New York City",
    "london":    "London",
    "tokyo":     "Tokyo",
    "barcelona": "Barcelona",
    "bangkok":   "Bangkok",
}


def get_connection():
    token = os.getenv("MOTHERDUCK_TOKEN")
    return duckdb.connect(f"md:travel_intel?motherduck_token={token}")


def get_city_context(city_slug: str) -> dict | None:
    conn = get_connection()
    result = conn.execute("""
        SELECT * FROM gold.gold_city_intelligence
        WHERE city_slug = ?
    """, [city_slug]).fetchdf()
    conn.close()
    if result.empty:
        return None
    return result.iloc[0].to_dict()


def build_prompt(context: dict, question: str) -> str:
    return f"""You are a travel intelligence assistant. Answer the user's question using only the data provided below. Be concise and specific. Do not make up information not present in the data.

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

RECENT NEWS ({context['article_count']} articles):
- Positive: {context['positive_count']} | Negative: {context['negative_count']} | Neutral: {context['neutral_count']}
- Headlines: {context['headlines_concat']}
- Note: sentiment is keyword-based, use headlines as primary signal.

USER QUESTION: {question}

Answer:"""


class AskRequest(BaseModel):
    city_slug: str
    question: str


class AskResponse(BaseModel):
    city: str
    question: str
    answer: str


@app.get("/cities")
def list_cities():
    return {"cities": [
        {"slug": slug, "name": name}
        for slug, name in CITIES.items()
    ]}


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    if request.city_slug not in CITIES:
        raise HTTPException(status_code=400, detail=f"Unknown city: {request.city_slug}")

    context = get_city_context(request.city_slug)
    if not context:
        raise HTTPException(status_code=404, detail=f"No data found for: {request.city_slug}")

    prompt = build_prompt(context, request.question)

    try:
        response = ollama.chat(
            model="llama3.2",
            messages=[{"role": "user", "content": prompt}]
        )
        answer = response["message"]["content"]
    except Exception as e:
        logger.error(f"Ollama error: {e}")
        raise HTTPException(status_code=503, detail="LLM unavailable — is Ollama running?")

    return AskResponse(
        city=CITIES[request.city_slug],
        question=request.question,
        answer=answer
    )


@app.get("/")
def root():
    return FileResponse("api/static/index.html")


app.mount("/static", StaticFiles(directory="api/static"), name="static")