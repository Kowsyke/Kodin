# Kodin - tests/test_buffer.py
#
# Unit tests for TextBuffer. Covers initial state, loading, saving,
# all cursor movement methods, and all text mutation operations.

import pytest
from core.buffer import TextBuffer


# --- Construction and loading ---

def test_new_buffer_has_one_blank_line():
    buf = TextBuffer()
    assert buf.lines == [""]
    assert buf.cursor_y == 0
    assert buf.cursor_x == 0
    assert buf.modified is False


def test_load_sets_lines_and_resets_cursor():
    buf = TextBuffer()
    buf.load(["hello", "world"])
    assert buf.lines == ["hello", "world"]
    assert buf.cursor_y == 0
    assert buf.cursor_x == 0


def test_load_empty_list_gives_one_blank_line():
    buf = TextBuffer()
    buf.load([])
    assert buf.lines == [""]


def test_save_joins_lines_with_newlines():
    buf = TextBuffer()
    buf.load(["hello", "world"])
    assert buf.save() == "hello\nworld"


def test_save_clears_modified_flag():
    buf = TextBuffer()
    buf.load(["a"])
    buf.insert_char("x")
    assert buf.modified is True
    buf.save()
    assert buf.modified is False


# --- Cursor movement ---

def test_move_down_increments_cursor_y():
    buf = TextBuffer()
    buf.load(["line1", "line2"])
    buf.move_down()
    assert buf.cursor_y == 1


def test_move_down_clamps_at_last_line():
    buf = TextBuffer()
    buf.load(["only"])
    buf.move_down()
    assert buf.cursor_y == 0


def test_move_up_decrements_cursor_y():
    buf = TextBuffer()
    buf.load(["a", "b"])
    buf.move_down()
    buf.move_up()
    assert buf.cursor_y == 0


def test_move_up_clamps_at_first_line():
    buf = TextBuffer()
    buf.load(["a"])
    buf.move_up()
    assert buf.cursor_y == 0


def test_move_right_increments_cursor_x():
    buf = TextBuffer()
    buf.load(["hello"])
    buf.move_right()
    assert buf.cursor_x == 1


def test_move_right_at_end_of_line_wraps_to_next_line():
    buf = TextBuffer()
    buf.load(["hi", "there"])
    buf.cursor_x = 2
    buf.move_right()
    assert buf.cursor_y == 1
    assert buf.cursor_x == 0


def test_move_right_at_end_of_last_line_clamps_in_normal_mode():
    buf = TextBuffer()
    buf.load(["hi"])
    buf.cursor_x = 2
    buf.move_right()  # insert_mode=False by default
    assert buf.cursor_y == 0
    assert buf.cursor_x == 1  # clamped to len("hi") - 1


def test_move_right_at_end_of_last_line_stays_in_insert_mode():
    buf = TextBuffer()
    buf.load(["hi"])
    buf.cursor_x = 2
    buf.move_right(insert_mode=True)
    assert buf.cursor_y == 0
    assert buf.cursor_x == 2  # no clamp in insert mode


def test_move_left_decrements_cursor_x():
    buf = TextBuffer()
    buf.load(["hello"])
    buf.cursor_x = 3
    buf.move_left()
    assert buf.cursor_x == 2


def test_move_left_at_start_of_line_wraps_to_prev_line():
    buf = TextBuffer()
    buf.load(["hi", "there"])
    buf.cursor_y = 1
    buf.cursor_x = 0
    buf.move_left()
    assert buf.cursor_y == 0
    assert buf.cursor_x == 2


def test_move_left_at_start_of_first_line_does_nothing():
    buf = TextBuffer()
    buf.load(["hi"])
    buf.move_left()
    assert buf.cursor_y == 0
    assert buf.cursor_x == 0


def test_move_down_clamps_cursor_x_to_shorter_line():
    buf = TextBuffer()
    buf.load(["hello world", "hi"])
    buf.cursor_x = 8
    buf.move_down()
    assert buf.cursor_y == 1
    assert buf.cursor_x == 2


# --- Insertion ---

def test_insert_char_inserts_at_cursor():
    buf = TextBuffer()
    buf.load(["hllo"])
    buf.cursor_x = 1
    buf.insert_char("e")
    assert buf.lines[0] == "hello"
    assert buf.cursor_x == 2


def test_insert_char_sets_modified():
    buf = TextBuffer()
    buf.insert_char("a")
    assert buf.modified is True


def test_insert_char_at_start_of_line():
    buf = TextBuffer()
    buf.load(["ello"])
    buf.cursor_x = 0
    buf.insert_char("h")
    assert buf.lines[0] == "hello"
    assert buf.cursor_x == 1


def test_insert_newline_splits_line():
    buf = TextBuffer()
    buf.load(["helloworld"])
    buf.cursor_x = 5
    buf.insert_newline()
    assert buf.lines == ["hello", "world"]
    assert buf.cursor_y == 1
    assert buf.cursor_x == 0


def test_insert_newline_at_start_creates_blank_line_above():
    buf = TextBuffer()
    buf.load(["hello"])
    buf.cursor_x = 0
    buf.insert_newline()
    assert buf.lines == ["", "hello"]
    assert buf.cursor_y == 1
    assert buf.cursor_x == 0


