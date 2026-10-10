"""Create the tables (schema.sql) and load the sample data (data.sql).

Re-runnable: schema.sql drops and recreates the tables every time.
"""
from pathlib import Path

from db import connection

HERE = Path(__file__).parent


def run_sql_file(conn, name):
    with conn.cursor() as cur:
        cur.execute((HERE / name).read_text())


if __name__ == "__main__":
    with connection() as conn:
        run_sql_file(conn, "schema.sql")
        run_sql_file(conn, "data.sql")
    print("Tables created: publisher, book, book_copy")
    print("Sample data loaded: 6 publishers, 9 books, 15 copies")
