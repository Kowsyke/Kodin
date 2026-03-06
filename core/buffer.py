class TextBuffer:
    def __init__(self):
        self.lines = []

    def load(self, lines):
        self.lines = list(lines)

    def append(self, text):
        self.lines.append(text)

    def get_lines(self):
        return self.lines

    def save(self):
        return "\n".join(self.lines)
