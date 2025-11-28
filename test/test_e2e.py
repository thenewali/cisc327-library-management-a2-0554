# test/test_e2e.py
"""
End-to-end browser tests for the Library Management System.

Flows:
1) R1: Add a book to the catalog and verify the success message.
2) R2: Borrow a book via the catalog page and verify the success flash message.
"""

import time
from playwright.sync_api import sync_playwright

# Your app (from app.py) runs on port 5000
BASE_URL = "http://127.0.0.1:5000"

# Based on your catalog and borrowing routes
ADD_BOOK_PATH   = "/add_book"   # catalog_bp.route('/add_book', methods=['GET', 'POST'])
CATALOG_PATH    = "/catalog"    # catalog_bp.route('/catalog')
BORROW_POST_URL = "/borrow"     # borrowing_bp.route('/borrow', methods=['POST'])


def test_r1_add_book_flow():
    """
    R1 flow:
    - Open Add Book page (/add_book)
    - Fill form with valid data
    - Submit
    - Check for success message from add_book_to_catalog()
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # set True to run headless if you want
        page = browser.new_page()

        # 1. Go to the Add Book page
        page.goto(f"{BASE_URL}{ADD_BOOK_PATH}")

        # 2. Fill the form
        # These names match your catalog.add_book route:
        #   title = request.form.get('title', '')
        #   author = request.form.get('author', '')
        #   isbn = request.form.get('isbn', '')
        #   total_copies = int(request.form.get('total_copies', ''))

        page.fill("input[name='title']", "E2E Test Book")
        page.fill("input[name='author']", "E2E Test Author")

        # Use a unique 13-digit ISBN each run so we don't hit "duplicate ISBN" validation
        unique_isbn = str(int(time.time() * 1000))[:13]
        page.fill("input[name='isbn']", unique_isbn)

        page.fill("input[name='total_copies']", "3")

        # 3. Submit the form
        page.click("button[type='submit']")

        # 4. Verify the success message is shown somewhere in the page body
        # library_service.add_book_to_catalog returns:
        #   Book "<title>" has been successfully added to the catalog.
        body_text = page.inner_text("body")
        assert "has been successfully added to the catalog" in body_text

        browser.close()


def test_r2_borrow_book_flow():
    """
    R2 flow:
    - Open catalog page (/catalog) that contains the borrow form.
    - Fill patron_id (6 digits) in the borrow form for a book.
    - Submit the form that posts to /borrow.
    - Check that the redirected catalog page shows the success flash message
      from borrow_book_by_patron().
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # 1. Go to the catalog page (books + borrow form)
        page.goto(f"{BASE_URL}{CATALOG_PATH}")

        # 2. Find the first borrow form on the page that posts to /borrow
        #    This assumes catalog.html has something like:
        #      <form action="/borrow" method="post"> ... </form>
        borrow_form = page.locator(f"form[action='{BORROW_POST_URL}']").first

        # 3. Fill the patron_id inside that form
        # borrowing_bp uses:
        #   patron_id = request.form.get('patron_id', '').strip()
        # So the template must have: <input name="patron_id">
        borrow_form.locator("input[name='patron_id']").fill("123456")  # must be exactly 6 digits

        # Do NOT fill book_id here:
        #   - your catalog page is already setting a hidden <input name="book_id" value="{{ book.id }}">
        #   - the previous failure showed that book_id is hidden and not editable
        # The backend will read that hidden book_id.

        # 4. Submit the borrow form
        borrow_form.locator("button[type='submit']").click()

        # 5. After submitting, borrowing_bp flashes `message` and redirects to catalog.catalog.
        # borrow_book_by_patron returns on success:
        #   Successfully borrowed "<title>". Due date: YYYY-MM-DD.
        body_text = page.inner_text("body")
        assert "Successfully borrowed" in body_text

        browser.close()
