"""Load sample data using parameterized queries.

Re-runnable: it empties every table first, in the same transaction as the
inserts, so running it twice gives the same data (and a failed run leaves
the old data untouched).
"""
from psycopg2.extras import execute_values

from db import connection

PUBLISHERS = [
    (1, "Pearson", "Pearson Education"),
    (2, "McGraw-Hill", "McGraw-Hill Education"),
    (3, "O'Reilly Media", "O'Reilly"),
    (4, "Wiley", "John Wiley & Sons"),
    (5, "Springer", "Springer Nature"),            # no books -> LEFT JOIN demo
    (6, "Cambridge University Press", "CUP"),      # no books -> LEFT JOIN demo
]

# (isbn, title, category, edition, price, year_of_publication, publisher_id)
# None -> NULL: one book has no price yet, one has no edition recorded.
BOOKS = [
    ("9780133970777", "Database System Concepts", "Databases", 7, 89.99, 2019, 2),
    ("9780072465631", "Database Management Systems", "Databases", 3, None, 2002, 2),
    ("9780136086208", "Fundamentals of Database Systems", "Databases", 7, 79.50, 2015, 1),
    ("9780134685991", "Effective Java", "Programming", 3, 54.99, 2018, 1),
    ("9780136681557", "Computer Networking: A Top-Down Approach", "Networking", 8, 95.00, 2021, 1),
    ("9780135957059", "The Pragmatic Programmer", "Programming", None, 44.99, 2019, 1),
    ("9781492056355", "Fluent Python", "Programming", 2, 59.99, 2022, 3),
    ("9781449373320", "Designing Data-Intensive Applications", "Databases", 1, 49.99, 2017, 3),
    ("9781119826736", "Operating System Concepts", "Systems", 10, 120.00, 2021, 4),
]

# (isbn, barcode_no, status); barcodes restart at 1 for each book.
# Two books have no copies at all -> LEFT JOIN / anti-join demo.
COPIES = [
    ("9780133970777", 1, "issued"),
    ("9780133970777", 2, "available"),
    ("9780133970777", 3, "available"),
    ("9780136086208", 1, "available"),
    ("9780136086208", 2, "lost"),
    ("9780134685991", 1, "available"),
    ("9780134685991", 2, "available"),
    ("9780135957059", 1, "issued"),
    ("9781492056355", 1, "issued"),
    ("9781492056355", 2, "issued"),
    ("9781492056355", 3, "available"),
    ("9781492056355", 4, "available"),
    ("9781449373320", 1, "available"),
    ("9781449373320", 2, "issued"),
    ("9781119826736", 1, "available"),
]


def seed(conn):
    with conn.cursor() as cur:
        cur.execute("TRUNCATE book_copy, book, publisher")
        execute_values(cur, "INSERT INTO publisher (publisher_id, name, publication_name)"
                            " VALUES %s", PUBLISHERS)
        execute_values(cur, "INSERT INTO book (isbn, title, category, edition, price,"
                            " year_of_publication, publisher_id) VALUES %s", BOOKS)
        execute_values(cur, "INSERT INTO book_copy (isbn, barcode_no, status)"
                            " VALUES %s", COPIES)


if __name__ == "__main__":
    with connection() as conn:
        seed(conn)
    print(f"Seeded {len(PUBLISHERS)} publishers, {len(BOOKS)} books, {len(COPIES)} copies")
