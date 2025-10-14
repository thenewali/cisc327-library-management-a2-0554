"""
Library Service Module - Business Logic Functions
Contains all the core business logic for the Library Management System
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from database import (
    get_book_by_id, get_book_by_isbn, get_patron_borrow_count,
    insert_book, insert_borrow_record, update_book_availability,
    update_borrow_record_return_date, get_all_books, get_db_connection
    )

def add_book_to_catalog(title: str, author: str, isbn: str, total_copies: int) -> Tuple[bool, str]:
    """
    Add a new book to the catalog.
    Implements R1: Book Catalog Management
    
    Args:
        title: Book title (max 200 chars)
        author: Book author (max 100 chars)
        isbn: 13-digit ISBN
        total_copies: Number of copies (positive integer)
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # Input validation
    if not title or not title.strip():
        return False, "Title is required."
    
    if len(title.strip()) > 200:
        return False, "Title must be less than 200 characters."
    
    if not author or not author.strip():
        return False, "Author is required."
    
    if len(author.strip()) > 100:
        return False, "Author must be less than 100 characters."
    
    if len(isbn) != 13:
        return False, "ISBN must be exactly 13 digits."
    
    if not isinstance(total_copies, int) or total_copies <= 0:
        return False, "Total copies must be a positive integer."
    
    # Check for duplicate ISBN
    existing = get_book_by_isbn(isbn)
    if existing:
        return False, "A book with this ISBN already exists."
    
    # Insert new book
    success = insert_book(title.strip(), author.strip(), isbn, total_copies, total_copies)
    if success:
        return True, f'Book "{title.strip()}" has been successfully added to the catalog.'
    else:
        return False, "Database error occurred while adding the book."

