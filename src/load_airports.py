import csv, os, sys
from pathlib import Path
from dotenv import load_dotenv
import mariadb

# Load .env near repo root
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "conduit_game")
DB_USER = os.getenv("DB_USER", "gameuser")
DB_PASS = os.getenv("DB_PASS", "yourpassword")

# airports.csv expected at data/airports.csv
PROJECT_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = PROJECT_ROOT / "data" / "airports.csv"

# Full schema matching the CSV columns (id is PK so we can upsert)
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS airports (
  id INT PRIMARY KEY,
  ident VARCHAR(20),
  type VARCHAR(50),
  name VARCHAR(200),
  latitude_deg DOUBLE,
  longitude_deg DOUBLE,
  elevation_ft INT,
  continent VARCHAR(10),
  iso_country VARCHAR(10),
  iso_region VARCHAR(20),
  municipality VARCHAR(100),
  scheduled_service VARCHAR(10),
  gps_code VARCHAR(20),
  iata_code VARCHAR(10),
  local_code VARCHAR(20),
  home_link TEXT,
  wikipedia_link TEXT,
  keywords TEXT
);
"""

INSERT_SQL = """
INSERT INTO airports (
  id, ident, type, name, latitude_deg, longitude_deg, elevation_ft,
  continent, iso_country, iso_region, municipality, scheduled_service,
  gps_code, iata_code, local_code, home_link, wikipedia_link, keywords
) VALUES (
  ?, ?, ?, ?, ?, ?, ?,
  ?, ?, ?, ?, ?,
  ?, ?, ?, ?, ?, ?
) ON DUPLICATE KEY UPDATE
  ident=VALUES(ident), type=VALUES(type), name=VALUES(name),
  latitude_deg=VALUES(latitude_deg), longitude_deg=VALUES(longitude_deg),
  elevation_ft=VALUES(elevation_ft), continent=VALUES(continent),
  iso_country=VALUES(iso_country), iso_region=VALUES(iso_region),
  municipality=VALUES(municipality), scheduled_service=VALUES(scheduled_service),
  gps_code=VALUES(gps_code), iata_code=VALUES(iata_code), local_code=VALUES(local_code),
  home_link=VALUES(home_link), wikipedia_link=VALUES(wikipedia_link), keywords=VALUES(keywords);
"""

def connect(db=None):
    kwargs = dict(user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT)
    if db:
        kwargs["database"] = db
    return mariadb.connect(**kwargs)

def ensure_db_exists():
    try:
        conn = connect(DB_NAME)
        conn.close()
        return
    except mariadb.OperationalError:
        pass
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        conn.commit()
        conn.close()
        print(f"Created database {DB_NAME} (or it already existed).")
    except mariadb.Error as e:
        print(f"Could not create database {DB_NAME}. Create it manually if needed. Error: {e}")

def ensure_schema():
    conn = connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(SCHEMA_SQL)
    conn.commit()
    conn.close()

def parse_int(v):
    try:
        return int(v) if v != "" else None
    except:
        return None

def parse_float(v):
    try:
        return float(v) if v != "" else None
    except:
        return None

def load_csv():
    if not CSV_PATH.exists():
        print(f"CSV not found: {CSV_PATH}")
        sys.exit(1)

    conn = connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM airports")
    before = cur.fetchone()[0]

    batch, BATCH = [], 1000
    total = 0
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rec = (
                parse_int(row["id"]),
                row["ident"] or None,
                row["type"] or None,
                row["name"] or None,
                parse_float(row["latitude_deg"]),
                parse_float(row["longitude_deg"]),
                parse_int(row["elevation_ft"]),
                row["continent"] or None,
                row["iso_country"] or None,
                row["iso_region"] or None,
                row["municipality"] or None,
                row["scheduled_service"] or None,
                row["gps_code"] or None,
                row["iata_code"] or None,
                row["local_code"] or None,
                row["home_link"] or None,
                row["wikipedia_link"] or None,
                row["keywords"] or None,
            )
            batch.append(rec)
            if len(batch) >= BATCH:
                cur.executemany(INSERT_SQL, batch)
                conn.commit()
                total += len(batch)
                print(f"Inserted {total:,}…")
                batch.clear()

    if batch:
        cur.executemany(INSERT_SQL, batch)
        conn.commit()
        total += len(batch)

    cur.execute("SELECT COUNT(*) FROM airports")
    after = cur.fetchone()[0]
    conn.close()

    print(f"Done. Rows before: {before:,}  after: {after:,}  added/updated: {after-before:,}")

if __name__ == "__main__":
    print("Setting up database + loading airports.csv …")
    ensure_db_exists()
    ensure_schema()
    load_csv()

