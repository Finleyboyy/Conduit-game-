# game_db.py — minimal, readable prototype (single file)
# Flow:
#   • Start at HEL (not part of the 10 travel options)
#   • Each run: pick 10 random airports (excluding HEL); 5 are secret conduits
#   • Menu shows only: Travel, Inventory, Help, Quit
#   • Inventory shows: Markka, and the 10 airports with distance + travel cost
#   • After arriving at a conduit airport: "You feel a strange presence here."
#     -> then (and only then) ask to close it

import sys
import random
from dataclasses import dataclass
from typing import List, Tuple, Optional

import mariadb
from geopy.distance import geodesic  # pip install geopy


# --------- Tunables (easy to tweak later) ----------
RATE_PER_KM = 0.5         # Markka per km, lower this value to make it cheaper to travel
REWARD_MARKKA = 100       # reward for closing a conduit
SANITY_LOSS = 5           # sanity penalty when closing a conduit
START_MARKKA = 500        # starting money
START_SANITY = 100        # shown nowhere; kept for future use


# --------- Database connection ----------
def get_connection():
    try:
        return mariadb.connect(
            user="gameuser",
            password="yourpassword",   # <-- CHANGE ME
            host="localhost",
            database="conduit_game",
            port=3306,
        )
    except mariadb.Error as e:
        print(f"DB connect error: {e}")
        sys.exit(1)


# --------- Database queries ----------
def fetch_hel() -> Tuple[int, str, str, str, Optional[float], Optional[float]]:
    """Return HEL row as (id, name, iata, country, lat, lon)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, iata_code, iso_country, latitude_deg, longitude_deg
        FROM airports
        WHERE iata_code = 'HEL'
        LIMIT 1;
    """)
    row = cur.fetchone()
    conn.close()
    if not row:
        raise RuntimeError("HEL not found in database.")
    return row


def fetch_random_airports_excl_hel(n: int = 10) -> List[Tuple[int, str, str, str, Optional[float], Optional[float]]]:
    """Return n random airports excluding HEL. Each row: (id, name, iata, country, lat, lon)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"""
        SELECT id, name, iata_code, iso_country, latitude_deg, longitude_deg
        FROM airports
        WHERE iata_code <> 'HEL'
        ORDER BY RAND()
        LIMIT {int(n)};
    """)
    rows = cur.fetchall()
    conn.close()
    return rows


# --------- In-memory state ----------
@dataclass
class AirportChoice:
    id: int
    name: str
    iata: str
    country: str
    lat: Optional[float]
    lon: Optional[float]
    conduit: bool = False
    visited: bool = False
    conduit_closed: bool = False


@dataclass
class RunState:
    # current location (starts at HEL; HEL is not in airports list)
    current_id: int
    current_name: str
    current_iata: str
    current_country: str
    current_lat: Optional[float]
    current_lon: Optional[float]

    # the 10 choices for this run (excluding HEL)
    airports: List[AirportChoice]

    # player stats
    markka: int = START_MARKKA
    sanity: int = START_SANITY


def start_new_run(seed: int | None = None) -> RunState:
    """Make a new run: HEL start, 10 random airports (excluding HEL), 5 hidden conduits."""
    hel_id, hel_name, hel_iata, hel_country, hel_lat, hel_lon = fetch_hel()
    rows = fetch_random_airports_excl_hel(10)
    choices = [AirportChoice(*r) for r in rows]

    rng = random.Random(seed) if seed is not None else random
    for idx in rng.sample(range(len(choices)), 5):
        choices[idx].conduit = True

    return RunState(
        current_id=hel_id,
        current_name=hel_name,
        current_iata=hel_iata,
        current_country=hel_country,
        current_lat=hel_lat,
        current_lon=hel_lon,
        airports=choices,
        markka=START_MARKKA,
        sanity=START_SANITY,
    )


# --------- Simple helpers ----------
def _coords_of(lat: Optional[float], lon: Optional[float]) -> Optional[tuple[float, float]]:
    if lat is None or lon is None:
        return None
    return (lat, lon)


def _coords_current(state: RunState) -> Optional[tuple[float, float]]:
    return _coords_of(state.current_lat, state.current_lon)


def _coords_airport(a: AirportChoice) -> Optional[tuple[float, float]]:
    return _coords_of(a.lat, a.lon)


def distance_km(state: RunState, a: AirportChoice) -> Optional[float]:
    cur = _coords_current(state)
    tgt = _coords_airport(a)
    if cur is None or tgt is None:
        return None
    return geodesic(cur, tgt).km


def travel_cost_from_current(state: RunState, a: AirportChoice, rate: float = RATE_PER_KM) -> Optional[int]:
    km = distance_km(state, a)
    if km is None:
        return None
    return max(1, int(round(rate * km)))


# --------- Inventory & UI prints (minimal) ----------
def show_inventory(state: RunState):
    print("\n=== INVENTORY ===")
    print(f"Markka: {state.markka}")
    cur_coords = _coords_current(state)
    print("\nDestinations (distance / cost):")
    for i, a in enumerate(state.airports, start=1):
        km = distance_km(state, a)
        cost = travel_cost_from_current(state, a)
        km_txt = f"{km:.0f} km" if km is not None else "N/A"
        cost_txt = f"{cost} Markka" if cost is not None else "N/A"
        print(f"{i:2d}. {a.name} ({a.iata or '—'}, {a.country}) — {km_txt} — {cost_txt}")
    print("==================")


def show_help():
    print(f"""
