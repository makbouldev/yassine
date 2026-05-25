# Online Database Setup

Had version katkhlli l'application tkhdem b online PostgreSQL database. Ila `DATABASE_URL`
ma kaynach, l'application katbqa khdama local b `app_data.db`.

## 1. Créer database free

Dir account f Supabase ola Neon, crée project/database, men baad copy PostgreSQL
connection string.

Connection string khaso yban b had l-form:

```text
postgresql://USER:PASSWORD@HOST:5432/DATABASE?sslmode=require
```

## 2. Configurer l'application

1. Copy `.env.example` w smmiha `.env`.
2. Bedel `DATABASE_URL=...` b connection string dyalk.
3. Installer dependencies:

```powershell
pip install -r requirements.txt
```

## 3. Upload l-table w users l online DB

Run had command mara wahda mn PC li fih `default_table.xlsx` w `app_data.db`:

```powershell
python migrate_to_online_db.py
```

Script kaydir:

- creation dyal tables online
- upload dyal `default_table.xlsx`
- copy dyal users mn `app_data.db`

## 4. Khddemha f ay PC

F kol PC, khas nafs `.env` b nafs `DATABASE_URL`, men baad:

```powershell
python main.py
```

Mn daba, login/users/table/history ghadi ykono f nafs online DB, donc users ma
khas-homch ykono f nafs reseau.

## Notes

- Default admin kaybqa `admin` / `admin` ila ma kanch admin f database.
- Bedel password dyal admin men Admin Dashboard.
- Ma t-sharech `.env` public, hit fih password dyal database.
