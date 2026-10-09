"""Create all tables from schema.sql (drops and recreates them, so it is re-runnable)."""
from pathlib import Path

from db import connection

SCHEMA_FILE = Path(__file__).with_name("schema.sql")


def create_tables(conn):
    with conn.cursor() as cur:
        cur.execute(SCHEMA_FILE.read_text())


if __name__ == "__main__":
    with connection() as conn:
        create_tables(conn)
    print("Tables created: publisher, book, book_copy, library_user, staff, issue")
