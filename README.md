# Library DBMS (Python + PostgreSQL)

Simplified subset of the library ER diagram: Publisher, Book, Book_copy, and the
Issue relationship with the User and Staff entities it connects.
Left out as out of scope: Student (the other ISA subclass), Authentication System / login,
and Author with the M:N "written by" relationship.

## ER diagram
Full ER diagram of the library system (rotated and brightened; the drawing itself is unchanged).

![Library ER diagram](docs/er_diagram.png)

## Run
```bash
pip install -r requirements.txt
export PGDATABASE=library_db PGUSER=... PGPASSWORD=...   # optional: PGHOST, PGPORT
python schema.py   # create tables from schema.sql (drops/recreates)
python seed.py     # sample data; safe to re-run (empties the tables first)
python demo.py     # integrity checks, delete rules, 7 demo queries
```

`schema.sql` is plain SQL, so the same schema can be created from psql
(`psql -d library_db -f schema.sql`) or by opening it in pgAdmin's Query Tool.
psql (`\dt`, `\d issue`) and pgAdmin are handy for showing the tables and constraints during the viva;
the Python scripts are the project itself.

## Schema
| Table | Columns | Keys |
|---|---|---|
| `publisher` | publisher_id, name, publication_name | PK publisher_id |
| `book` | isbn, title, category, edition, price, year_of_publication, publisher_id | PK isbn; FK publisher_id -> publisher |
| `book_copy` | isbn, barcode_no, status | PK (isbn, barcode_no); FK isbn -> book ON DELETE CASCADE |
| `library_user` | user_id, first_name, last_name, address, city, state | PK user_id |
| `staff` | staff_id, user_id | PK staff_id; FK user_id -> library_user (UNIQUE, ON DELETE CASCADE) |
| `issue` | issue_id, user_id, staff_id, isbn, barcode_no, issue_date, due_date, return_date, fine_amt | PK issue_id; FK user_id -> library_user; FK staff_id -> staff; FK (isbn, barcode_no) -> book_copy |

Extra constraints: `book.publisher_id NOT NULL`; `price >= 0`; `fine_amt >= 0`;
`due_date >= issue_date`; `return_date` is NULL (still out) or `>= issue_date`;
a unique partial index allows only one open loan (`return_date IS NULL`) per copy.

Mapping notes: the ER "User" is `library_user` because `USER` is a reserved word in PostgreSQL.
Name (first/last) and Address (city/state) are composite attributes, stored as their parts.

## Sample data
6 publishers (2 with no books), 9 books (2 with no copies, one with a NULL price, one with a NULL edition),
15 copies, 6 users (2 of them staff, 2 who never borrowed), 8 issues (4 still out, 1 of them overdue,
2 returned late with a fine). Loan dates are relative to the day `seed.py` runs, so "overdue" always has a row.

## Viva talking points
- **Composite PK on book_copy:** it is a weak entity. `barcode_no` (1, 2, 3...) only identifies a copy
  *within one book*, so the key is `(isbn, barcode_no)`; the isbn part is also the FK to the owner.
- **Composite FK on issue:** because book_copy's key has two columns, issue must reference both
  `(isbn, barcode_no)`. An isbn that exists with a barcode that doesn't is still rejected.
- **CASCADE on book_copy->book, not on book->publisher:** a copy has no meaning without its book,
  so deleting a book removes its copies. A publisher deletion should never silently wipe out
  the catalogue; the default `NO ACTION` forces you to reassign or delete books first.
- **Cascade stops at issue:** deleting a book whose copies have loan history fails, because issue
  references those copies with no cascade. The whole DELETE is refused, so loan history stays intact.
- **Integrity demos:** bad FK (copy and issue), duplicate composite key, a second open loan of the same copy,
  and a due date before the issue date are all rejected by PostgreSQL itself, independent of application code.
- **LEFT JOIN vs INNER JOIN:** query 4 lists 6 publishers with a LEFT JOIN but only 4 with an INNER JOIN.
  `COUNT(b.isbn)` gives 0 for the unmatched ones because COUNT(column) skips NULLs (COUNT(*) would give 1).
  Query 5 uses `LEFT JOIN ... WHERE c.isbn IS NULL` to find books with no copies; query 7 keeps users who never
  borrowed and uses `COALESCE` to turn their NULL fine total into 0.
- **NULLs in filters:** query 3 (`price > 50`) leaves out the Databases book with a NULL price, because
  comparing NULL gives "unknown", not true.
- **Which queries join:** a join is used only when the selected columns live in different tables.
  Query 3 reads only `book`. Query 6 gets the title through `issue.isbn -> book` directly; going through
  `book_copy` would add nothing it needs.
- **Connections:** `db.connection()` commits on success, rolls back on an error, and always closes the
  connection in `finally`. (psycopg2's own `with conn:` only ends the transaction; it does not close.)
- **Re-runnable seed:** `seed.py` runs `TRUNCATE` and all inserts in one transaction. Running it twice gives
  the same data, and if any insert fails the TRUNCATE is rolled back too, so the old data survives.
- **Security:** credentials via env vars; all values passed as query parameters (no string formatting).
