import sqlite3
from datetime import datetime, timedelta
import library_service as svc

def make_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""CREATE TABLE books (
        id INTEGER PRIMARY KEY, title TEXT, author TEXT, isbn TEXT,
        total_copies INTEGER, available_copies INTEGER)""")
    c.execute("""CREATE TABLE borrow_records (
        id INTEGER PRIMARY KEY,
        patron_id TEXT, book_id INTEGER,
        borrow_date TEXT, due_date TEXT, return_date TEXT)""")
    conn.commit()
    return conn

def seed_loan(conn, *, patron="123456", book_id=1, title="Clean Code",
              borrowed_days_ago=10, returned_days_ago=None):
    now = datetime.now()
    borrowed_at = now - timedelta(days=borrowed_days_ago)
    due_at = borrowed_at + timedelta(days=14)
    returned_at = None if returned_days_ago is None else (now - timedelta(days=returned_days_ago))
    conn.execute("INSERT INTO books(id,title,author,isbn,total_copies,available_copies) VALUES(1,?,?,?,1,0)",
                 (title, "Uncle Bob", "9780132350884"))
    conn.execute("""INSERT INTO borrow_records(patron_id,book_id,borrow_date,due_date,return_date)
                    VALUES(?,?,?,?,?)""",
                 (patron, book_id, borrowed_at.isoformat(), due_at.isoformat(),
                  None if returned_at is None else returned_at.isoformat()))
    conn.commit()
    return borrowed_at, due_at, returned_at

def patch_conn(monkeypatch, conn):
    def get_db_connection():
        return conn
    monkeypatch.setattr(svc, "get_db_connection", get_db_connection, raising=True)

def test_no_overdue_active(monkeypatch):
    conn = make_db()
    seed_loan(conn, borrowed_days_ago=10) 
    patch_conn(monkeypatch, conn)
    out = svc.calculate_late_fee_for_book("123456", 1)
    assert out["status"] == "ok" and out["days_overdue"] == 0 and out["fee_amount"] == 0.0

def test_5_days_overdue_active(monkeypatch):
    conn = make_db()
    seed_loan(conn, borrowed_days_ago=19) 
    patch_conn(monkeypatch, conn)
    out = svc.calculate_late_fee_for_book("123456", 1)
    assert out["days_overdue"] == 5 and out["fee_amount"] == 2.5

def test_12_days_overdue_returned(monkeypatch):
    conn = make_db()
    seed_loan(conn, borrowed_days_ago=26, returned_days_ago=0)
    patch_conn(monkeypatch, conn)
    out = svc.calculate_late_fee_for_book("123456", 1)
    assert out["days_overdue"] == 12 and out["fee_amount"] == 8.5

def test_cap_at_15(monkeypatch):
    conn = make_db()
    seed_loan(conn, borrowed_days_ago=80)
    patch_conn(monkeypatch, conn)
    out = svc.calculate_late_fee_for_book("123456", 1)
    assert out["fee_amount"] == 15.0

def test_invalid_patron(monkeypatch):
    conn = make_db()
    seed_loan(conn)
    patch_conn(monkeypatch, conn)
    out = svc.calculate_late_fee_for_book("12a456", 1)
    assert out["status"] == "error" and "invalid patron id" in out["message"].lower()

def test_no_loan(monkeypatch):
    conn = make_db()
    patch_conn(monkeypatch, conn)
    out = svc.calculate_late_fee_for_book("123456", 1)
    assert out["status"] == "error" and "no loan" in out["message"].lower()
