from core.buffer import TextBuffer
from utils.files import load_file, save_file
from ui.render import display


class Editor:
    def __init__(self, filepath):
        self.filepath = filepath
        self.buffer = TextBuffer()

    def start(self):
        lines = load_file(self.filepath)
        self.buffer.load(lines)

        while True:
            display(self.buffer.get_lines())

            user_input = input("> ")

            if user_input == ":q":
                break

            elif user_input == ":w":
                content = self.buffer.save()
                save_file(self.filepath, content)
                print("File saved.")

            else:
                self.buffer.append(user_input)
