import pytest
import services.library_service as svc

def test_add_book_valid_input(monkeypatch):
    monkeypatch.setattr(svc, "insert_book", lambda title, author, isbn, total, available: True, raising=False)
    monkeypatch.setattr(svc, "get_book_by_isbn", lambda isbn: None, raising=False)

    ok, msg = svc.add_book_to_catalog("Test Book", "Test Author", "1234567890123", 5)
    assert ok is True

def test_add_book_isbn_length_only(monkeypatch):
    monkeypatch.setattr(svc, "insert_book", lambda *a, **k: True, raising=False)
    monkeypatch.setattr(svc, "get_book_by_isbn", lambda isbn: None, raising=False)

    ok, msg = svc.add_book_to_catalog("Percy Jackson", "Rick Riordan", "123456789012a", 1)
    assert ok is True

def test_add_book_db_error_bubbles_up(monkeypatch):
    monkeypatch.setattr(svc, "insert_book", lambda *a, **k: False, raising=False)
    monkeypatch.setattr(svc, "get_book_by_isbn", lambda isbn: None, raising=False)

    ok, msg = svc.add_book_to_catalog("Any", "Any", "1234567890123", 1)
    assert ok is False

def test_add_book_title_too_long():
    long_title = "x" * 201
    ok, msg = svc.add_book_to_catalog(long_title, "Author", "1234567890123", 5)
    assert ok is False
    assert msg == "Title must be less than 200 characters."

def test_add_book_missing_author():
    ok, msg = svc.add_book_to_catalog("Title", "   ", "1234567890123", 5)
    assert ok is False
    assert msg == "Author is required."

def test_add_book_author_too_long():
    long_author = "y" * 101
    ok, msg = svc.add_book_to_catalog("Title", long_author, "1234567890123", 5)
    assert ok is False
    assert msg == "Author must be less than 100 characters."
