"""
MariaDB/MySQL connection handling (pclaimassist_db).

Phase 1 scope: used only by case_session_store.py to persist reviewed OCR
"case sessions" (previously JSON files under uploads/reviewed_results/
sessions/). Grid templates, training crops, and every other OCR storage
path are untouched and remain file-based - see template_store.py.

Credentials come from environment variables / a local .env file (see
config.py's loader and .env.example) - never hardcoded here.
"""
import logging
from contextlib import contextmanager

import pymysql
import pymysql.cursors

import config
from errors import DatabaseConnectionError, DatabaseError

logger = logging.getLogger(__name__)


def get_connection():
    """Open a new connection to pclaimassist_db.

    Raises DatabaseConnectionError (caught by the app's existing error
    handlers, same as every other OCRAppError) if the database is
    unreachable or credentials are wrong.
    """
    try:
        return pymysql.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=config.DB_CONNECT_TIMEOUT,
            autocommit=False,
        )
    except pymysql.MySQLError as e:
        logger.error(
            "Database connection failed (%s@%s:%s/%s): %s",
            config.DB_USER, config.DB_HOST, config.DB_PORT, config.DB_NAME, e,
        )
        raise DatabaseConnectionError(
            f"Could not connect to the database at {config.DB_HOST}:{config.DB_PORT}/"
            f"{config.DB_NAME}. Is MariaDB running in XAMPP? ({e})"
        ) from e


@contextmanager
def get_db_cursor(commit=False):
    """Yield a DictCursor on a fresh connection.

    Commits and closes automatically on success; rolls back and closes on
    failure. Connection failures surface as DatabaseConnectionError; query
    failures on an otherwise-good connection surface as DatabaseError. Both
    are OCRAppError subclasses, so existing routes need no extra try/except
    - the app's registered error handlers already turn them into the same
    flat {"success": false, "error": "..."} JSON shape every other error
    uses.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            yield cursor
        if commit:
            conn.commit()
    except pymysql.MySQLError as e:
        conn.rollback()
        logger.error("Database query failed: %s", e)
        raise DatabaseError(str(e)) from e
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def test_connection():
    """Round-trip check used by the /db_health diagnostic route.

    Returns the MariaDB/MySQL server version string on success; raises
    DatabaseConnectionError on failure.
    """
    with get_db_cursor() as cursor:
        cursor.execute("SELECT VERSION() AS version")
        row = cursor.fetchone()
    return row["version"] if row else "unknown"
