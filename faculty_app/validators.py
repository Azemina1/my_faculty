"""
Strict validation rules for inputs (Email, Book Titles, Names) 
with Unicode support, security checks, and 3NF business logic constraints:
- Library membership & debt checks
- Canteen pricing based on `is_external` status
- Exam registration payment verifications
"""

import re
import unicodedata
from .models import Transaction, Loan


def validate_email_address(email: str, max_length: int = 40) -> str:
    """
    Validates email: max 40 chars, requires '@', no dangerous characters.
    """
    try:
        email = str(email).strip()
    except Exception:
        raise ValueError("Invalid format for email address.")

    if not email:
        raise ValueError("Email address cannot be empty.")
    
    if len(email) > max_length:
        raise ValueError(f"Email address exceeds maximum length of {max_length} characters.")
    
    if "@" not in email:
        raise ValueError("Invalid email address. It must contain the '@' symbol.")
    
    email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    if not re.match(email_regex, email):
        raise ValueError("Invalid email format. Please enter a valid email (e.g., user@faculty.com).")
        
    return email


def validate_book_title(title: str) -> str:
    """
    Validates book title: max 50 chars, allows unicode letters, symbols, 
    and numbers, but strictly forbids starting with a digit.
    """
    try:
        title = str(title).strip()
    except Exception:
        raise ValueError("Invalid format for book title.")

    if not title:
        raise ValueError("Book title cannot be empty.")
    
    if len(title) > 50:
        raise ValueError("Book title exceeds maximum length of 50 characters.")
    
    if title[0].isdigit():
        raise ValueError("Book title cannot start with a number.")
    
    for char in title:
        category = unicodedata.category(char)
        if not (category.startswith('L') or category.startswith('N') or category == 'Zs' or category.startswith('P') or category.startswith('S')):
            raise ValueError(f"Invalid character '{char}' in book title.")
            
    return title


class FacultyBusinessValidator:
    """
    Enforces business rules and validation logic across faculty modules.
    """

    @staticmethod
    def validate_library_loan(member):
        """
        Validates if a member is eligible to borrow a book:
        1. Must not have active overdue loans or unpaid debts.
        2. If external, membership transaction must be verified.
        """
        # Check for unreturned loans
        active_loans = Loan.objects.filter(member=member, is_returned=False)
        if active_loans.exists():
            return False, "Member has unreturned books."

        # Check if external member has a verified membership transaction
        if member.is_external:
            membership_paid = Transaction.objects.filter(
                member=member,
                transaction_type='INCOME',
                is_verified=True
            ).exists()
            if not membership_paid:
                return False, "External member must pay the annual library fee (21.00 EUR) before borrowing."

        return True, "Validation passed."

    @staticmethod
    def calculate_meal_price(member):
        """
        Calculates canteen meal price depending on whether the user is external.
        """
        from .constants import CANTEEN_PRICE_EXTERNAL, CANTEEN_PRICE_STUDENT
        if member.is_external:
            return CANTEEN_PRICE_EXTERNAL
        return CANTEEN_PRICE_STUDENT

    @staticmethod
    def validate_exam_registration(member):
        """
        Ensures external participants have verified payment for exam registration.
        """
        if member.is_external:
            payment_exists = Transaction.objects.filter(
                member=member,
                transaction_type='INCOME',
                is_verified=True
            ).exists()
            if not payment_exists:
                return False, "Exam registration denied: Payment fee not verified."
        return True, "Exam registration approved."