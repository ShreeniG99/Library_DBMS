# Library DBMS (Python + PostgreSQL)

Simplified subset of the library ER diagram: `publisher`, `book`, `book_copy`.
(ISA user hierarchy, ternary Issue relationship and the Author M:N junction are out of scope.)

## Run
```bash
pip install -r requirements.txt
export PGDATABASE=library_db PGUSER=... PGPASSWORD=...   # optional: PGHOST, PGPORT
python schema.py   # create tables (drops/recreates)
python seed.py     # sample data
python demo.py     # FK-violation demo + 3 queries
```

## Schema
- `publisher(publisher_id PK, name, publication_name)`
- `book(isbn PK, title, category, edition, price, year_of_publication, publisher_id FK -> publisher)`
- `book_copy(isbn FK -> book ON DELETE CASCADE, barcode_no, status, PK(isbn, barcode_no))`

`book.publisher_id` is `NOT NULL` (every book has a publisher) and `price` has `CHECK (price >= 0)`.

## Viva talking points
- **Composite PK on book_copy:** it is a weak entity. `barcode_no` (1, 2, 3...) only identifies a copy
  *within one book*, so the key is `(isbn, barcode_no)`; the isbn part is also the FK to the owner.
- **CASCADE on book_copy->book, not on book->publisher:** a copy has no meaning without its book,
  so deleting a book should remove its copies. A publisher deletion should never silently wipe out
  the catalogue; the default `NO ACTION` forces you to reassign or delete books first.
- **FK violation demo:** inserting a copy with isbn `0000000000000` raises `ForeignKeyViolation`
  ("Key (isbn)=... is not present in table book"), so the DB itself prevents orphan rows,
  independent of application code.
- **Joins:** queries 1 and 2 join (title/price in `book`, publisher name in `publisher`). Copies per
  book needs title (in `book`) and counts from `book_copy`, so it joins too; only the category/price filter needs no join (all columns in `book`).
- **Security:** credentials via env vars; all values passed as query parameters (no string formatting).
