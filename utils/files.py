def load_file(path):
    try:
        with open(path, "r") as f:
            return f.read().splitlines()
    except FileNotFoundError:
        return []

def save_file(path, content):
    with open(path, "w") as f:
        f.write(content)
