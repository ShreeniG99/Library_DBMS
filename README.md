# Library DBMS (Python + PostgreSQL)

Simplified subset of the library ER diagram: three tables, **Publisher**, **Book** and **Book_copy**,
linked by the "Published by" and "has" relationships.
Left out as out of scope: User (with the Student/Staff ISA), Authentication System, Issue, and Author.

## ER diagram
Full ER diagram of the library system (rotated and brightened; the drawing itself is unchanged).

![Library ER diagram](docs/er_diagram.png)

## Run
```bash
pip install -r requirements.txt
export PGDATABASE=library_db PGUSER=... PGPASSWORD=...   # optional: PGHOST, PGPORT
python schema.py   # create tables from schema.sql (drops/recreates)
python seed.py     # sample data; safe to re-run (empties the tables first)
python demo.py     # integrity checks, delete rules, 5 demo queries
```

`schema.sql` is plain SQL, so the same schema can be created from psql
(`psql -d library_db -f schema.sql`) or by opening it in pgAdmin's Query Tool.
psql (`\dt`, `\d book_copy`) and pgAdmin are handy for showing the tables and constraints during the viva;
the Python scripts are the project itself.

## Schema
| Table | Columns | Keys |
|---|---|---|
| `publisher` | publisher_id, name, publication_name | PK publisher_id |
| `book` | isbn, title, category, edition, price, year_of_publication, publisher_id | PK isbn; FK publisher_id -> publisher |
| `book_copy` | isbn, barcode_no, status | PK (isbn, barcode_no); FK isbn -> book ON DELETE CASCADE |

Extra constraints: `book.publisher_id` is `NOT NULL` (every book has a publisher) and `price >= 0`.

## Sample data
6 publishers (2 with no books), 9 books (2 with no copies, one with a NULL price, one with a NULL edition),
15 copies with mixed status (available / issued / lost).

## Viva talking points
- **Composite PK on book_copy:** it is a weak entity. `barcode_no` (1, 2, 3...) only identifies a copy
  *within one book*, so the key is `(isbn, barcode_no)`; the isbn part is also the FK to the owner.
- **CASCADE on book_copy->book, not on book->publisher:** a copy has no meaning without its book,
  so deleting a book removes its copies. A publisher deletion should never silently wipe out
  the catalogue; the default `NO ACTION` forces you to reassign or delete books first.
- **Integrity demos:** a copy with a non-existent isbn, a book with a non-existent publisher, a duplicate
  `(isbn, barcode_no)` and a negative price are all rejected by PostgreSQL itself, independent of application code.
- **LEFT JOIN vs INNER JOIN:** query 4 lists 6 publishers with a LEFT JOIN but only 4 with an INNER JOIN.
  `COUNT(b.isbn)` gives 0 for the unmatched ones because COUNT(column) skips NULLs (COUNT(*) would give 1).
  Query 5 uses `LEFT JOIN ... WHERE c.isbn IS NULL` to find books with no copies.
- **NULLs in filters:** query 3 (`price > 50`) leaves out the Databases book with a NULL price, because
  comparing NULL gives "unknown", not true.
- **Which queries join:** a join is used only when the selected columns live in different tables.
  Query 1 needs `book` + `publisher`, query 2 needs title from `book` and counts from `book_copy`;
  query 3 reads only `book`, so it has no join.
- **Connections:** `db.connection()` commits on success, rolls back on an error, and always closes the
  connection in `finally`. (psycopg2's own `with conn:` only ends the transaction; it does not close.)
- **Re-runnable seed:** `seed.py` runs `TRUNCATE` and all inserts in one transaction. Running it twice gives
  the same data, and if any insert fails the TRUNCATE is rolled back too, so the old data survives.
- **Security:** credentials via env vars; all values passed as query parameters (no string formatting).
