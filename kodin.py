# Kodin - kodin.py
#
# Entry point only. Parses the optional filename argument and runs KodinApp.

import sys
from app import KodinApp


def main() -> None:
    filepath = sys.argv[1] if len(sys.argv) > 1 else None
    KodinApp(filepath=filepath).run()


if __name__ == "__main__":
    main()
