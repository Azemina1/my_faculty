"""
Pytest test suite for validating ERP inputs (Book titles, Emails, etc.).
"""

import pytest
from faculty_app.validators import validate_book_title, validate_email_address

def test_valid_book_title_with_unicode_and_numbers():
    """Test that valid titles with unicode and inner numbers pass successfully."""
    assert validate_book_title("Python 3 Uvod") == "Python 3 Uvod"
    assert validate_book_title("Financijsko poslovanje (2026)") == "Financijsko poslovanje (2026)"

def test_invalid_book_title_starts_with_digit():
    """Test that titles starting with a digit raise a ValueError."""
    with pytest.raises(ValueError, match="Book title cannot start with a number."):
        validate_book_title("3. Svijet")

def test_invalid_book_title_too_long():
    """Test that titles exceeding 50 characters are rejected."""
    long_title = "A" * 51
    with pytest.raises(ValueError, match="Book title exceeds maximum length"):
        validate_book_title(long_title)

def test_valid_email_address():
    """Test that correct email format passes."""
    assert validate_email_address("student@faculty.com") == "student@faculty.com"

def test_invalid_email_missing_at():
    """Test that emails without '@' symbol are rejected."""
    with pytest.raises(ValueError, match="It must contain the '@' symbol."):
        validate_email_address("studentfaculty.com")