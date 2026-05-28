"""Browser entrypoint for the Pygame evolution game.

Railway serves the pygbag build of this file so the game can run in a browser.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Allow pygbag/browser builds and local `python main.py` runs without an editable install.
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from evogame.ui.app import App


async def main() -> None:
    app = App()
    try:
        while app.running:
            dt_ms = app.clock.tick(60)
            app.step_one_frame(dt_ms)
            # Yield control so pygbag can keep the browser event loop responsive.
            await asyncio.sleep(0)
    finally:
        app.shutdown()


# In pygbag, ``shell.source(main.py)`` already runs inside the browser event loop.
# Scheduling the game coroutine avoids nesting ``asyncio.run`` under that loop.
if __name__ == "__main__":
    if sys.platform == "emscripten":
        asyncio.create_task(main())
    else:
        asyncio.run(main())
