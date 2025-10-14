# Assignment 1
**Name:** Ali Nadeem  
**Student ID:** 20410554
**Group:** 3

---

## 1. QA Report

### R1: Add new books
| Function Name                      | Implementation Status | What is Missing |
|-----------------------------------|-----------------------|-----------------|
| `library_service.add_book_to_catalog` | Partial | Only checks length of ISBN, not that it is digits-only |
| `catalog_routes.add_book`         | Complete | – |

### R2: Display new books
| Function Name            | Implementation Status | What is Missing |
|--------------------------|-----------------------|-----------------|
| `catalog_routes.catalog` | Complete              | Links to template, where table and borrow button are implemented |

### R3: Book Borrowing Interface
| Function Name                   | Implementation Status | What is Missing |
|--------------------------------|-----------------------|-----------------|
| `borrowing_route.borrow_book`  | Partial               | No try/except for patron ID, so no proper error message |
| `library_service.borrow_book_by_patron` | Partial | Logic allows 6 books instead of max 5 |

### R4: Book Return Processing
| Function Name                  | Implementation Status | What is Missing |
|--------------------------------|-----------------------|-----------------|
| `borrowing_route.return_book`  | Partial               | No try/except for patron ID |
| `library_service.return_book_by_patron` | Incomplete | Function not implemented |

### R5: Late Fee Calculation API
| Function Name                          | Implementation Status | What is Missing |
|---------------------------------------|-----------------------|-----------------|
| `library_service.calculate_late_fee_for_book` | Incomplete | Function not implemented |

### R6: Book Search Functionality
| Function Name                       | Implementation Status | What is Missing |
|------------------------------------|-----------------------|-----------------|
| `library_service.search_books_in_catalog` | Incomplete | Function not implemented |
| `search_routes.search_books`       | Partial | No validation on search type; any string allowed |

### R7: Patron Status Report
| Function Name                       | Implementation Status | What is Missing |
|------------------------------------|-----------------------|-----------------|
| `library_service.get_patron_status_report` | Incomplete | Function not implemented |

---

## 2. Unit Test Summary



- **`tests/test_r1_add_book.py`** — 5 tests (valid add, empty title, long author, bad ISBN, invalid copies)  
- **`tests/test_r3_borrow.py`** — 4 tests (invalid patron, nonexistent book `xfail`, borrow limit boundary `xfail`, valid borrow )  

