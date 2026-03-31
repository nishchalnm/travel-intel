FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir duckdb==1.5.1 --force-reinstall

COPY . .

CMD ["python", "-m", "orchestration.flows.daily_pipeline"]