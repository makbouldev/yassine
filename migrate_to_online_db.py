from pathlib import Path
import sqlite3

import database


ROOT = Path(__file__).resolve().parent
LOCAL_DB = ROOT / "app_data.db"
DEFAULT_TABLE = ROOT / "default_table.xlsx"


def migrate_users():
    if not LOCAL_DB.exists():
        return 0

    copied = 0
    with sqlite3.connect(LOCAL_DB) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT username, password, role FROM users")
        except sqlite3.OperationalError:
            return 0

        for username, password, role in cursor.fetchall():
            database.upsert_user(username, password, role)
            copied += 1

    return copied


def migrate_table():
    if not DEFAULT_TABLE.exists():
        return False
    return database.import_excel_file(DEFAULT_TABLE, replace=True)


def main():
    if not database.using_postgres():
        raise SystemExit(
            "DATABASE_URL is not configured. Copy .env.example to .env and add your online PostgreSQL URL first."
        )

    database.init_db()
    table_uploaded = migrate_table()
    users_copied = migrate_users()

    print(f"Connected to {database.storage_label()}")
    print(f"Table uploaded: {'yes' if table_uploaded else 'no'}")
    print(f"Users copied from local SQLite: {users_copied}")
    print("Done. Use the same .env file on every computer that should share this database.")


if __name__ == "__main__":
    main()
