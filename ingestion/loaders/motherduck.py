import duckdb
import os
import pandas as pd
from loguru import logger


class MotherDuckLoader:
    """
    Handles all writes to MotherDuck.
    One method per concern: connect, create schema, load, log run.
    """

    def __init__(self, database: str = "travel_intel"):
        token = os.getenv("MOTHERDUCK_TOKEN")
        if not token:
            raise ValueError("MOTHERDUCK_TOKEN not set in environment")
        
        # Connect to default MotherDuck first (no specific database)
        base_conn = duckdb.connect(f"md:?motherduck_token={token}")
        
        # Create the database if it doesn't exist
        base_conn.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
        base_conn.close()
        
        # Now connect to our specific database
        self.conn = duckdb.connect(f"md:{database}?motherduck_token={token}")
        self.database = database
        logger.info(f"[motherduck] Connected to {database}")

    def ensure_schema(self, schema: str):
        self.conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
        logger.debug(f"[motherduck] Schema ready: {schema}")

    def load(
        self,
        records: list[dict],
        schema: str,
        table: str,
        mode: str = "replace"   # "replace" for daily full reload, "append" for incremental
    ):
        if not records:
            logger.warning(f"[motherduck] No records to load into {schema}.{table}")
            return

        df = pd.DataFrame(records)
        self.ensure_schema(schema)

        full_table = f"{schema}.{table}"

        if mode == "replace":
            self.conn.execute(f"DROP TABLE IF EXISTS {full_table}")
            self.conn.execute(
                f"CREATE TABLE {full_table} AS SELECT * FROM df"
            )
        elif mode == "append":
            self.conn.execute(
                f"CREATE TABLE IF NOT EXISTS {full_table} AS "
                f"SELECT * FROM df WHERE 1=0"   # empty table with same schema
            )
            self.conn.execute(f"INSERT INTO {full_table} SELECT * FROM df")

        row_count = self.conn.execute(
            f"SELECT COUNT(*) FROM {full_table}"
        ).fetchone()[0]

        logger.info(
            f"[motherduck] Loaded {len(records)} rows → "
            f"{full_table} (total rows: {row_count})"
        )

    def log_pipeline_run(
        self,
        source: str,
        city_slug: str,
        rows_extracted: int,
        status: str,
        error: str | None = None
    ):
        """
        Every pipeline run gets logged — this is your run history table.
        Critical for production credibility.
        """
        self.ensure_schema("ops")
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS ops.pipeline_runs (
                run_id        VARCHAR DEFAULT gen_random_uuid()::VARCHAR,
                source        VARCHAR,
                city_slug     VARCHAR,
                rows_extracted INTEGER,
                status        VARCHAR,
                error         VARCHAR,
                ran_at        TIMESTAMP DEFAULT now()
            )
        """)
        self.conn.execute("""
            INSERT INTO ops.pipeline_runs
                (source, city_slug, rows_extracted, status, error)
            VALUES (?, ?, ?, ?, ?)
        """, [source, city_slug, rows_extracted, status, error])