HELP
  T : Travel
  I : Inventory (shows Markka and 10 airports with distance & cost)
  H : Help
  Q : Quit

Notes
  • Start at HEL (Helsinki-Vantaa). HEL is not in the 10; you cannot return to HEL.
  • 10 airports each run (excluding HEL); 5 are secret conduits.
  • Travel cost = {RATE_PER_KM} Markka per km (rounded, min 1).
  • You only learn a conduit is present after you arrive.
""")


def show_menu():
    print("\nChoose: [T]ravel  [I]nventory  [H]elp  [Q]uit")


def show_travel_options(state: RunState):
    print("\nDestinations (choose 1..10):")
    for i, a in enumerate(state.airports, start=1):
        km = distance_km(state, a)
        cost = travel_cost_from_current(state, a)
        km_txt = f"{km:.0f} km" if km is not None else "N/A"
        cost_txt = f"{cost} Markka" if cost is not None else "N/A"
        print(f"{i:2d}. {a.name} ({a.iata or '—'}, {a.country}) — {km_txt} — {cost_txt}")


# --------- Game actions ----------
def travel_to_index(state: RunState, idx: int) -> str:
    """Attempt travel to airport #idx (1..10). On success, update current location and return a short message."""
    if not 1 <= idx <= len(state.airports):
        return "Out of range (choose 1..10)."

    a = state.airports[idx - 1]
    km = distance_km(state, a)
    cost = travel_cost_from_current(state, a)

    if km is None or cost is None:
        return "Cannot compute distance/cost for that route."
    if state.markka < cost:
        return f"Not enough Markka (need {cost}, have {state.markka})."

    # pay & move
    state.markka -= cost
    state.current_id = a.id
    state.current_name = a.name
    state.current_iata = a.iata
    state.current_country = a.country
    state.current_lat = a.lat
    state.current_lon = a.lon
    a.visited = True

    msg = f"Arrived at {a.name} ({a.iata or '—'}, {a.country})."
    # Presence reveal (no hints before arrival)
    if a.conduit and not a.conduit_closed:
        msg += " You feel a strange presence here."
        # Ask to close right now
        choice = input("Close the conduit now? (Y/N): ").strip().lower()
        if choice == "y":
            a.conduit_closed = True
            state.markka += REWARD_MARKKA
            state.sanity = max(0, state.sanity - SANITY_LOSS)
            msg += f" Conduit CLOSED (+{REWARD_MARKKA} Markka, -{SANITY_LOSS} Sanity)."
        else:
            msg += " You leave it be… for now."
    return msg


# --------- Main loop ----------
def main():
    print("Welcome to HELL")
    state = start_new_run()

    while True:
        show_menu()
        cmd = input("> ").strip().lower()

        if cmd == "q":
            print("Goodbye.")
            break

        elif cmd == "h":
            show_help()

        elif cmd == "i":
            show_inventory(state)

        elif cmd == "t":
            show_travel_options(state)
            sel = input("Go to (1-10): ").strip()
            if sel.isdigit():
                idx = int(sel)
                print(travel_to_index(state, idx))
            else:
                print("Please enter a number between 1 and 10.")

        else:
            print("Unknown command. Use T, I, H, or Q.")


if __name__ == "__main__":
    main()
