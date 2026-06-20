from pathlib import Path
import os
import sys

import psycopg2
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent

SQL_FILES = [
    "setup database.sql",
    "agencies.sql",
    "master_cleanup.sql",
    "organizations.sql",
    "modes.sql",
    "tos.sql",
    "locations_creation.sql",
    "ridership.sql",
    "cost and trips.sql",
]

REQUIRED_MASTER_COLUMNS = {
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

AUTOCOMMIT_COMMANDS = {
    "VACUUM",
    "CREATE DATABASE",
    "DROP DATABASE",
    "ALTER SYSTEM",
}


def connect():
    load_dotenv(PROJECT_ROOT / ".env")

    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "public_transit"),
        user=os.getenv("DB_USER", "transit"),
        password=os.getenv("DB_PASSWORD", ""),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
    )


def iter_sql_statements(sql_text):
    """Yield statements split on semicolons outside quotes/comments."""
    statement = []
    i = 0
    in_single_quote = False
    in_double_quote = False
    in_line_comment = False
    in_block_comment = False
    dollar_quote_tag = None

    while i < len(sql_text):
        char = sql_text[i]
        next_char = sql_text[i + 1] if i + 1 < len(sql_text) else ""

        if in_line_comment:
            statement.append(char)
            if char == "\n":
                in_line_comment = False
            i += 1
            continue

        if in_block_comment:
            statement.append(char)
            if char == "*" and next_char == "/":
                statement.append(next_char)
                in_block_comment = False
                i += 2
            else:
                i += 1
            continue

        if dollar_quote_tag:
            if sql_text.startswith(dollar_quote_tag, i):
                statement.append(dollar_quote_tag)
                i += len(dollar_quote_tag)
                dollar_quote_tag = None
            else:
                statement.append(char)
                i += 1
            continue

        if not in_single_quote and not in_double_quote:
            if char == "-" and next_char == "-":
                statement.extend([char, next_char])
                in_line_comment = True
                i += 2
                continue
            if char == "/" and next_char == "*":
                statement.extend([char, next_char])
                in_block_comment = True
                i += 2
                continue
            if char == "$":
                tag_end = sql_text.find("$", i + 1)
                if tag_end != -1:
                    tag = sql_text[i : tag_end + 1]
                    tag_name = tag[1:-1]
                    if tag_name == "" or tag_name.replace("_", "").isalnum():
                        dollar_quote_tag = tag
                        statement.append(tag)
                        i = tag_end + 1
                        continue

        if char == "'" and not in_double_quote:
            statement.append(char)
            if in_single_quote and next_char == "'":
                statement.append(next_char)
                i += 2
                continue
            in_single_quote = not in_single_quote
            i += 1
            continue

        if char == '"' and not in_single_quote:
            statement.append(char)
            in_double_quote = not in_double_quote
            i += 1
            continue

        if char == ";" and not in_single_quote and not in_double_quote:
            current = "".join(statement).strip()
            if current:
                yield current
            statement = []
            i += 1
            continue

        statement.append(char)
        i += 1

    trailing = "".join(statement).strip()
    if trailing:
        yield trailing


def first_sql_word(statement):
    for line in statement.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        return stripped.split(None, 1)[0].upper()
    return ""


def print_result_rows(cursor):
    if cursor.description is None:
        return

    rows = cursor.fetchall()
    if not rows:
        print("  returned 0 rows")
        return

    column_names = [column.name for column in cursor.description]
    print("  " + "\t".join(column_names))
    for row in rows:
        print("  " + "\t".join("" if value is None else str(value) for value in row))


def validate_master_table(cursor):
    cursor.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'public_transit_master'
        """
    )
    columns = {row[0] for row in cursor.fetchall()}

    if not columns:
        raise RuntimeError(
            "Table public_transit_master was not found. Run "
            "load_curated_master.py before this SQL pipeline."
        )

    missing_columns = sorted(REQUIRED_MASTER_COLUMNS - columns)
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise RuntimeError(
            "Table public_transit_master does not look like the curated wide "
            f"master table. Missing columns: {missing}. Run "
            "load_curated_master.py instead of loading the raw API download."
        )


def execute_statement(conn, cursor, statement):
    command = first_sql_word(statement)
    needs_autocommit = command in AUTOCOMMIT_COMMANDS

    if needs_autocommit:
        conn.commit()
        conn.autocommit = True

    try:
        cursor.execute(statement)
        print_result_rows(cursor)
    finally:
        if needs_autocommit:
            conn.autocommit = False


def run_sql_file(conn, cursor, path):
    if not path.exists():
        raise FileNotFoundError(f"Missing SQL file: {path}")

    print(f"\nRunning {path.name}")
    sql_text = path.read_text()

    for statement in iter_sql_statements(sql_text):
        execute_statement(conn, cursor, statement)

    conn.commit()


def main():
    with connect() as conn:
        with conn.cursor() as cursor:
            validate_master_table(cursor)
            for file_name in SQL_FILES:
                run_sql_file(conn, cursor, PROJECT_ROOT / file_name)

    print("\nSQL pipeline complete.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\nSQL pipeline failed: {exc}", file=sys.stderr)
        sys.exit(1)
