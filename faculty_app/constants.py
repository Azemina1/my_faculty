"""
System-wide immutable configurations and business logic constants 
using MappingProxyType to ensure data consistency and prevent accidental modifications.
All coded and commented in English.
"""

from types import MappingProxyType

SYSTEM_CONFIG = MappingProxyType({
    # String length limits
    "MAX_BOOK_TITLE_LENGTH": 50,
    "MAX_EMAIL_LENGTH": 40,
    "DEFAULT_START_ID": 100,
    
    # Library Membership Fees (EUR)
    "EMPLOYEE_MEMBERSHIP_FEE": 0.00,
    "STUDENT_MEMBERSHIP_FEE": 16.40,
    "EXTERNAL_USER_FEE": 21.00,
    
    # Restaurant / Canteen Prices (EUR)
    "CANTEEN_PRICE_STUDENT": 1.57,  # Subsidized meal price
    "CANTEEN_PRICE_EXTERNAL": 4.50, # Full commercial meal price
    
    # Exam Registration Fees for External Participants (EUR)
    "EXAM_FEE_EXTERNAL": 50.00,
})

# Backward-compatible individual variable references mapped from the secure configuration
LIBRARY_FEE_EMPLOYEE = SYSTEM_CONFIG["EMPLOYEE_MEMBERSHIP_FEE"]
LIBRARY_FEE_STUDENT = SYSTEM_CONFIG["STUDENT_MEMBERSHIP_FEE"]
LIBRARY_FEE_EXTERNAL = SYSTEM_CONFIG["EXTERNAL_USER_FEE"]

CANTEEN_PRICE_STUDENT = SYSTEM_CONFIG["CANTEEN_PRICE_STUDENT"]
CANTEEN_PRICE_EXTERNAL = SYSTEM_CONFIG["CANTEEN_PRICE_EXTERNAL"]

EXAM_FEE_EXTERNAL = SYSTEM_CONFIG["EXAM_FEE_EXTERNAL"]