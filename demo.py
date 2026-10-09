"""Viva demo: integrity checks, delete rules, and the demo queries."""
from textwrap import dedent

from psycopg2 import errors

from db import connection


def show(cur, title, sql, params=None):
    sql = dedent(sql).strip()
    print(f"\n--- {title} ---")
    print(sql)
    cur.execute(sql, params)
    cols = [d[0] for d in cur.description]
    print(" | ".join(cols))
    for row in cur.fetchall():
        print(" | ".join("NULL" if v is None else str(v) for v in row))
    print(f"({cur.rowcount} rows)")


def expect_error(conn, label, error_type, sql, params):
    """Run a statement that must be rejected; print the database's reason."""
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
        print(f"UNEXPECTED: {label} was accepted")
    except error_type as e:
        detail = (e.diag.message_detail or e.diag.message_primary or "").strip()
        print(f"{label}: rejected ({error_type.__name__})")
        print(f"  {detail}")
    finally:
        conn.rollback()


def integrity_demo(conn):
    print("=== Referential integrity demo ===")
    expect_error(conn, "book_copy with a non-existent isbn", errors.ForeignKeyViolation,
                 "INSERT INTO book_copy (isbn, barcode_no, status) VALUES (%s, %s, %s)",
                 ("0000000000000", 1, "available"))
    expect_error(conn, "issue of a copy that does not exist", errors.ForeignKeyViolation,
                 "INSERT INTO issue (issue_id, user_id, staff_id, isbn, barcode_no, due_date)"
                 " VALUES (%s, %s, %s, %s, %s, CURRENT_DATE + 14)",
                 (99, 3, 1, "9780133970777", 9))   # book exists, copy 9 does not
    expect_error(conn, "duplicate (isbn, barcode_no)", errors.UniqueViolation,
                 "INSERT INTO book_copy (isbn, barcode_no, status) VALUES (%s, %s, %s)",
                 ("9780133970777", 1, "available"))
    expect_error(conn, "second open loan of a copy already out", errors.UniqueViolation,
                 "INSERT INTO issue (issue_id, user_id, staff_id, isbn, barcode_no, due_date)"
                 " VALUES (%s, %s, %s, %s, %s, CURRENT_DATE + 14)",
                 (99, 4, 1, "9781492056355", 1))   # copy 1 of Fluent Python is out
    expect_error(conn, "due date before issue date", errors.CheckViolation,
                 "INSERT INTO issue (issue_id, user_id, staff_id, isbn, barcode_no, due_date)"
                 " VALUES (%s, %s, %s, %s, %s, CURRENT_DATE - 1)",
                 (99, 4, 1, "9780134685991", 1))


def delete_rules_demo(conn):
    print("\n=== Delete rules demo (every change is rolled back) ===")
    expect_error(conn, "delete publisher 1 (book->publisher, no cascade)",
                 errors.ForeignKeyViolation,
                 "DELETE FROM publisher WHERE publisher_id = %s", (1,))

    isbn = "9780134685991"  # Effective Java: has copies, never issued
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM book_copy WHERE isbn = %s", (isbn,))
        before = cur.fetchone()[0]
        cur.execute("DELETE FROM book WHERE isbn = %s", (isbn,))
        cur.execute("SELECT COUNT(*) FROM book_copy WHERE isbn = %s", (isbn,))
        after = cur.fetchone()[0]
    conn.rollback()
    print(f"delete book {isbn} (book_copy->book, CASCADE): copies {before} -> {after}")

    # Cascade would remove copies that issue rows point at; issue has no cascade,
    # so the whole delete is refused and loan history is protected.
    expect_error(conn, "delete a book whose copies have loan history",
                 errors.ForeignKeyViolation,
                 "DELETE FROM book WHERE isbn = %s", ("9780133970777",))


def queries_demo(conn):
    print("\n=== Demo queries ===")
    with conn.cursor() as cur:
        # title/price live in book, publisher name in publisher -> JOIN needed
        show(cur, "1. JOIN: books with their publisher", """
            SELECT b.title, b.price, p.name AS publisher
            FROM book b
            JOIN publisher p ON p.publisher_id = b.publisher_id
            ORDER BY p.name, b.title""")

        # copy counts come from book_copy, title lives in book -> JOIN needed.
        # INNER JOIN: books with no copies drop out (see query 5).
        show(cur, "2. Aggregate: copies per book", """
            SELECT b.isbn, b.title, COUNT(*) AS copies
            FROM book b
            JOIN book_copy c ON c.isbn = b.isbn
            GROUP BY b.isbn, b.title
            ORDER BY copies DESC, b.title""")

        # category and price are both in book -> no JOIN needed
        show(cur, "3. Filter: Databases books costing more than 50", """
            SELECT title, category, price
            FROM book
            WHERE category = %s AND price > %s
            ORDER BY price DESC""", ("Databases", 50))

        # LEFT JOIN keeps publishers with no books; COUNT(b.isbn) ignores NULLs -> 0
        show(cur, "4. LEFT JOIN: books per publisher, including publishers with none", """
            SELECT p.name, COUNT(b.isbn) AS books
            FROM publisher p
            LEFT JOIN book b ON b.publisher_id = p.publisher_id
            GROUP BY p.publisher_id, p.name
            ORDER BY books DESC, p.name""")
        cur.execute("""SELECT COUNT(DISTINCT p.publisher_id) FROM publisher p
                       JOIN book b ON b.publisher_id = p.publisher_id""")
        print(f"(the same query with an INNER JOIN returns only {cur.fetchone()[0]} rows)")

        # anti-join: LEFT JOIN, then keep the rows where no copy matched
        show(cur, "5. LEFT JOIN + IS NULL: books with no copies", """
            SELECT b.isbn, b.title
            FROM book b
            LEFT JOIN book_copy c ON c.isbn = b.isbn
            WHERE c.isbn IS NULL
            ORDER BY b.title""")

        # names in library_user, title in book, dates in issue -> two JOINs.
        # issue.isbn reaches book directly; book_copy adds no needed column.
        show(cur, "6. Issue: copies currently out, with overdue days", """
            SELECT u.first_name, u.last_name, b.title, i.barcode_no, i.due_date,
                   GREATEST(CURRENT_DATE - i.due_date, 0) AS days_overdue
            FROM issue i
            JOIN library_user u ON u.user_id = i.user_id
            JOIN book b ON b.isbn = i.isbn
            WHERE i.return_date IS NULL
            ORDER BY days_overdue DESC, b.title""")

        # LEFT JOIN keeps users who never borrowed; COALESCE turns their NULL sum into 0
        show(cur, "7. LEFT JOIN + aggregate: loans and fines per user", """
            SELECT u.user_id, u.first_name, u.last_name,
                   COUNT(i.issue_id) AS loans,
                   COALESCE(SUM(i.fine_amt), 0.00) AS total_fines
            FROM library_user u
            LEFT JOIN issue i ON i.user_id = u.user_id
            GROUP BY u.user_id, u.first_name, u.last_name
            ORDER BY u.user_id""")


if __name__ == "__main__":
    with connection() as conn:
        integrity_demo(conn)
        delete_rules_demo(conn)
        queries_demo(conn)
