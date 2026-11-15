import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.core.game import GeometryDashGame


def main() -> None:
    config_path = os.path.join(BASE_DIR, "config", "config.json")
    game = GeometryDashGame(base_dir=BASE_DIR, config_path=config_path)
    game.run()


if __name__ == "__main__":
    main()
