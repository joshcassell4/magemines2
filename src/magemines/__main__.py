"""Entry point for MageMines when run as a module."""

import sys
from .game.game_loop import run_game


def main() -> int:
    """Main entry point for the game."""
    try:
        run_game()
        return 0
    except KeyboardInterrupt:
        print("\nGame interrupted by user.")
        return 0
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
