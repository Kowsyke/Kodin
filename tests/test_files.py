import os
import tempfile
import pytest
from utils.files import load_file, save_file


def test_load_file_returns_list_of_strings(tmp_path):
    f = tmp_path / "sample.txt"
    f.write_text("hello\nworld\n")
    result = load_file(str(f))
    assert result == ["hello", "world"]


def test_load_file_missing_file_returns_empty_list():
    result = load_file("/tmp/kodin_nonexistent_xyz.txt")
    assert result == []


def test_load_file_empty_file_returns_empty_list(tmp_path):
    f = tmp_path / "empty.txt"
    f.write_text("")
    result = load_file(str(f))
    assert result == []


def test_save_file_writes_content(tmp_path):
    f = tmp_path / "out.txt"
    save_file(str(f), "line1\nline2")
    assert f.read_text() == "line1\nline2"


def test_save_file_overwrites_existing_content(tmp_path):
    f = tmp_path / "out.txt"
    f.write_text("old content")
    save_file(str(f), "new content")
    assert f.read_text() == "new content"
