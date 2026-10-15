"""
Database models for the university ERP system (`my_faculty`).
Fully 3NF compliant, covering Library, Canteen, Exams, Subjects, and Transactions.
Coded and commented entirely in English.
"""

from django.db import models
from django.utils import timezone
from datetime import timedelta


class Member(models.Model):
    """
    Represents faculty members with specific roles: 
    Student, Citizen, Professor, External Professor.
    Includes financial flags for annual tuition and fee exemptions.
    """
    ROLE_CHOICES = [
        ('STUDENT', 'Student'),
        ('CITIZEN', 'Citizen / Visitor'),
        ('PROFESSOR', 'Professor'),
        ('EXTERNAL_PROFESSOR', 'External Professor'),
    ]

    full_name = models.CharField(max_length=50)
    jmbg = models.CharField(max_length=13, unique=True)
    card_number = models.CharField(max_length=11, unique=True)
    email = models.EmailField(max_length=40, unique=True)
    role = models.CharField(max_length=25, choices=ROLE_CHOICES, default='STUDENT')
    is_external = models.BooleanField(default=False)  # Kept for backward compatibility
    
    # Financial flags for academic fees
    is_tuition_paid = models.BooleanField(default=False, verbose_name="Annual Tuition Paid (Free Exams)")
    is_fee_exempt = models.BooleanField(default=False, verbose_name="Fee Exempt / Scholarship")
    
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.full_name} ({self.get_role_display()}) - Card: {self.card_number}"


class Book(models.Model):
    """
    Represents books available in the faculty library, including stock quantity.
    """
    title = models.CharField(max_length=50)
    author = models.CharField(max_length=50)
    quantity = models.PositiveIntegerField(default=1, verbose_name="Stock Quantity")
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        # Automatski postavi je li knjiga dostupna ovisno o količini na zalihi
        if self.quantity > 0:
            self.is_available = True
        else:
            self.is_available = False
        super().save(*args, **kwargs)

    def __str__(self):
        return f'"{self.title}" by {self.author} (Stock: {self.quantity})'

class Subject(models.Model):
    """
    Represents academic subjects/courses managed by admin,
    linked to professors, external professors, and course/exam fees.
    """
    name = models.CharField(max_length=200, verbose_name="Subject Name")
    code = models.CharField(max_length=50, unique=True, verbose_name="Subject Code")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    
    professor = models.ForeignKey(
        Member, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='taught_subjects',
        limit_choices_to={'role': 'PROFESSOR'},
        verbose_name="Main Professor"
    )
    
    external_professor = models.ForeignKey(
        Member, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='external_taught_subjects',
        limit_choices_to={'role': 'EXTERNAL_PROFESSOR'},
        verbose_name="External Professor"
    )
    
    fee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Course/Exam Fee (EUR)")

    def __str__(self):
        return f"{self.code} - {self.name} ({self.fee_amount} €)"



class Loan(models.Model):
    """
    Tracks book loans with renewal rules (7 days initial + 5 days extension + 3 days extension),
    automatic due dates, and late fine calculation (0.25 EUR per overdue day).
    """
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    issue_date = models.DateTimeField(default=timezone.now, verbose_name="Issue Date")
    due_date = models.DateTimeField(null=True, blank=True, verbose_name="Due Date")
    renewal_count = models.PositiveIntegerField(default=0, verbose_name="Renewal Count (Max 2)")
    is_returned = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # Ako se tek kreira posudba, početni rok je 7 dana
        if not self.pk and not self.due_date:
            self.due_date = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)

    @property
    def calculate_fine(self):
        """
        Izračunava zamudninu (0.25 € po danu) ako je istekao rok, a knjiga nije vraćena.
        """
        if not self.is_returned and self.due_date and timezone.now() > self.due_date:
            overdue_days = (timezone.now() - self.due_date).days
            return round(overdue_days * 0.25, 2)
        return 0.00

    def extend_loan(self):
        """
        Pravilo produženja: 1. produženje +5 dana, 2. produženje +3 dana. Max 2 produženja.
        """
        if self.is_returned:
            return False, "Cannot extend a returned book."
        
        if self.renewal_count == 0:
            self.due_date += timedelta(days=5)
            self.renewal_count += 1
            self.save()
            return True, "Loan extended by 5 days."
        elif self.renewal_count == 1:
            self.due_date += timedelta(days=3)
            self.renewal_count += 1
            self.save()
            return True, "Loan extended by 3 days (Final extension)."
        else:
            return False, "Maximum extensions reached (7d + 5d + 3d limit). Please return the book."


    def __str__(self):
        date_formatted = self.issue_date.strftime('%d.%m.%Y.') if self.issue_date else 'N/A'
        return f"Posudba: {self.book.title} (Korisnik: {self.member.full_name}, Datum: {date_formatted})"

    


