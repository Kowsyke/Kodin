import sys
from utils.files import load_file, save_file

def main():
    if len(sys.argv) < 2:
        print("Kodin v0.1")
        print("Usage: python kodin.py <file>")
        return

    filename = sys.argv[1]
    buffer = load_file(filename)

    print(f"\nKodin editing: {filename}\n")

    for i, line in enumerate(buffer):
        print(f"{i+1}: {line}", end="")

    print("\nType new lines. Empty line to save and exit.\n")

    while True:
        new = input("> ")
        if new == "":
            break
        buffer.append(new + "\n")

    save_file(filename, "".join( buffer))
    print("File saved.")

if __name__ == "__main__":
    main()

