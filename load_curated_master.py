from pathlib import Path
import os
import sys

import pandas as pd
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_CSV_PATH = PROJECT_ROOT / "public_transit_data_us.csv"
TABLE_NAME = "public_transit_master"

REQUIRED_COLUMNS = {
    "NTD ID",
    "Agency",
    "HQ City",
    "HQ State",
    "Organization Type",
    "Service Area Population",
    "Service Area SQ Miles",
    "Avg Trip Length FY",
    "Fares FY",
    "Operating Expenses FY",
    "Avg Cost Per Trip FY",
    "Avg Fares Per Trip FY",
    "Passenger Miles FY",
    "3 Mode",
    "Status",
    "Mode",
    "TOS",
}


def db_settings():
    load_dotenv(PROJECT_ROOT / ".env")

    return {
        "dbname": os.getenv("DB_NAME", "public_transit"),
        "user": os.getenv("DB_USER", "transit"),
        "password": os.getenv("DB_PASSWORD", ""),
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
    }


def create_database_if_missing(settings):
    conn = psycopg2.connect(
        dbname="postgres",
        user=settings["user"],
        password=settings["password"],
        host=settings["host"],
        port=settings["port"],
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (settings["dbname"],),
            )
            if cursor.fetchone():
                print(f"Database '{settings['dbname']}' already exists.")
                return

            print(f"Creating database '{settings['dbname']}'...")
            cursor.execute(
                sql.SQL("CREATE DATABASE {}").format(
                    sql.Identifier(settings["dbname"])
                )
            )
    finally:
        conn.close()


def database_url(settings):
    return URL.create(
        drivername="postgresql+psycopg2",
        username=settings["user"],
        password=settings["password"],
        host=settings["host"],
        port=settings["port"],
        database=settings["dbname"],
    )


def read_curated_csv(path):
    df = pd.read_csv(path, encoding="utf-8-sig")
    df.columns = [str(column).strip() for column in df.columns]

    empty_unnamed_columns = [
        column
        for column in df.columns
        if column.startswith("Unnamed:") and df[column].isna().all()
    ]
    if empty_unnamed_columns:
        df = df.drop(columns=empty_unnamed_columns)

    missing_columns = sorted(REQUIRED_COLUMNS - set(df.columns))
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise ValueError(f"Curated CSV is missing required columns: {missing}")

    return df


def main():
    csv_env = os.getenv("MASTER_CSV")
    csv_path = Path(csv_env).expanduser() if csv_env else DEFAULT_CSV_PATH
    if not csv_path.is_absolute():
        csv_path = PROJECT_ROOT / csv_path

    if not csv_path.exists():
        raise FileNotFoundError(f"Curated CSV not found: {csv_path}")

    settings = db_settings()
    create_database_if_missing(settings)

    df = read_curated_csv(csv_path)
    engine = create_engine(database_url(settings))
    df.to_sql(TABLE_NAME, engine, index=False, if_exists="replace")

    print(f"Loaded '{csv_path}' into '{TABLE_NAME}' ({len(df)} rows).")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\nCurated master load failed: {exc}", file=sys.stderr)
        sys.exit(1)
