"""Insert sample data using parameterized queries."""
from psycopg2.extras import execute_values

from db import get_connection

PUBLISHERS = [
    (1, "Pearson", "Pearson Education"),
    (2, "McGraw-Hill", "McGraw-Hill Education"),
    (3, "O'Reilly Media", "O'Reilly"),
    (4, "Wiley", "John Wiley & Sons"),
]

BOOKS = [
    ("9780133970777", "Database System Concepts", "Databases", 7, 89.99, 2019, 2),
    ("9780136086208", "Fundamentals of Database Systems", "Databases", 7, 79.50, 2015, 1),
    ("9781491946008", "Fluent Python", "Programming", 2, 59.99, 2022, 3),
    ("9781119826736", "Operating System Concepts", "Systems", 10, 120.00, 2021, 4),
]

# (isbn, number of copies); barcodes restart at 1 for each book
COPIES = [
    ("9780133970777", 3),
    ("9780136086208", 2),
    ("9781491946008", 4),
    ("9781119826736", 1),
]


def seed(conn):
    copy_rows = [
        (isbn, n, "available") for isbn, count in COPIES for n in range(1, count + 1)
    ]
    # One copy on loan so the status filter has something to show
    copy_rows[0] = (copy_rows[0][0], copy_rows[0][1], "issued")
    with conn.cursor() as cur:
        execute_values(
            cur,
            "INSERT INTO publisher (publisher_id, name, publication_name) VALUES %s",
            PUBLISHERS,
        )
        execute_values(
            cur,
            "INSERT INTO book (isbn, title, category, edition, price,"
            " year_of_publication, publisher_id) VALUES %s",
            BOOKS,
        )
        execute_values(
            cur,
            "INSERT INTO book_copy (isbn, barcode_no, status) VALUES %s",
            copy_rows,
        )
    conn.commit()


if __name__ == "__main__":
    with get_connection() as conn:
        seed(conn)
    print("Seeded 4 publishers, 4 books, 10 copies")
