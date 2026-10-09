"""Connection helpers. Credentials come from environment variables."""
import os
from contextlib import contextmanager

import psycopg2


def get_connection():
    return psycopg2.connect(
        host=os.environ.get("PGHOST", "localhost"),
        port=os.environ.get("PGPORT", "5432"),
        dbname=os.environ["PGDATABASE"],
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
    )


@contextmanager
def connection():
    """Commit on success, roll back on error, and always close the connection.

    psycopg2's own `with conn:` only ends the transaction; it does not close.
    """
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
