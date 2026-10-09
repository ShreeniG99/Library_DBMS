-- Library DBMS schema. Re-runnable: drops and recreates every table.
-- Run from Python (schema.py) or directly:  psql -d library_db -f schema.sql

DROP TABLE IF EXISTS issue;
DROP TABLE IF EXISTS book_copy;
DROP TABLE IF EXISTS book;
DROP TABLE IF EXISTS staff;
DROP TABLE IF EXISTS library_user;
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
-- so the key is (isbn, barcode_no). Copies die with their book
-- (unless an issue row still references them, see issue below).
CREATE TABLE book_copy (
    isbn       CHAR(13) NOT NULL REFERENCES book(isbn) ON DELETE CASCADE,
    barcode_no INTEGER  NOT NULL,
    status     VARCHAR(20) NOT NULL DEFAULT 'available',
    PRIMARY KEY (isbn, barcode_no)
);

-- "User" in the ER diagram. USER is a reserved word in PostgreSQL,
-- hence library_user. Name and Address are composite attributes,
-- stored as their component columns.
CREATE TABLE library_user (
    user_id    INTEGER PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name  VARCHAR(50),
    address    VARCHAR(200),
    city       VARCHAR(50),
    state      VARCHAR(50)
);

-- Staff IS-A User: one staff row per user at most (UNIQUE), and the
-- subclass row goes away with its user.
CREATE TABLE staff (
    staff_id INTEGER PRIMARY KEY,
    user_id  INTEGER NOT NULL UNIQUE
             REFERENCES library_user(user_id) ON DELETE CASCADE
);

-- Issue relationship: a User borrows a Book_copy, processed by one Staff.
-- Composite FK to book_copy because that table has a composite key.
-- No cascades: loan history must not disappear silently.
CREATE TABLE issue (
    issue_id    INTEGER PRIMARY KEY,
    user_id     INTEGER  NOT NULL REFERENCES library_user(user_id),
    staff_id    INTEGER  NOT NULL REFERENCES staff(staff_id),
    isbn        CHAR(13) NOT NULL,
    barcode_no  INTEGER  NOT NULL,
    issue_date  DATE     NOT NULL DEFAULT CURRENT_DATE,
    due_date    DATE     NOT NULL,
    return_date DATE,                                  -- NULL = still out
    fine_amt    NUMERIC(8,2) NOT NULL DEFAULT 0 CHECK (fine_amt >= 0),
    FOREIGN KEY (isbn, barcode_no) REFERENCES book_copy(isbn, barcode_no),
    CHECK (due_date >= issue_date),
    CHECK (return_date IS NULL OR return_date >= issue_date)
);

-- A copy can be out on at most one loan at a time.
CREATE UNIQUE INDEX one_open_issue_per_copy
    ON issue (isbn, barcode_no) WHERE return_date IS NULL;
