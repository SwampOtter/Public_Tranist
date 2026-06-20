import pandas as pd
from sqlalchemy import create_engine
from pathlib import Path
import requests
from dotenv import load_dotenv
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

# Build a project-local path when the CSV is generated from inputs.
PROJECT_ROOT = Path.cwd()
RAW_DATA_ROOT = PROJECT_ROOT / "data" / "raw"
DEFAULT_LENGTH = 1000

# API info
BASE_URL = "https://data.transportation.gov/api/v3/views/8bui-9xvu/query.json"

# Current source export.
table_name = "public_transit_master"

# Local Postgres connection.
db_user = "transit"
db_pass = ""
db_host = "localhost"
db_port = "5432"
db_name = "public_transit"


def get_api_token() -> str:
    """Load APP token from the local file"""
    load_dotenv()
    api_token = os.getenv("DOTD_API_KEY")

    if not api_token:
        raise ValueError('Missing DOTD_API_TOKEN')

    return api_token


def get_api_key() -> str:
    """Load APP secret token from the local file"""
    load_dotenv()
    app_secret = os.getenv("DOTD_API_KEY")

    if not app_secret:
        raise ValueError('Missing DOTD_SECRET_TOKEN')

    return app_secret


def create_csv_path() -> Path:
    """Create the versioned filename of the raw dataset"""
    timestamp = datetime.now(ZoneInfo('America/Chicago')).strftime('%Y%m%d_%H%M%S')
    file_name = f'dotd_monthly_ridership_{timestamp}.csv'
    output_file_path = RAW_DATA_ROOT / file_name

    return output_file_path


def file_is_recent(folder=RAW_DATA_ROOT, pattern="*.csv", days=60):
    cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)

    candidates = [
        path for path in Path(folder).glob(pattern)
        if path.is_file() and path.stat().st_mtime >= cutoff
    ]

    if not candidates:
        return None

    return max(candidates, key=lambda path: path.stat().st_mtime)


def download_data(base_url=BASE_URL, page_length=DEFAULT_LENGTH):
    """Access the DOTD API and download the raw dataset"""
    # api_token = get_api_token()
    # api_secret = get_api_key()
    recent_file = file_is_recent()


    if recent_file:
        print(f'Using recent existing file: {recent_file}')
        return recent_file

    rows = []
    offset = 0

    try:
        while True:
            params = {
                "$limit":page_length,
                "$offset":offset
            }

            response = requests.get(
                base_url,
                # auth=(api_token, api_secret),
                params=params,
                timeout=60
            )
            response.raise_for_status()

            data = response.json()

            if not data:
                break

            rows.extend(data)
            print(f'Downloaded {len(rows):,} rows...')

            if len(data) < page_length:
                break

            offset += page_length

    except requests.exceptions.RequestException as e:
        print(f'An error occurred during download: {e}')

    if len(rows) > 0:
        df = pd.DataFrame(rows)
        output_path = create_csv_path()
        df.to_csv(output_path)
        print(f'Success! {len(rows)} rows written to {output_path}')

def main():
    download_data()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f'\nERROR: {exc}', file=sys.stderr)
        sys.exit(1)


import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_database(db_name, db_user, db_pass, db_host, db_port):
    # Connect to the maintenance database so the project database can be created.
    conn = psycopg2.connect(
        dbname="postgres", user=db_user, password=db_pass, host=db_host, port=db_port
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
    exists = cur.fetchone()

    if not exists:
        print(f"🛠️ Creating database '{db_name}'...")
        cur.execute(f"CREATE DATABASE {db_name}")
    else:
        print(f"✅ Database '{db_name}' already exists.")

    cur.close()
    conn.close()


create_database(db_name, db_user, db_pass, db_host, db_port)

# SQLAlchemy handles the pandas-to-Postgres write.
engine = create_engine(
    f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
)

file_path = file_is_recent()
file_path = str(file_path)

df = pd.read_csv(file_path)

# Rebuild the master table from the current CSV.
df.to_sql(table_name, engine, index=False, if_exists="replace")

print(f"✅ Loaded '{file_path}' into table '{table_name}' ({len(df)} rows)")

