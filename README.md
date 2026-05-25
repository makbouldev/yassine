# Yassine Excel Manager

Desktop application for managing a shared table with user login, admin user management, edit history, and optional online PostgreSQL storage.

## Install

```powershell
pip install -r requirements.txt
```

## Run

```powershell
python main.py
```

Default login:

```text
admin / admin
```

Change the admin password from the Admin Dashboard after first login.

## Online Database

The app works locally with SQLite by default. To share the same table between users on different networks, copy `.env.example` to `.env` and add a PostgreSQL `DATABASE_URL` from Supabase or Neon.

Then upload local data once:

```powershell
python migrate_to_online_db.py
```

See `ONLINE_DATABASE_SETUP.md` for the full setup steps.
