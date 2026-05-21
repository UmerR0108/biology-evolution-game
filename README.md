# evogame

AP Biology evolution simulation game.

## Setup

    python -m pip install -e ".[dev]"

## Run the game

    python scripts/run_game.py

You play a field researcher in a forest with a pond. Walk around with WASD or arrows; bunnies wander the grass; guppies (color-tinted by phenotype) drift in the pond. Walk to the cottage and press E (or J anywhere) to open the Field Journal, where the predator toggle and live allele-frequency chart live.

## Controls

- WASD / arrow keys — walk
- E — interact (near the cottage opens the Field Journal)
- J — toggle Field Journal from anywhere
- ESC — close journal, or quit if journal is closed

## Run tests

    pytest

## Run the breeding demo

    python scripts/breed_demo.py
