import library_service as svc

def test_search_title_case_insensitive(monkeypatch):
    books = [
        {"id": 1, "title": "The Hobbit", "author": "J.R.R. Tolkien", "isbn": "9780547928227"},
        {"id": 2, "title": "Clean Code", "author": "Robert C. Martin", "isbn": "9780132350884"},
    ]
    monkeypatch.setattr(svc, "get_all_books", lambda: books)
    out = svc.search_books_in_catalog("hobbit", "title")
    assert [b["id"] for b in out] == [1]

def test_search_author(monkeypatch):
    books = [
        {"id": 1, "title": "Test", "author": "A. Author", "isbn": "111"},
        {"id": 2, "title": "Another", "author": "Mark Twain", "isbn": "222"},
    ]
    monkeypatch.setattr(svc, "get_all_books", lambda: books)
    out = svc.search_books_in_catalog("twain", "author")
    assert len(out) == 1 and out[0]["id"] == 2

def test_search_isbn_digits_only(monkeypatch):
    books = [{"id": 1, "title": "X", "author": "Y", "isbn": "978-0-13-235088-4"}]
    monkeypatch.setattr(svc, "get_all_books", lambda: books)
    out = svc.search_books_in_catalog("0132350884", "isbn")
    assert len(out) == 1 and out[0]["id"] == 1

def test_search_empty_term(monkeypatch):
    monkeypatch.setattr(svc, "get_all_books", lambda: [{"id": 1}])
    assert svc.search_books_in_catalog("   ", "title") == []

def test_search_invalid_type_defaults_to_title(monkeypatch):
    books = [{"id": 1, "title": "Alpha", "author": "Beta", "isbn": "123"}]
    monkeypatch.setattr(svc, "get_all_books", lambda: books)
    out = svc.search_books_in_catalog("alp", "nope")
    assert len(out) == 1 and out[0]["id"] == 1