class CanteenMeal(models.Model):
    """
    Represents canteen meal orders placed by members.
    Automatically distinguishes subsidized price for students/professors vs commercial price for guests.
    """
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    meal_type = models.CharField(max_length=30, default='LUNCH')
    price = models.DecimalField(max_digits=8, decimal_places=2, default=1.57)
    date = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        # Automatically set price based on member role
        # Citizens / Visitors pay full commercial price (e.g., 4.50 EUR)
        if self.member.role == 'CITIZEN' or self.member.is_external:
            self.price = 4.50
        else:
            self.price = 1.57  # Subsidized price for students and professors
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.meal_type} - {self.member.full_name} ({self.price} EUR)"


class ExamRegistration(models.Model):
    """
    Moodle-like exam portal tracking registrations, grades (0.0 - 10.0), 
    passing status, linked subjects, payment verification, and recommended library books.
    """
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Subject")
    exam_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Exam Name")
    grade = models.FloatField(default=0.0)  # 0.0 to 10.0 scale
    is_passed = models.BooleanField(default=False)
    is_fee_paid = models.BooleanField(default=False, verbose_name="Exam/Course Fee Paid")
    exam_date = models.DateTimeField(null=True, blank=True)
    recommended_book = models.ForeignKey(Book, on_delete=models.SET_NULL, null=True, blank=True)
    registration_date = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        # Automatski postavi naziv ispita prema nazivu predmeta ako nije ručno upisan
        if self.subject and not self.exam_name:
            self.exam_name = self.subject.name
            
        # Automatski odredi je li ispit položen na temelju ocjene (6.0 - 10.0)
        if self.grade >= 6.0:
            self.is_passed = True
        else:
            self.is_passed = False
        super().save(*args, **kwargs)

    def __str__(self):
        status = f"Passed ({self.grade})" if self.is_passed else "Pending/Failed"
        return f"Exam: {self.exam_name} for {self.member.full_name} [{status}]"


class Transaction(models.Model):
    """
    Central financial ledger supporting detailed categories, 
    4 payment methods, and historical dates up to 1 year back.
    """
    TRANSACTION_TYPES = [
        ('INCOME', 'Income'),
        ('EXPENSE', 'Expense'),
    ]

    INCOME_CATEGORIES = [
        ('STATE_BUDGET', 'State Budget'),
        ('TUITION', 'Annual Tuition Fee (1000 €)'),
        ('MONTHLY_MEMBERSHIP', 'Library Monthly Membership (8 €)'),
        ('ANNUAL_MEMBERSHIP', 'Library Annual Membership (16 €)'),
        ('FINES', 'Late Fines (0.25 € / day)'),
        ('EXAM_FEE', 'Exam Fee (100 €)'),
        ('CANTEEN', 'Canteen Meal Sales'),
        ('BOOK_SALES', 'Book Sales'),
        ('DONATION', 'Donations'),
        ('OTHER_INC', 'Other Income'),
    ]

    EXPENSE_CATEGORIES = [
        ('SALARIES', 'Salaries (Plaće)'),
        ('MATERIAL', 'Material'),
        ('TRANSPORT', 'Transport'),
        ('OTHER_EXP', 'Other Expense'),
    ]

    # Kombinirana lista za polje u bazi
    CATEGORY_CHOICES = INCOME_CATEGORIES + EXPENSE_CATEGORIES

    PAYMENT_METHODS = [
        ('Cash', 'Cash'),
        ('IBAN', 'IBAN / Bank Transfer'),
        ('PayPal', 'PayPal'),
        ('Canteen Card', 'Canteen Card'),
    ]

    member = models.ForeignKey(Member, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Linked Member (Student / Professor)")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Amount (EUR)")
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES, verbose_name="Type")
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='OTHER_INC', verbose_name="Category")
    payment_method = models.CharField(max_length=30, choices=PAYMENT_METHODS, default='Cash', verbose_name="Payment Method")
    is_verified = models.BooleanField(default=True, verbose_name="Verified")
    description = models.CharField(max_length=255, blank=True, null=True, verbose_name="Description")
    date = models.DateTimeField(default=timezone.now, verbose_name="Date (Supports past 1 year)")

    def __str__(self):
        return f"{self.get_transaction_type_display()} [{self.category}]: {self.amount} EUR ({self.payment_method})"