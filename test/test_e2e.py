# End-to-end browser tests for the Library Management System.

# R1: Add a book and check the message
# R2: Borrow a book and check the flash message


# Imports
import time
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:5000"

# paths
ADD_BOOK_PATH   = "/add_book"   
CATALOG_PATH    = "/catalog"    
BORROW_POST_URL = "/borrow"     


def test_r1_add_book_flow():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  
        page = browser.new_page()

        # Goes to the add book page
        page.goto(f"{BASE_URL}{ADD_BOOK_PATH}")

        # Fills out the form
        page.fill("input[name='title']", "E2E Test Book")
        page.fill("input[name='author']", "E2E Test Author")

        unique_isbn = str(int(time.time() * 1000))[:13]
        page.fill("input[name='isbn']", unique_isbn)

        page.fill("input[name='total_copies']", "3")

        # Send the form
        page.click("button[type='submit']")

        # Message check
        body_text = page.inner_text("body")
        assert "has been successfully added to the catalog" in body_text

        browser.close()


def test_r2_borrow_book_flow():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Goes to the catalog page 
        page.goto(f"{BASE_URL}{CATALOG_PATH}")

        # Finds borrow form
        borrow_form = page.locator(f"form[action='{BORROW_POST_URL}']").first

        # Fills out the borrow form
        borrow_form.locator("input[name='patron_id']").fill("123456") 

        # Sends the borrow form
        borrow_form.locator("button[type='submit']").click()

        # Message check
        body_text = page.inner_text("body")
        assert "Successfully borrowed" in body_text

        browser.close()
