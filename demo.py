"""Viva demo: referential-integrity violation + three queries."""
import psycopg2
from psycopg2 import errors

from db import get_connection


def show(cur, title, sql, params=None):
    print(f"\n--- {title} ---")
    print(sql.strip())
    cur.execute(sql, params)
    cols = [d[0] for d in cur.description]
    print(" | ".join(cols))
    for row in cur.fetchall():
        print(" | ".join(str(v) for v in row))


def integrity_demo(conn):
    print("=== Referential integrity demo ===")
    bad_isbn = "0000000000000"  # not in book
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO book_copy (isbn, barcode_no, status) VALUES (%s, %s, %s)",
                (bad_isbn, 1, "available"),
            )
        conn.commit()
        print("UNEXPECTED: insert succeeded")
    except errors.ForeignKeyViolation as e:
        conn.rollback()
        print("Insert rejected (ForeignKeyViolation):")
        print(" ", str(e).strip().replace("\n", "\n  "))


def queries_demo(conn):
    print("\n=== Demo queries ===")
    with conn.cursor() as cur:
        # title/price live in book, publisher name lives in publisher -> JOIN needed
        show(cur, "1. JOIN: books with their publisher",
             """SELECT b.title, b.price, p.name AS publisher
                FROM book b JOIN publisher p ON p.publisher_id = b.publisher_id
                ORDER BY b.title""")
        # isbn and the rows to count are both in book_copy -> no join needed
        show(cur, "2. Aggregate: copies per book (book_copy only, grouped by isbn)",
             """SELECT isbn, COUNT(*) AS copies
                FROM book_copy GROUP BY isbn ORDER BY copies DESC, isbn""")
        # category and price are both in book -> no join needed
        show(cur, "3. Filter: Databases books costing more than 80",
             """SELECT title, category, price FROM book
                WHERE category = %s AND price > %s""", ("Databases", 80))


if __name__ == "__main__":
    with get_connection() as conn:
        integrity_demo(conn)
        queries_demo(conn)
