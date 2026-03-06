def display(lines):
    print("\n--- Kodin Editor ---\n")

    for i, line in enumerate(lines, start=1):
        print(f"{i:3} | {line}")

    print("\nType text to append.")
    print("Commands: :w (save) :q (quit)")
