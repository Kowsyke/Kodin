# Kodin - utils/files.py
#
# Stateless file I/O utilities. load_file reads a file into a list of
# strings (one per line, no trailing newlines). save_file writes a string
# to disk, overwriting whatever was there. No editor state, no side effects.


def load_file(path):
    try:
        with open(path, "r") as f:
            return f.read().splitlines()
    except FileNotFoundError:
        return []

def save_file(path, content):
    with open(path, "w") as f:
        f.write(content)
