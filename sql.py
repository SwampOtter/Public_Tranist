import pandas as pd
from sqlalchemy import create_engine

# === CONFIG ===
csv_file = "/Users/swampotter/DataGripProjects/Public Tranist/public_transit_data_us.csv"  # CSV input
table_name = "public_transit_master"  # Desired table name

# PostgreSQL connection settings
db_user = "swampotter"
db_pass = ""
db_host = "localhost"  # Or IP address
db_port = "5432"  # Default PostgreSQL port
db_name = "public_transit"

# === READ CSV ===
df = pd.read_csv(csv_file)

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


# === CREATE DATABASE IF IT DOESN'T EXIST ===
def create_database(db_name, db_user, db_pass, db_host, db_port):
    conn = psycopg2.connect(
        dbname="postgres", user=db_user, password=db_pass, host=db_host, port=db_port
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    # Check if the database already exists
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
    exists = cur.fetchone()

    if not exists:
        print(f"🛠️ Creating database '{db_name}'...")
        cur.execute(f"CREATE DATABASE {db_name}")
    else:
        print(f"✅ Database '{db_name}' already exists.")

    cur.close()
    conn.close()


# === CALL THE FUNCTION ===
create_database(db_name, db_user, db_pass, db_host, db_port)

# === CREATE SQLALCHEMY ENGINE ===
engine = create_engine(
    f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
)

# === WRITE TO SQL ===
df.to_sql(table_name, engine, index=False, if_exists="replace")  # or 'append'

print(f"✅ Loaded '{csv_file}' into table '{table_name}' ({len(df)} rows)")
