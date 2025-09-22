import csv
import mariadb
import sys
from pathlib import Path

CSV_FILE = Path(r"C:\Users\jackm\conduit_game\data\airports.csv")

def main():
    try:
        conn = mariadb.connect(
            user="gameuser",
            password="yourpassword",  # <-- change this
            host="localhost",
            port=3306,
            database="conduit_game"
        )
    except mariadb.Error as e:
        print(f"Error connecting: {e}")
        sys.exit(1)

    cur = conn.cursor()

    try:
        with CSV_FILE.open(newline='', encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = []
            for r in reader:
                rows.append((
                    int(r["id"]) if r["id"] else None,
                    r.get("ident"),
                    r.get("type"),
                    r.get("name"),
                    float(r["latitude_deg"]) if r.get("latitude_deg") else None,
                    float(r["longitude_deg"]) if r.get("longitude_deg") else None,
                    int(float(r["elevation_ft"])) if r.get("elevation_ft") else None,
                    r.get("continent"),
                    r.get("iso_country"),
                    r.get("iso_region"),
                    r.get("municipality"),
                    r.get("scheduled_service"),
                    r.get("gps_code"),
                    r.get("iata_code"),
                    r.get("local_code"),
                    r.get("home_link"),
                    r.get("wikipedia_link"),
                    r.get("keywords"),
                ))

        cur.executemany("""
            INSERT INTO airports (
                id, ident, type, name, latitude_deg, longitude_deg, elevation_ft,
                continent, iso_country, iso_region, municipality, scheduled_service,
                gps_code, iata_code, local_code, home_link, wikipedia_link, keywords
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, rows)
        conn.commit()
        print(f"Inserted {len(rows)} rows.")
    except FileNotFoundError:
        print(f"CSV not found at: {CSV_FILE}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()
