# evogame

AP Biology evolution simulation game.

## Setup

    python -m pip install -e ".[dev]"

## Run the game

    uv run python scripts/run_game.py

You play a field researcher in a forest with a pond. Walk around with WASD or arrows; bunnies wander the grass and gain a gold observation ring when close enough to study; guppies (color-tinted by phenotype) drift in the pond. Walk to the cottage or pond and press E/Enter (or J anywhere) to open the Field Journal, where the predator toggle, live allele-frequency chart, selected-gene notes, and field observation notes live. Use Tab, the numbered shortcuts, click signposts, or click the small area map in the upper-right to travel between Home, Pond, and Forest.

## Controls

- WASD / arrow keys — walk
- Hold Shift — sprint while exploring
- E / Enter — interact near the cottage, research pond, area exits, or highlighted wildlife
- J — toggle Field Journal from anywhere
- Space — start/stop generations while the journal is open
- N — advance exactly one generation while the journal is open and paused
- G — cycle the journal chart through tracked genes
- 1-4 while journal is open — jump directly to a tracked gene chart
- Click the journal gene tabs — switch the live allele-frequency chart
- +/- or mouse wheel — adjust generation speed while the journal is open
- PgUp / PgDn — scroll long journal observation notes
- Home / End — jump to the top or bottom of long journal observation notes
- P — toggle predators while the journal is open
- R — reset the current research run while the journal is open
- 1 / H, 2 / P, 3 / F — jump to Home, Pond, or Forest
- Tab — cycle to the next field site (Home → Pond → Forest)
- Click signposts or the upper-right area map — travel between field areas
- ESC — close journal, or quit if journal is closed

## Run tests

    uv run pytest -q

## Run the breeding demo

    python scripts/breed_demo.py
