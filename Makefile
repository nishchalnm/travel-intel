.PHONY: env run dbt-silver dbt-gold dbt-all

env:
	export MOTHERDUCK_TOKEN=$(shell grep MOTHERDUCK_TOKEN .env | cut -d '=' -f2) && \
	source .venv/bin/activate

token:
	$(eval export MOTHERDUCK_TOKEN=$(shell grep MOTHERDUCK_TOKEN .env | cut -d '=' -f2))
	@echo "MOTHERDUCK_TOKEN loaded"

run:
	docker compose up -d

down:
	docker compose down

dbt-silver:
	cd transform/dbt_project && \
	export MOTHERDUCK_TOKEN=$(shell grep MOTHERDUCK_TOKEN ../.env | cut -d '=' -f2) && \
	dbt run --select silver_weather silver_pois silver_news silver_country_info

dbt-gold:
	cd transform/dbt_project && \
	export MOTHERDUCK_TOKEN=$(shell grep MOTHERDUCK_TOKEN ../.env | cut -d '=' -f2) && \
	dbt run --select gold_city_intelligence

dbt-all:
	cd transform/dbt_project && \
	export MOTHERDUCK_TOKEN=$(shell grep MOTHERDUCK_TOKEN ../.env | cut -d '=' -f2) && \
	dbt run