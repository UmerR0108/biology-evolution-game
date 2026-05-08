"""Run the evogame frontend MVP — guppy + predator pressure."""
import sys
from pathlib import Path

# Allow running directly without `pip install -e .`
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from evogame.ui.app import App


def main() -> None:
    app = App()
    app.run()


if __name__ == "__main__":
    main()
