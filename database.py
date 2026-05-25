import datetime
import json
import os
import sqlite3
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

DB_FILE = "app_data.db"
ENV_FILE = Path(__file__).with_name(".env")

DEFAULT_TABLE_HEADERS = [
    "N°Fact",
    "Rep",
    "Date",
    "Reçu",
    "Libelles",
    "Versement",
    "Débours",
    "Honoraires",
    "T.V.A",
    "Honors/H.T",
]
TABLE_HEADERS_KEY = "table_headers"
TABLE_SEEDED_KEY = "table_seeded"


def _load_env_file():
    if not ENV_FILE.exists():
        return

    for raw_line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_env_file()


def _database_url():
    return os.environ.get("DATABASE_URL", "").strip()


def using_postgres():
    url = _database_url().lower()
    return url.startswith("postgresql://") or url.startswith("postgres://")


def _postgres_url():
    url = _database_url()
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]

    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    host = (parsed.hostname or "").lower()
    if host and host not in {"localhost", "127.0.0.1", "::1"}:
        query.setdefault("sslmode", "require")

    return urlunparse(parsed._replace(query=urlencode(query)))


def storage_label():
    return "online PostgreSQL database" if using_postgres() else f"local SQLite file ({DB_FILE})"


def get_connection():
    if using_postgres():
        try:
            import psycopg
        except ImportError as exc:
            raise RuntimeError(
                "DATABASE_URL is configured, but the PostgreSQL driver is missing. "
                "Run: pip install -r requirements.txt"
            ) from exc
        return psycopg.connect(_postgres_url())

    return sqlite3.connect(DB_FILE)


def _placeholder():
    return "%s" if using_postgres() else "?"


def _id_column():
    return "SERIAL PRIMARY KEY" if using_postgres() else "INTEGER PRIMARY KEY AUTOINCREMENT"


def _is_unique_error(exc):
    return isinstance(exc, sqlite3.IntegrityError) or getattr(exc, "sqlstate", None) == "23505"


def _fetch_meta(cursor, key):
    p = _placeholder()
    cursor.execute(f"SELECT value FROM spreadsheet_meta WHERE key = {p}", (key,))
    row = cursor.fetchone()
    return row[0] if row else None


