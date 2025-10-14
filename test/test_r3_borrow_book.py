import pytest
from datetime import datetime, timedelta
import library_service as svc

def _ok_insert_borrow(patron_id, book_id, borrow_date, due_date):
    return True

def _ok_update_availability(book_id, delta):
    return True

def test_borrow_happy_path_allows_when_have_5_already(monkeypatch):
    """
    Starters commonly block at >5 (not >=5), so having exactly 5 should still pass.
    """
    # book exists and has copies
    monkeypatch.setattr(svc, "get_book_by_id",
                        lambda bid: {"id": bid, "title": "Clean Code", "available_copies": 2}, raising=False)
    # patron currently has 5 -> allowed if impl uses (> 5)
    monkeypatch.setattr(svc, "get_patron_borrow_count", lambda pid: 5, raising=False)
    monkeypatch.setattr(svc, "insert_borrow_record", _ok_insert_borrow, raising=False)
    monkeypatch.setattr(svc, "update_book_availability", _ok_update_availability, raising=False)

    ok, msg = svc.borrow_book_by_patron("123456", 1)
    assert ok is True

def test_borrow_rejects_when_no_copies(monkeypatch):
    monkeypatch.setattr(svc, "get_book_by_id",
                        lambda bid: {"id": bid, "title": "Clean Code", "available_copies": 0}, raising=False)
    monkeypatch.setattr(svc, "get_patron_borrow_count", lambda pid: 0, raising=False)

    ok, msg = svc.borrow_book_by_patron("123456", 1)
    assert ok is False and "not available" in msg.lower()

def test_borrow_invalid_patron(monkeypatch):
    ok, msg = svc.borrow_book_by_patron("12A456", 1)
    assert ok is False and "invalid patron id" in msg.lower()

def test_borrow_hits_db_error(monkeypatch):
    # book ok
    monkeypatch.setattr(svc, "get_book_by_id",
                        lambda bid: {"id": bid, "title": "Clean Code", "available_copies": 1}, raising=False)
    monkeypatch.setattr(svc, "get_patron_borrow_count", lambda pid: 0, raising=False)
    # simulate DB insert failure
    monkeypatch.setattr(svc, "insert_borrow_record", lambda *a, **k: False, raising=False)

    ok, msg = svc.borrow_book_by_patron("123456", 1)
    assert ok is False and "database error" in msg.lower()
