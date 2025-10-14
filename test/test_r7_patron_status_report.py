import sqlite3
from datetime import datetime, timedelta
import library_service as svc

def setup_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE books(
            id INTEGER PRIMARY KEY, title TEXT, author TEXT, isbn TEXT,
            total_copies INTEGER, available_copies INTEGER
        );
        CREATE TABLE borrow_records(
            id INTEGER PRIMARY KEY,
            patron_id TEXT, book_id INTEGER,
            borrow_date TEXT, due_date TEXT, return_date TEXT
        );
    """)
    conn.commit()
    return conn

def patch_conn(monkeypatch, conn):
    monkeypatch.setattr(svc, "get_db_connection", lambda: conn, raising=True)

def test_report_no_records(monkeypatch):
    conn = setup_db()
    patch_conn(monkeypatch, conn)
    out = svc.get_patron_status_report("123456")
    assert out["status"] == "ok"
    assert out["summary"]["active_count"] == 0
    assert out["summary"]["lifetime_loans"] == 0
    assert out["active_loans"] == []
    assert out["recent_returns"] == []

def test_report_active_and_returned(monkeypatch):
    conn = setup_db()
    patch_conn(monkeypatch, conn)
    now = datetime.now()

    conn.execute("INSERT INTO books(id,title,author,isbn,total_copies,available_copies) VALUES(1,'Clean Code','RCM','9780132350884',1,0)")
    conn.execute("INSERT INTO books(id,title,author,isbn,total_copies,available_copies) VALUES(2,'The Pragmatic Programmer','HT','9780201616224',1,1)")

    b1 = now - timedelta(days=26)
    d1 = b1 + timedelta(days=14)
    conn.execute("""INSERT INTO borrow_records(patron_id,book_id,borrow_date,due_date,return_date)
                    VALUES(?,?,?,?,NULL)""", ("123456", 1, b1.isoformat(), d1.isoformat()))

    b2 = now - timedelta(days=20)
    d2 = b2 + timedelta(days=14)
    r2 = now - timedelta(days=2)
    conn.execute("""INSERT INTO borrow_records(patron_id,book_id,borrow_date,due_date,return_date)
                    VALUES(?,?,?,?,?)""", ("123456", 2, b2.isoformat(), d2.isoformat(), r2.isoformat()))
    conn.commit()

    out = svc.get_patron_status_report("123456")
    assert out["status"] == "ok"
    assert out["summary"]["active_count"] == 1
    assert out["summary"]["lifetime_loans"] == 2
    # Active loan fee & overdue
    active = out["active_loans"][0]
    assert active["book_id"] == 1
    assert active["days_overdue"] >= 12
    assert active["accrued_fee"] >= 8.5
    # Recent returns
    ret = out["recent_returns"][0]
    assert ret["book_id"] == 2
    assert ret["was_late"] is True
    assert ret["days_overdue"] == 6
    assert ret["fee_at_return"] == 3.0

def test_report_invalid_patron(monkeypatch):
    conn = setup_db()
    patch_conn(monkeypatch, conn)
    out = svc.get_patron_status_report("12A456")
    assert out["status"] == "error"