def _set_meta(cursor, key, value):
    p = _placeholder()
    cursor.execute(f"DELETE FROM spreadsheet_meta WHERE key = {p}", (key,))
    cursor.execute(f"INSERT INTO spreadsheet_meta (key, value) VALUES ({p}, {p})", (key, value))


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    id_col = _id_column()
    try:
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS users (
                id {id_col},
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL
            )
            """
        )

        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS history (
                id {id_col},
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                username TEXT NOT NULL,
                row_idx INTEGER,
                column_name TEXT,
                old_value TEXT,
                new_value TEXT
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS spreadsheet_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )

        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS spreadsheet_rows (
                id {id_col},
                row_order INTEGER NOT NULL,
                data_json TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        p = _placeholder()
        cursor.execute(f"SELECT COUNT(*) FROM users WHERE role = {p}", ("admin",))
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                f"INSERT INTO users (username, password, role) VALUES ({p}, {p}, {p})",
                ("admin", "admin", "admin"),
            )

        if _fetch_meta(cursor, TABLE_HEADERS_KEY) is None:
            _set_meta(cursor, TABLE_HEADERS_KEY, json.dumps(DEFAULT_TABLE_HEADERS, ensure_ascii=False))

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def verify_login(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    p = _placeholder()
    cursor.execute(
        f"SELECT role FROM users WHERE username = {p} AND password = {p}",
        (username, password),
    )
    user = cursor.fetchone()
    conn.close()
    return user[0] if user else None


def get_all_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username, role FROM users ORDER BY username")
    users = cursor.fetchall()
    conn.close()
    return users


def add_user(username, password, role="user"):
    conn = get_connection()
    cursor = conn.cursor()
    p = _placeholder()
    try:
        cursor.execute(
            f"INSERT INTO users (username, password, role) VALUES ({p}, {p}, {p})",
            (username, password, role),
        )
        conn.commit()
        return True
    except Exception as exc:
        conn.rollback()
        if _is_unique_error(exc):
            return False
        raise
    finally:
        conn.close()


def upsert_user(username, password, role="user"):
    conn = get_connection()
    cursor = conn.cursor()
    p = _placeholder()
    try:
        cursor.execute(
            f"UPDATE users SET password = {p}, role = {p} WHERE username = {p}",
            (password, role, username),
        )
        if cursor.rowcount == 0:
            cursor.execute(
                f"INSERT INTO users (username, password, role) VALUES ({p}, {p}, {p})",
                (username, password, role),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_user(username):
    if username == "admin":
        return False
    conn = get_connection()
    cursor = conn.cursor()
    p = _placeholder()
    cursor.execute(f"DELETE FROM users WHERE username = {p}", (username,))
    conn.commit()
    conn.close()
    return True


def change_password(username, new_password):
    conn = get_connection()
    cursor = conn.cursor()
    p = _placeholder()
    cursor.execute(f"UPDATE users SET password = {p} WHERE username = {p}", (new_password, username))
    conn.commit()
    conn.close()


def insert_history(timestamp, username, row_idx, column_name, old_value, new_value):
    conn = get_connection()
    cursor = conn.cursor()
    p = _placeholder()
    try:
        cursor.execute(
            f"""
            INSERT INTO history (timestamp, username, row_idx, column_name, old_value, new_value)
            VALUES ({p}, {p}, {p}, {p}, {p}, {p})
            """,
            (timestamp, username, row_idx, column_name, str(old_value), str(new_value)),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def log_edit(username, row_idx, column_name, old_value, new_value):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    insert_history(timestamp, username, row_idx, column_name, old_value, new_value)


def get_history():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT timestamp, username, row_idx, column_name, old_value, new_value "
        "FROM history ORDER BY timestamp DESC, id DESC"
    )
    history = cursor.fetchall()
    conn.close()
    return history


def get_table_headers():
    conn = get_connection()
    cursor = conn.cursor()
    value = _fetch_meta(cursor, TABLE_HEADERS_KEY)
    conn.close()
    if not value:
        return DEFAULT_TABLE_HEADERS[:]
    try:
        headers = json.loads(value)
        return headers if headers else DEFAULT_TABLE_HEADERS[:]
    except json.JSONDecodeError:
        return DEFAULT_TABLE_HEADERS[:]


def get_table_data():
    headers = get_table_headers()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT data_json FROM spreadsheet_rows ORDER BY row_order ASC, id ASC")
    rows = []
    for (payload,) in cursor.fetchall():
        try:
            data = json.loads(payload) if payload else {}
        except json.JSONDecodeError:
            data = {}
        rows.append([data.get(header, "") for header in headers])
    conn.close()
    return headers, rows


def save_table_data(headers, rows):
    conn = get_connection()
    cursor = conn.cursor()
    p = _placeholder()
    try:
        _set_meta(cursor, TABLE_HEADERS_KEY, json.dumps(headers, ensure_ascii=False))
        _set_meta(cursor, TABLE_SEEDED_KEY, "1")
        cursor.execute("DELETE FROM spreadsheet_rows")

        for row_order, row in enumerate(rows):
            record = {}
            for index, header in enumerate(headers):
                value = row[index] if index < len(row) else ""
                record[header] = "" if value is None else str(value)

            cursor.execute(
                f"INSERT INTO spreadsheet_rows (row_order, data_json) VALUES ({p}, {p})",
                (row_order, json.dumps(record, ensure_ascii=False)),
            )

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def import_excel_file(filepath="default_table.xlsx", replace=True):
    import pandas as pd

    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(path)

    if not replace:
        _headers, rows = get_table_data()
        if rows:
            return False

    df = pd.read_excel(path, dtype=str).fillna("")
    headers = df.columns.tolist() or DEFAULT_TABLE_HEADERS[:]
    rows = df.values.tolist()
    save_table_data(headers, rows)
    return True


def seed_table_from_excel_if_empty(filepath="default_table.xlsx"):
    conn = get_connection()
    cursor = conn.cursor()
    seeded = _fetch_meta(cursor, TABLE_SEEDED_KEY)
    conn.close()
    if seeded:
        return False

    _headers, rows = get_table_data()
    if rows:
        save_table_data(_headers, rows)
        return False

    path = Path(filepath)
    if not path.exists():
        save_table_data(_headers, rows)
        return False

    return import_excel_file(path, replace=True)
