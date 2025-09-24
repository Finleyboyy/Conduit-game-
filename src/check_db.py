import os
from dotenv import load_dotenv
import mariadb

load_dotenv()

conn = mariadb.connect(
    user=os.getenv("DB_USER","gameuser"),
    password=os.getenv("DB_PASS","yourpassword"),
    host=os.getenv("DB_HOST","localhost"),
    port=int(os.getenv("DB_PORT","3306")),
    database=os.getenv("DB_NAME","conduit_game"),
)
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM airports")
print("Airports:", cur.fetchone()[0])
cur.execute("SELECT iata_code, name FROM airports WHERE iata_code='HEL'")
print("HEL row:", cur.fetchone())
conn.close()
