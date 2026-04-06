# ✈️ Travel Intel

A production-grade data engineering pipeline that aggregates daily travel data 
for 5 cities, transforms it through a medallion architecture, and serves 
AI-powered travel recommendations via a local LLM.

**"Should I visit Bangkok this week?"** → answered with live weather, 
news sentiment, top attractions, and country context.

---

## Architecture
```
4 REST APIs (weather, POIs, news, country data)
        ↓
   Python Extractors
   (httpx + Pydantic validation + Tenacity retry)
        ↓
  Bronze Layer — MotherDuck (raw, full reload daily)
        ↓
    dbt transforms
        ↓
  Silver Layer — cleaned, normalized, deduplicated
        ↓
  Gold Layer — 1 denormalized row per city
        ↓
  FastAPI + llama3.2 (Ollama)
        ↓
  Chat Frontend — travel Q&A
```

**Data Sources:**
- [Open-Meteo](https://open-meteo.com/) — 7-day weather forecast (free, no key)
- [OpenTripMap](https://opentripmap.io/) — top 20 POIs per city (free tier)
- [GNews](https://gnews.io/) — travel headlines + keyword sentiment (free tier)
- [RestCountries](https://restcountries.com/) — country metadata (free, no key)

**Cities:** New York · London · Tokyo · Barcelona · Bangkok

---

## Tech Stack

| Layer | Technology |
|---|---|
| Extraction | Python 3.11, httpx, Pydantic v2, Tenacity |
| Warehouse | DuckDB 1.5.1 + MotherDuck (cloud) |
| Transformation | dbt-duckdb 1.9.1 |
| Orchestration | Prefect 2.19.0 + Prefect Cloud |
| LLM | Ollama (llama3.2), local via Docker |
| API | FastAPI 0.111.0 |
| Containerization | Docker + Docker Compose |
| Logging | Loguru |

---

## Data Pipeline

### Bronze Layer (raw)
Full reload on every run — idempotent, safe, auditable.

| Table | Rows | Description |
|---|---|---|
| `bronze.weather` | 35 | 7-day forecast × 5 cities |
| `bronze.pois` | 100 | 20 POIs × 5 cities |
| `bronze.news` | ~25 | 3-10 articles per city |
| `bronze.restcountries` | 5 | 1 row per city |
| `ops.pipeline_runs` | growing | every run logged |

### Silver Layer (cleaned)
dbt models — SQL as code, version controlled, tested.

| Model | Transformation |
|---|---|
| `silver_weather` | Aggregate 7 days → 1 weekly summary per city |
| `silver_pois` | Top 5 by rating, extract primary category |
| `silver_news` | Deduplicate by title, sentiment counts, concat headlines |
| `silver_country_info` | Extract city-level timezone, clean metadata |

### Gold Layer (business-ready)
`gold_city_intelligence` — 1 fully denormalized row per city.
All context the LLM needs in a single `SELECT WHERE city_slug = ?`.
No joins at query time.

---

## Data Quality

25 dbt tests across silver and gold layers:
- `not_null` on all critical columns
- `unique` on all city-level grain keys
```bash
dbt test
# Done. PASS=25 WARN=0 ERROR=0 SKIP=0 TOTAL=25
```

---

## Orchestration

Prefect Cloud schedules the pipeline daily at 6am ET.
Every run is tracked in the Prefect Cloud UI with task-level 
status, duration, and logs.

Pipeline run history is also stored in `ops.pipeline_runs` 
for warehouse-level observability independent of the orchestrator.

---

## LLM Query Layer

The `POST /ask` endpoint:
1. Queries `gold.gold_city_intelligence` for the city context
2. Builds a structured prompt with weather, POIs, news, country data
3. Calls llama3.2 via Ollama
4. Returns a grounded travel recommendation

The LLM is constrained to answer only from provided data — 
no hallucination of facts not present in the gold table.

---

## Running Locally

### Prerequisites
- Python 3.11
- Docker + Docker Compose
- MotherDuck account (free tier)
- Ollama with llama3.2 pulled

### Setup
```bash
git clone https://github.com/nishchalnm/travel-intel
cd travel-intel
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# fill in MOTHERDUCK_TOKEN, OPENTRIPMAP_API_KEY, GNEWS_API_KEY
```

### Run the pipeline
```bash
# Start Ollama
docker compose up ollama -d

# Run extraction + load to bronze
python orchestration/flows/daily_pipeline.py

# Run dbt transforms (silver + gold)
cd transform/dbt_project
export MOTHERDUCK_TOKEN=$(grep MOTHERDUCK_TOKEN ../../.env | cut -d '=' -f2)
dbt run
dbt test
```

### Start the API + frontend
```bash
uvicorn api.main:app --reload --port 8000
# Open http://localhost:8000
```

### Run with Prefect scheduling
```bash
prefect cloud login --key YOUR_PREFECT_API_KEY
prefect agent start -q 'default'
# Pipeline runs automatically at 6am ET
```

---

## Key Architecture Decisions

**Medallion architecture** — bronze stores raw API responses as an 
audit log. Silver normalizes and cleans. Gold is purpose-built for 
the LLM — one row per city, no joins at query time.

**Full reload on bronze** — at this data volume, idempotency matters 
more than incremental complexity. Every run produces the same result 
from the same inputs.

**dbt for transforms** — SQL as code. Version controlled, testable, 
auto-documented. Transformations are reproducible and auditable.

**Pydantic at extraction** — bad data fails loud at the boundary, 
before it reaches the warehouse. Never silently loads garbage.

**Denormalized gold table** — the LLM reads gold repeatedly. 
Pre-computing the join once means no join logic in the prompt, 
faster queries, simpler code.

**generate_schema_name macro** — overrides dbt's default schema 
concatenation behavior. Without it, models land in `silver_silver` 
instead of `silver`. Standard production dbt pattern.

**ops.pipeline_runs** — observability built in from day one. 
Every run logged regardless of success or failure. Query it to 
see row counts, failure rates, and timing trends across any time window.

---

## Project Structure
```
travel-intel/
├── ingestion/
│   ├── sources/          # 4 extractors (restcountries, open_meteo, 
│   │                     #   opentripmap, gnews)
│   ├── loaders/          # MotherDuck loader + pipeline run logging
│   └── query/            # Ollama travel assistant (CLI)
├── transform/
│   └── dbt_project/
│       ├── models/
│       │   ├── silver/   # 4 silver models + schema.yml tests
│       │   └── gold/     # gold_city_intelligence + schema.yml tests
│       └── macros/       # generate_schema_name override
├── orchestration/
│   └── flows/            # Prefect flow + task decorators
├── api/
│   ├── main.py           # FastAPI backend
│   └── static/           # Chat frontend (single HTML file)
├── config/
│   └── cities.yml        # Single source of truth for city list
├── Dockerfile
└── docker-compose.yml
```

---

## Adding a City

1. Add entry to `config/cities.yml`
2. Add timezone mapping in `silver_country_info.sql` CASE statement
3. Run pipeline — all 4 extractors pick it up automatically
4. Run `dbt run && dbt test`

---

*Built with free-tier services only. MotherDuck (10GB), 
Prefect Cloud, GNews, OpenTripMap, Open-Meteo, RestCountries.*