def test_insert_newline_at_end_creates_blank_line_below():
    buf = TextBuffer()
    buf.load(["hello"])
    buf.cursor_x = 5
    buf.insert_newline()
    assert buf.lines == ["hello", ""]
    assert buf.cursor_y == 1
    assert buf.cursor_x == 0


# --- Deletion ---

def test_delete_char_removes_char_before_cursor():
    buf = TextBuffer()
    buf.load(["hello"])
    buf.cursor_x = 3
    buf.delete_char()
    assert buf.lines[0] == "helo"
    assert buf.cursor_x == 2


def test_delete_char_at_start_of_line_merges_with_prev():
    buf = TextBuffer()
    buf.load(["hello", "world"])
    buf.cursor_y = 1
    buf.cursor_x = 0
    buf.delete_char()
    assert buf.lines == ["helloworld"]
    assert buf.cursor_y == 0
    assert buf.cursor_x == 5


def test_delete_char_at_start_of_first_line_does_nothing():
    buf = TextBuffer()
    buf.load(["hello"])
    buf.cursor_y = 0
    buf.cursor_x = 0
    buf.delete_char()
    assert buf.lines == ["hello"]
    assert buf.cursor_y == 0
    assert buf.cursor_x == 0


def test_delete_char_sets_modified():
    buf = TextBuffer()
    buf.load(["ab"])
    buf.cursor_x = 1
    buf.delete_char()
    assert buf.modified is True


# --- get_lines ---

def test_get_lines_returns_current_lines():
    buf = TextBuffer()
    buf.load(["a", "b"])
    assert buf.get_lines() == ["a", "b"]


# --- delete_char_under (vim 'x') ---

def test_delete_char_under_removes_char_at_cursor():
    buf = TextBuffer()
    buf.load(["hello"])
    buf.cursor_x = 1
    buf.delete_char_under()
    assert buf.lines[0] == "hllo"
    assert buf.cursor_x == 1


def test_delete_char_under_last_char_clamps_cursor():
    buf = TextBuffer()
    buf.load(["ab"])
    buf.cursor_x = 1  # at 'b', the last char
    buf.delete_char_under()
    assert buf.lines[0] == "a"
    assert buf.cursor_x == 0  # clamped to len("a") - 1


def test_delete_char_under_on_empty_line_does_nothing():
    buf = TextBuffer()
    buf.load([""])
    buf.delete_char_under()
    assert buf.lines[0] == ""
    assert buf.cursor_x == 0


def test_delete_char_under_sets_modified():
    buf = TextBuffer()
    buf.load(["ab"])
    buf.cursor_x = 0
    buf.delete_char_under()
    assert buf.modified is True


# --- delete_line (vim 'dd') ---

def test_delete_line_removes_current_line():
    buf = TextBuffer()
    buf.load(["a", "b", "c"])
    buf.cursor_y = 1
    buf.delete_line()
    assert buf.lines == ["a", "c"]
    assert buf.cursor_y == 1


def test_delete_line_last_line_clamps_cursor_y():
    buf = TextBuffer()
    buf.load(["a", "b"])
    buf.cursor_y = 1
    buf.delete_line()
    assert buf.lines == ["a"]
    assert buf.cursor_y == 0


def test_delete_line_only_line_replaces_with_blank():
    buf = TextBuffer()
    buf.load(["hello"])
    buf.delete_line()
    assert buf.lines == [""]
    assert buf.cursor_y == 0


def test_delete_line_sets_modified():
    buf = TextBuffer()
    buf.load(["a", "b"])
    buf.delete_line()
    assert buf.modified is True


# --- open_line_below ---

def test_open_line_below_inserts_blank_line_after_current():
    buf = TextBuffer()
    buf.load(["hello", "world"])
    buf.cursor_y = 0
    buf.open_line_below()
    assert buf.lines == ["hello", "", "world"]
    assert buf.cursor_y == 1
    assert buf.cursor_x == 0


# --- open_line_above ---

def test_open_line_above_inserts_blank_line_before_current():
    buf = TextBuffer()
    buf.load(["hello", "world"])
    buf.cursor_y = 1
    buf.open_line_above()
    assert buf.lines == ["hello", "", "world"]
    assert buf.cursor_y == 1
    assert buf.cursor_x == 0


# --- jump navigation ---

def test_move_to_line_start_sets_cursor_x_to_zero():
    buf = TextBuffer()
    buf.load(["hello"])
    buf.cursor_x = 3
    buf.move_to_line_start()
    assert buf.cursor_x == 0


def test_move_to_line_end_normal_mode():
    buf = TextBuffer()
    buf.load(["hello"])
    buf.move_to_line_end()
    assert buf.cursor_x == 4  # max index = len("hello") - 1


def test_move_to_line_end_insert_mode():
    buf = TextBuffer()
    buf.load(["hello"])
    buf.move_to_line_end(insert_mode=True)
    assert buf.cursor_x == 5  # one past end, valid for insertion


def test_move_to_line_end_empty_line_normal_mode():
    buf = TextBuffer()
    buf.load([""])
    buf.move_to_line_end()
    assert buf.cursor_x == 0  # max(0 - 1, 0) = 0


def test_move_to_first_line():
    buf = TextBuffer()
    buf.load(["a", "b", "c"])
    buf.cursor_y = 2
    buf.move_to_first_line()
    assert buf.cursor_y == 0


def test_move_to_last_line():
    buf = TextBuffer()
    buf.load(["a", "b", "c"])
    buf.move_to_last_line()
    assert buf.cursor_y == 2
