# Kodin - kodin.py
#
# Entry point only. Parses the filename argument, creates an Editor,
# and calls start(). All logic lives in core/ and ui/.

import sys
from core.editor import Editor


def main():
    if len(sys.argv) < 2:
        print("Usage: python kodin.py <file>")
        sys.exit(1)
    Editor(sys.argv[1]).start()


if __name__ == "__main__":
    main()
