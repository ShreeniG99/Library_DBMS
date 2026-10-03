"""Create the three tables (drops and recreates them, so it is re-runnable)."""
from db import get_connection

DDL = """
DROP TABLE IF EXISTS book_copy;
DROP TABLE IF EXISTS book;
DROP TABLE IF EXISTS publisher;

CREATE TABLE publisher (
    publisher_id     INTEGER PRIMARY KEY,
    name             VARCHAR(100) NOT NULL,
    publication_name VARCHAR(100)
);

-- N:1 to publisher. Plain REFERENCES (= ON DELETE NO ACTION): a publisher
-- cannot be deleted while books still point at it.
CREATE TABLE book (
    isbn                CHAR(13) PRIMARY KEY,
    title               VARCHAR(200) NOT NULL,
    category            VARCHAR(50),
    edition             INTEGER,
    price               NUMERIC(8,2) CHECK (price >= 0),
    year_of_publication INTEGER,
    publisher_id        INTEGER NOT NULL REFERENCES publisher(publisher_id)
);

-- Weak entity: barcode_no is only unique within one book's copies,
-- so the key is (isbn, barcode_no). Copies die with their book.
CREATE TABLE book_copy (
    isbn       CHAR(13) NOT NULL REFERENCES book(isbn) ON DELETE CASCADE,
    barcode_no INTEGER  NOT NULL,
    status     VARCHAR(20) NOT NULL DEFAULT 'available',
    PRIMARY KEY (isbn, barcode_no)
);
"""


def create_tables(conn):
    with conn.cursor() as cur:
        cur.execute(DDL)
    conn.commit()


if __name__ == "__main__":
    with get_connection() as conn:
        create_tables(conn)
    print("Tables created: publisher, book, book_copy")
