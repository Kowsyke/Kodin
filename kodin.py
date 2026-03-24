import sys
from utils.files import load_file, save_file

def main():

    if len(sys.argv) < 2:
        print("Kodin v0.1")
        print("Usage: python kodin.py <file>")
        return

    filename = sys.argv[1]
    buffer = load_file(filename)

    cursor_y = 0
    cursor_x = 0

    print(f"\nKodin editing: {filename}\n")

    if len(buffer) == 0:
        buffer.append("\n")

    for i, line in enumerate(buffer):
        print(f"{i+1}: {line}", end="")

    print("\nType new lines. Empty line to save and exit.\n")

    while True:
        print(f"\nCursor position: ({cursor_y}, {cursor_x})")

        command = input("> ")

        if command == "":
            break

        elif command == "j":
            cursor_y = min(cursor_y + 1, len(buffer) - 1)

        elif command == "k":
            cursor_y = max(cursor_y - 1, 0)

        elif command == "h":
            cursor_x = max(cursor_x - 1, 0)

        elif command == "l":
            cursor_x += 1

        else:
            buffer.append(command + "\n")

    save_file(filename, "".join(buffer))
    print("File saved.")

if __name__ == "__main__":
    main()