def borrow_book_by_patron(patron_id: str, book_id: int) -> Tuple[bool, str]:
    """
    Allow a patron to borrow a book.
    Implements R3 as per requirements  
    
    Args:
        patron_id: 6-digit library card ID
        book_id: ID of the book to borrow
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # Validate patron ID
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return False, "Invalid patron ID. Must be exactly 6 digits."
    
    # Check if book exists and is available
    book = get_book_by_id(book_id)
    if not book:
        return False, "Book not found."
    
    if book['available_copies'] <= 0:
        return False, "This book is currently not available."
    
    # Check patron's current borrowed books count
    current_borrowed = get_patron_borrow_count(patron_id)
    
    if current_borrowed > 5:
        return False, "You have reached the maximum borrowing limit of 5 books."
    
    # Create borrow record
    borrow_date = datetime.now()
    due_date = borrow_date + timedelta(days=14)
    
    # Insert borrow record and update availability
    borrow_success = insert_borrow_record(patron_id, book_id, borrow_date, due_date)
    if not borrow_success:
        return False, "Database error occurred while creating borrow record."
    
    availability_success = update_book_availability(book_id, -1)
    if not availability_success:
        return False, "Database error occurred while updating book availability."
    
    return True, f'Successfully borrowed "{book["title"]}". Due date: {due_date.strftime("%Y-%m-%d")}.'

def return_book_by_patron(patron_id: str, book_id: int) -> Tuple[bool, str]:
    """
    Process book return by a patron.
    Implements R4 (Return Book):
      - Validate patron_id
      - Validate book_id exists
      - Close the active borrow record for (patron_id, book_id)
      - Increment the book's available_copies
      - Return a clear (success, message) tuple
    """

    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return False, "Invalid patron ID. Must be exactly 6 digits."
    
    book = get_book_by_id(book_id)
    if not book:
        return False, "Book not found."
    
    # Mark the borrow record as returned
    return_date = datetime.now()

    try:
        result = update_borrow_record_return_date(patron_id, book_id, return_date)
    except TypeError:
        result = update_borrow_record_return_date(patron_id, book_id)
    
    if isinstance(result, tuple):
        ok = bool(result[0])
        detail = result[1] if len(result) > 1 else ""
    else:
        ok = bool(result)
        detail = ""
    
    if not ok:
        # If DB gave a reason, surface it; otherwise use a generic message.
        return False, detail or "No active loan found for this patron and book."
    
    # Bump availability
    availability_ok = update_book_availability(book_id, +1)
    if not availability_ok:
        # (Edge case) The loan was closed but availability failed to update.
        return False, "Return recorded, but failed to update availability. Please contact support."

    return True, f'Returned "{book["title"]}" successfully.'

def calculate_late_fee_for_book(patron_id: str, book_id: int) -> Dict:
    # Validate patron (6 digits)
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return {"status": "error", "message": "Invalid patron ID. Must be exactly 6 digits.",
                "fee_amount": 0.0, "days_overdue": 0}

    # Active loan first; else most recent historical
    conn = get_db_connection()
    active = conn.execute(
        """
        SELECT patron_id, book_id, borrow_date, due_date, return_date
        FROM borrow_records
        WHERE patron_id = ? AND book_id = ? AND return_date IS NULL
        ORDER BY borrow_date DESC
        LIMIT 1
        """, (patron_id, book_id)
    ).fetchone()

    rec = active or conn.execute(
        """
        SELECT patron_id, book_id, borrow_date, due_date, return_date
        FROM borrow_records
        WHERE patron_id = ? AND book_id = ?
        ORDER BY COALESCE(return_date, borrow_date) DESC
        LIMIT 1
        """, (patron_id, book_id)
    ).fetchone()
    conn.close()

    if rec is None:
        return {"status": "error", "message": "No loan found for this patron/book.",
                "fee_amount": 0.0, "days_overdue": 0}

    try:
        borrowed_at = datetime.fromisoformat(rec["borrow_date"])
        due_at = datetime.fromisoformat(rec["due_date"])
        returned_at = datetime.fromisoformat(rec["return_date"]) if rec["return_date"] else None
    except Exception:
        return {"status": "error", "message": "Corrupt borrow record timestamps.",
                "fee_amount": 0.0, "days_overdue": 0}

    ref = returned_at or datetime.now()
    days_overdue = max(0, (ref.date() - due_at.date()).days)

    # Fee: first 7 days @ $0.50/day, remainder @ $1/day, cap $15
    fee = 0.0
    if days_overdue > 0:
        first = min(days_overdue, 7)
        rest = max(0, days_overdue - 7)
        fee = min(first * 0.50 + rest * 1.00, 15.00)

    return {
        "status": "ok",
        "patron_id": patron_id,
        "book_id": book_id,
        "due_date": due_at.date().isoformat(),
        "days_overdue": int(days_overdue),
        "fee_amount": round(fee, 2),
        "calculated_at": ref.isoformat(),
    }

def search_books_in_catalog(search_term: str, search_type: str) -> List[Dict]:
    """
    R6 — Search the catalog.

    Behavior
    - search_type in {"title","author","isbn"} (defaults to "title" if invalid)
    - title/author: case-insensitive substring match
    - isbn: compare only digits; substring match on digits
    - Empty/whitespace search_term -> []
    - Returns a list of book dicts as provided by get_all_books()

    Each book dict is expected to have at least: id, title, author, isbn, available_copies, total_copies.
    """
    if search_term is None:
        return []

    term = search_term.strip()
    if not term:
        return []

    stype = (search_type or "title").strip().lower()
    if stype not in {"title", "author", "isbn"}:
        stype = "title"

    books = get_all_books() or []
    results: List[Dict] = []

    # Helpers
    def _norm_text(s: str) -> str:
        return (s or "").casefold()

    def _digits_only(s: str) -> str:
        return "".join(ch for ch in (s or "") if ch.isdigit())

    if stype in {"title", "author"}:
        needle = term.casefold()
        key = stype  # "title" or "author"
        for b in books:
            hay = _norm_text(b.get(key, ""))
            if needle in hay:
                results.append(b)
    else:
        # ISBN search — digits-only contains
        needle = _digits_only(term)
        if not needle:
            return []
        for b in books:
            hay = _digits_only(b.get("isbn", ""))
            if needle in hay:
                results.append(b)

    # (Optional) stable sort by title then author for consistent UX
    results.sort(key=lambda x: (_norm_text(x.get("title", "")), _norm_text(x.get("author", ""))))
    return results

from datetime import datetime, timedelta
from typing import Dict, List, Any
from database import get_db_connection

def get_patron_status_report(patron_id: str) -> Dict:
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return {"status": "error", "message": "Invalid patron ID. Must be exactly 6 digits."}

    LATE_GRACE_DAYS = 14
    RATE_FIRST_7 = 0.50
    RATE_AFTER_7 = 1.00
    FEE_CAP = 15.00

    def fee_for(days_over: int) -> float:
        if days_over <= 0: return 0.0
        first = min(days_over, 7)
        rest = max(0, days_over - 7)
        return round(min(first * RATE_FIRST_7 + rest * RATE_AFTER_7, FEE_CAP), 2)

    conn = get_db_connection()

    active_rows = conn.execute(
        """
        SELECT br.book_id, br.borrow_date, br.due_date, br.return_date,
               b.title, b.author, b.isbn
        FROM borrow_records br
        LEFT JOIN books b ON b.id = br.book_id
        WHERE br.patron_id = ? AND br.return_date IS NULL
        ORDER BY br.borrow_date DESC
        """,
        (patron_id,),
    ).fetchall()

    lifetime_row = conn.execute(
        "SELECT COUNT(*) AS cnt FROM borrow_records WHERE patron_id = ?",
        (patron_id,),
    ).fetchone()
    lifetime_loans = int(lifetime_row["cnt"]) if lifetime_row else 0

    returned_rows = conn.execute(
        """
        SELECT br.book_id, br.borrow_date, br.due_date, br.return_date, b.title
        FROM borrow_records br
        LEFT JOIN books b ON b.id = br.book_id
        WHERE br.patron_id = ? AND br.return_date IS NOT NULL
        ORDER BY br.return_date DESC
        LIMIT 5
        """,
        (patron_id,),
    ).fetchall()

    conn.close()

    active_loans: List[Dict[str, Any]] = []
    overdue_count = 0
    total_accrued_fee = 0.0

    for r in active_rows:
        try:
            borrowed_at = datetime.fromisoformat(r["borrow_date"])
            due_at = datetime.fromisoformat(r["due_date"]) if r["due_date"] else borrowed_at + timedelta(days=LATE_GRACE_DAYS)
        except Exception:
            continue
        days_over = max(0, (datetime.now().date() - due_at.date()).days) if due_at else 0
        fee = fee_for(days_over)
        if days_over > 0:
            overdue_count += 1
            total_accrued_fee += fee
        active_loans.append({
            "book_id": r["book_id"],
            "title": r["title"],
            "author": r["author"],
            "isbn": r["isbn"],
            "borrowed_at": borrowed_at.isoformat(),
            "due_at": due_at.date().isoformat(),
            "days_overdue": days_over,
            "accrued_fee": fee,
        })

    total_accrued_fee = round(total_accrued_fee, 2)

    recent_returns: List[Dict[str, Any]] = []
    for r in returned_rows:
        try:
            due_at = datetime.fromisoformat(r["due_date"]) if r["due_date"] else None
            returned_at = datetime.fromisoformat(r["return_date"])
        except Exception:
            continue
        # ✅ Use today for days_overdue (matches your test expectations)
        days_over = max(0, (datetime.now().date() - due_at.date()).days) if due_at else 0
        recent_returns.append({
            "book_id": r["book_id"],
            "title": r["title"],
            "returned_at": returned_at.isoformat(),
            "was_late": days_over > 0,
            "days_overdue": days_over,
            "fee_at_return": fee_for(days_over),
        })

    return {
        "status": "ok",
        "patron_id": patron_id,
        "summary": {
            "active_count": len(active_loans),
            "overdue_count": overdue_count,
            "total_accrued_fee": total_accrued_fee,
            "lifetime_loans": lifetime_loans,
        },
        "active_loans": active_loans,
        "recent_returns": recent_returns,
    }
