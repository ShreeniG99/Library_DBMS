"""Load sample data using parameterized queries.

Re-runnable: it empties every table first, in the same transaction as the
inserts, so running it twice gives the same data (and a failed run leaves
the old data untouched).
"""
from datetime import date, timedelta

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

# (isbn, number of copies); barcodes restart at 1 for each book.
# Two books have no copies at all -> LEFT JOIN / anti-join demo.
COPIES = [
    ("9780133970777", 3),
    ("9780136086208", 2),
    ("9780134685991", 2),
    ("9780135957059", 1),
    ("9781492056355", 4),
    ("9781449373320", 2),
    ("9781119826736", 1),
]

# (user_id, first_name, last_name, address, city, state); one user has no address.
USERS = [
    (1, "Asha", "Rao", "12 MG Road", "Bengaluru", "Karnataka"),
    (2, "Ravi", "Kumar", "4 Anna Salai", "Chennai", "Tamil Nadu"),
    (3, "Meera", "Nair", "7 Marine Drive", "Kochi", "Kerala"),
    (4, "Arjun", "Singh", "22 Civil Lines", "Jaipur", "Rajasthan"),
    (5, "Priya", "Das", "9 Park Street", "Kolkata", "West Bengal"),
    (6, "Karan", "Shah", None, None, None),
]

STAFF = [(1, 1), (2, 2)]  # (staff_id, user_id): Asha and Ravi are staff

FINE_PER_DAY = 2.00
LOAN_DAYS = 14

# (issue_id, user_id, staff_id, isbn, barcode_no, issued_days_ago, returned_days_ago)
# returned_days_ago None -> still out (return_date NULL). Dates are relative
# to today so the overdue query always has something to show.
LOANS = [
    (1, 3, 1, "9780133970777", 1, 30, 20),    # returned on time
    (2, 4, 1, "9780133970777", 2, 25, 5),     # returned 6 days late -> fine
    (3, 3, 2, "9781492056355", 1, 10, None),  # out, not yet due
    (4, 5, 2, "9781492056355", 2, 40, None),  # out and overdue
    (5, 6, 1, "9781449373320", 1, 3, None),   # out, not yet due
    (6, 4, 2, "9781119826736", 1, 50, 30),    # returned 6 days late -> fine
    (7, 5, 1, "9780136086208", 1, 8, 2),      # returned on time
    (8, 3, 1, "9780133970777", 1, 12, None),  # same copy as loan 1, out again
]


def issue_rows(today):
    rows = []
    for issue_id, user_id, staff_id, isbn, barcode, issued_ago, returned_ago in LOANS:
        issue_date = today - timedelta(days=issued_ago)
        due_date = issue_date + timedelta(days=LOAN_DAYS)
        return_date = None if returned_ago is None else today - timedelta(days=returned_ago)
        late_days = (return_date - due_date).days if return_date else 0
        fine = FINE_PER_DAY * max(late_days, 0)
        rows.append((issue_id, user_id, staff_id, isbn, barcode,
                     issue_date, due_date, return_date, fine))
    return rows


def seed(conn):
    issues = issue_rows(date.today())
    on_loan = {(r[3], r[4]) for r in issues if r[7] is None}
    copy_rows = [
        (isbn, n, "issued" if (isbn, n) in on_loan else "available")
        for isbn, count in COPIES
        for n in range(1, count + 1)
    ]
    with conn.cursor() as cur:
        cur.execute("TRUNCATE issue, book_copy, book, staff, library_user, publisher")
        execute_values(cur, "INSERT INTO publisher (publisher_id, name, publication_name)"
                            " VALUES %s", PUBLISHERS)
        execute_values(cur, "INSERT INTO book (isbn, title, category, edition, price,"
                            " year_of_publication, publisher_id) VALUES %s", BOOKS)
        execute_values(cur, "INSERT INTO book_copy (isbn, barcode_no, status)"
                            " VALUES %s", copy_rows)
        execute_values(cur, "INSERT INTO library_user (user_id, first_name, last_name,"
                            " address, city, state) VALUES %s", USERS)
        execute_values(cur, "INSERT INTO staff (staff_id, user_id) VALUES %s", STAFF)
        execute_values(cur, "INSERT INTO issue (issue_id, user_id, staff_id, isbn,"
                            " barcode_no, issue_date, due_date, return_date, fine_amt)"
                            " VALUES %s", issues)
    return len(copy_rows), len(issues)


if __name__ == "__main__":
    with connection() as conn:
        n_copies, n_issues = seed(conn)
    print(f"Seeded {len(PUBLISHERS)} publishers, {len(BOOKS)} books, {n_copies} copies, "
          f"{len(USERS)} users, {len(STAFF)} staff, {n_issues} issues")
