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


def _show_browser_exception(message: str) -> None:
    """Surface pygbag/browser startup failures on the page instead of a gray canvas."""
    if sys.platform != "emscripten":
        return
    try:
        import platform

        infobox = platform.window.infobox
        infobox.style.display = "block"
        infobox.style.whiteSpace = "pre-wrap"
        infobox.innerText = message
    except Exception:
        # If the browser host objects are not ready, keep the original exception.
        return


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


async def browser_main() -> None:
    """Run the game under pygbag and keep async task exceptions visible."""
    try:
        await main()
    except Exception:
        import traceback

        _show_browser_exception(traceback.format_exc())
        raise


if __name__ == "__main__":
    if sys.platform == "emscripten":
        # Keep the browser entrypoint in pygbag's normal asyncio.run(...) shape.
        # The loader patch hides the gray infobox before awaiting this long-lived
        # coroutine, so the game can draw while startup exceptions still surface.
        asyncio.run(browser_main())
    else:
        asyncio.run(main())
