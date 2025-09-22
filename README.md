Conduit Game

A text-based horror survival game where the player must travel between airports to find and close mysterious conduits hidden across the world.

🎮 Gameplay Overview

The player always starts at HEL Airport (Helsinki, Finland).

At the beginning of each run, 10 random airports are selected from the global database.

5 of these airports secretly contain conduits that the player must discover and close.

Travel costs Markka (in-game currency), and distance between airports affects the price.

Players can access their Inventory at any time to:

View the “Bloody Note” (which lists the 10 airports in play).

Check Markka balance, sanity, and other items (weapons, potions, etc. — being developed).

Press [I] for Inventory, [H] for Help, or [Q] to quit the game.

🗄️ Tech Details

Written in Python 3.13.

Uses MariaDB to store airport and run data.

Future expansions include combat and sanity systems handled by other team members.

🚀 Setup

Clone this repository:

git clone https://github.com/Finleyboyy/Conduit-game-.git


Install requirements:

pip install mariadb geopy


Load the airports CSV into MariaDB (see src/load_airports.py).

Run the game:

python src/game_db.py

📌 Notes

This is a collaborative project, different members are handling different systems (combat, doom clock, inventory expansion, etc).

The database ensures every playthrough is fresh and randomized.
