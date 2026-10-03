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


def delete_rules_demo(conn):
    print("\n=== Delete rules demo (each runs in a transaction that is rolled back) ===")
    with conn.cursor() as cur:
        try:
            cur.execute("DELETE FROM publisher WHERE publisher_id = %s", (1,))
            print("UNEXPECTED: publisher deleted")
        except errors.ForeignKeyViolation as e:
            print("book->publisher (no cascade): delete publisher 1 rejected:")
            print(" ", str(e).splitlines()[1] if "\n" in str(e) else str(e))
        conn.rollback()
        isbn = "9780133970777"
        cur.execute("SELECT COUNT(*) FROM book_copy WHERE isbn = %s", (isbn,))
        before = cur.fetchone()[0]
        cur.execute("DELETE FROM book WHERE isbn = %s", (isbn,))
        cur.execute("SELECT COUNT(*) FROM book_copy WHERE isbn = %s", (isbn,))
        after = cur.fetchone()[0]
        print(f"book_copy->book (CASCADE): deleting book {isbn}: copies {before} -> {after}")
        conn.rollback()
        try:
            cur.execute("INSERT INTO book_copy VALUES (%s, %s, %s)", (isbn, 1, "available"))
            print("UNEXPECTED: duplicate composite key accepted")
        except errors.UniqueViolation:
            print("Composite PK: duplicate (isbn, barcode_no) rejected")
        conn.rollback()


def queries_demo(conn):
    print("\n=== Demo queries ===")
    with conn.cursor() as cur:
        # title/price live in book, publisher name lives in publisher -> JOIN needed
        show(cur, "1. JOIN: books with their publisher",
             """SELECT b.title, b.price, p.name AS publisher
                FROM book b JOIN publisher p ON p.publisher_id = b.publisher_id
                ORDER BY b.title""")
        # copy counts come from book_copy, but title lives in book -> JOIN needed
        show(cur, "2. Aggregate: copies per book (with title)",
             """SELECT b.isbn, b.title, COUNT(c.barcode_no) AS copies
                FROM book b JOIN book_copy c ON c.isbn = b.isbn
                GROUP BY b.isbn, b.title ORDER BY copies DESC, b.title""")
        # category and price are both in book -> no join needed
        show(cur, "3. Filter: Databases books costing more than 80",
             """SELECT title, category, price FROM book
                WHERE category = %s AND price > %s""", ("Databases", 80))


if __name__ == "__main__":
    with get_connection() as conn:
        integrity_demo(conn)
        delete_rules_demo(conn)
        queries_demo(conn)
