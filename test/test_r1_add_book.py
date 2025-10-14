import pytest
import library_service as svc

def test_add_book_valid_input(monkeypatch):
    monkeypatch.setattr(svc, "insert_book", lambda title, author, isbn, total, available: True, raising=False)
    monkeypatch.setattr(svc, "get_book_by_isbn", lambda isbn: None, raising=False)

    ok, msg = svc.add_book_to_catalog("Test Book", "Test Author", "1234567890123", 5)
    assert ok is True

def test_add_book_isbn_length_only(monkeypatch):
    """
    Starter R1 usually checks only LENGTH==13 (not all-digits).
    So a 13-char value with a letter should still pass in the given code.
    """
    monkeypatch.setattr(svc, "insert_book", lambda *a, **k: True, raising=False)
    monkeypatch.setattr(svc, "get_book_by_isbn", lambda isbn: None, raising=False)

    ok, msg = svc.add_book_to_catalog("Percy Jackson", "Rick Riordan", "123456789012a", 1)
    assert ok is True

def test_add_book_db_error_bubbles_up(monkeypatch):
    monkeypatch.setattr(svc, "insert_book", lambda *a, **k: False, raising=False)
    monkeypatch.setattr(svc, "get_book_by_isbn", lambda isbn: None, raising=False)

    ok, msg = svc.add_book_to_catalog("Any", "Any", "1234567890123", 1)
    assert ok is False
