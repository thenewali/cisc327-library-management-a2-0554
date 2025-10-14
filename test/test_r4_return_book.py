import types
from datetime import datetime
import library_service as svc

def patch_return_happy(monkeypatch):
    books = {1: {"id": 1, "title": "Clean Code", "available_copies": 0}}
    loan = {"returned_at": None}

    def get_book_by_id(book_id):
        return books.get(book_id)

    def update_borrow_record_return_date(patron_id, book_id, return_date=None):
        if patron_id != "123456" or book_id != 1 or loan["returned_at"] is not None:
            return False, "No active loan found for this patron and book."
        loan["returned_at"] = return_date or datetime.now()
        return True, "Return recorded"

    def update_book_availability(book_id, delta):
        if book_id not in books:
            return False
        books[book_id]["available_copies"] += delta
        return True

    monkeypatch.setattr(svc, "get_book_by_id", get_book_by_id)
    monkeypatch.setattr(svc, "update_borrow_record_return_date", update_borrow_record_return_date)
    monkeypatch.setattr(svc, "update_book_availability", update_book_availability)
    return books, loan

def test_return_success(monkeypatch):
    books, loan = patch_return_happy(monkeypatch)
    ok, msg = svc.return_book_by_patron("123456", 1)
    assert ok is True
    assert "returned" in msg.lower()
    assert books[1]["available_copies"] == 1
    assert loan["returned_at"] is not None

def test_return_invalid_patron(monkeypatch):
    patch_return_happy(monkeypatch)
    ok, msg = svc.return_book_by_patron("12a456", 1)
    assert ok is False and "invalid patron id" in msg.lower()

def test_return_no_active_loan(monkeypatch):
    books, loan = patch_return_happy(monkeypatch)
    loan["returned_at"] = datetime.now()
    ok, msg = svc.return_book_by_patron("123456", 1)
    assert ok is False and ("no active loan" in msg.lower() or "not" in msg.lower())
