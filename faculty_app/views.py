"""
Views for the university ERP system (`my_faculty`).
Handles dashboard analytics, book loans, member registrations, 
canteen meal orders, exam registrations, financial categories, and GPAs.
Coded and commented entirely in English.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db import models
from datetime import timedelta
from decimal import Decimal

from .models import Member, Book, Loan, Transaction, CanteenMeal, ExamRegistration
from .validators import validate_email_address, validate_book_title, FacultyBusinessValidator
from .constants import SYSTEM_CONFIG
from .translations import TRANSLATIONS


def dashboard_view(request):
    """
    Handles the main ERP dashboard:
    - Displays top active members, latest books, and active loans.
    - Manages POST actions for member registration and book additions.
    """
    lang = request.session.get('lang', request.session.get('django_language', 'en'))
    t = TRANSLATIONS.get(lang, TRANSLATIONS['en'])

    if request.method == 'POST':
        action = request.POST.get('action')

        # 1. Register a new member with role selection
        if action == 'add_member':
            full_name = request.POST.get('full_name', '').strip()
            jmbg = request.POST.get('jmbg', '').strip()
            card_number = request.POST.get('card_number', '').strip()
            raw_email = request.POST.get('email', '').strip()
            role = request.POST.get('role', 'STUDENT')

            try:
                email = validate_email_address(raw_email, max_length=SYSTEM_CONFIG['MAX_EMAIL_LENGTH'])
                
                if not full_name or not jmbg or not card_number:
                    raise ValueError("All fields are required for member registration.")

                is_external = True if role in ['CITIZEN', 'EXTERNAL_PROFESSOR'] else False

                Member.objects.create(
                    full_name=full_name,
                    jmbg=jmbg,
                    card_number=card_number,
                    email=email,
                    role=role,
                    is_external=is_external
                )
                messages.success(request, "Member successfully registered!")
            except Exception as e:
                messages.error(request, f"Registration error: {e}")

            return redirect('dashboard')

        # 2. Add a new book
        elif action == 'add_book':
            raw_title = request.POST.get('title', '').strip()
            author = request.POST.get('author', '').strip()

            try:
                title = validate_book_title(raw_title)
                if not author:
                    raise ValueError("Author field cannot be empty.")

                Book.objects.create(title=title, author=author)
                messages.success(request, "Book successfully added to the library!")
            except Exception as e:
                messages.error(request, f"Book addition error: {e}")

            return redirect('dashboard')

        # 3. Issue a book loan
        elif action == 'issue_loan':
            member_id = request.POST.get('member_id')
            book_id = request.POST.get('book_id')

            member = get_object_or_404(Member, id=member_id)
            book = get_object_or_404(Book, id=book_id)

            is_valid, validation_message = FacultyBusinessValidator.validate_library_loan(member)
            if not is_valid:
                messages.error(request, f"Loan denied: {validation_message}")
                return redirect('dashboard')

            if not book.is_available:
                messages.error(request, "Loan denied: The selected book is currently not available.")
                return redirect('dashboard')

            due_date = timezone.now() + timedelta(days=14)
            Loan.objects.create(member=member, book=book, due_date=due_date)
            book.is_available = False
            book.save()

            messages.success(request, f"Book '{book.title}' successfully issued to {member.full_name}!")
            return redirect('dashboard')

        # 4. Return a book loan
        elif action == 'return_loan':
            loan_id = request.POST.get('loan_id')
            loan = get_object_or_404(Loan, id=loan_id, is_returned=False)

            loan.is_returned = True
            loan.save()

            book = loan.book
            book.is_available = True
            book.save()

            messages.success(request, f"Book '{book.title}' successfully returned.")
            return redirect('dashboard')

    top_members = Member.objects.annotate(loan_count=models.Count('loan')).order_by('-loan_count')[:5]
    latest_books = Book.objects.order_by('-created_at')[:5]
    active_loans = Loan.objects.filter(is_returned=False).select_related('member', 'book')

    context = {
        't': t,
        'top_members': top_members,
        'latest_books': latest_books,
        'active_loans': active_loans,
    }

    return render(request, 'erp/dashboard.html', context)


def set_language_view(request, lang_code):
    """
    Switches active language in session.
    """
    if lang_code in ['en', 'hr', 'de']:
        request.session['lang'] = lang_code
        request.session['django_language'] = lang_code
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


def canteen_view(request):
    """
    Handles canteen meal orders. Students and professors pay 1.57 EUR, others 4.50 EUR.
    Automatically generates financial transaction with category 'CANTEEN'.
    """
    lang = request.session.get('lang', request.session.get('django_language', 'en'))
    t = TRANSLATIONS.get(lang, TRANSLATIONS['en'])
    
    if request.method == 'POST':
        member_id = request.POST.get('member_id')
        meal_type = request.POST.get('meal_type')
        
        try:
            member = get_object_or_404(Member, id=member_id)
            
            # Students and Professors get subsidized price (1.57), others commercial (4.50)
            price = Decimal('1.57') if member.role in ['STUDENT', 'PROFESSOR'] else Decimal('4.50')
            
            CanteenMeal.objects.create(
                member=member,
                meal_type=meal_type,
                price=price
            )
            
            Transaction.objects.create(
                member=member,
                amount=price,
                transaction_type='INCOME',
                category='CANTEEN',
                payment_method='Canteen Card',
                is_verified=True,
                description=f"Canteen meal ({meal_type}) for {member.full_name}"
            )
            
            messages.success(request, f"Meal ordered for {member.full_name} (Price: {price} €).")
        except Exception as e:
            messages.error(request, f"Canteen error: {e}")
            
        return redirect('canteen')
        
    canteen_orders = CanteenMeal.objects.select_related('member').order_by('-date')[:10]
    return render(request, 'erp/canteen.html', {'t': t, 'canteen_orders': canteen_orders})


def exams_view(request):
    """
    Moodle & Exam Portal:
    - Allows exam registration.
    - Calculates GPA for students with > 5 passed exams.
    - Identifies top 3 best students and 1 worst student.
    """
    lang = request.session.get('lang', request.session.get('django_language', 'en'))
    t = TRANSLATIONS.get(lang, TRANSLATIONS['en'])

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'register_exam':
            member_id = request.POST.get('member_id')
            exam_name = request.POST.get('exam_name', '').strip()
            book_id = request.POST.get('recommended_book_id')

            try:
                member = get_object_or_404(Member, id=member_id)
                if not exam_name:
                    raise ValueError("Exam name cannot be empty.")

                is_valid, validation_message = FacultyBusinessValidator.validate_exam_registration(member)
                if not is_valid:
                    messages.error(request, f"Exam registration denied: {validation_message}")
                else:
                    rec_book = Book.objects.filter(id=book_id).first() if book_id else None
                    ExamRegistration.objects.create(
                        member=member,
                        exam_name=exam_name,
                        recommended_book=rec_book
                    )
                    messages.success(request, f"Exam '{exam_name}' registered successfully for {member.full_name}!")
            except Exception as e:
                messages.error(request, f"Exam error: {e}")

            return redirect('exams')

    exams = ExamRegistration.objects.select_related('member', 'recommended_book').order_by('-registration_date')
    all_books = Book.objects.all()


# GPA Calculation and Ranking (> 5 passed exams)
    student_gpa_list = []
    members = Member.objects.filter(role='STUDENT')
    for m in members:
        passed_exams = ExamRegistration.objects.filter(member=m, is_passed=True)
        if passed_exams.count() > 5:
            raw_avg = sum(e.grade for e in passed_exams) / passed_exams.count()
            # Ograniči prosjek na maksimalno 10.0 u slučaju neispravno unesenih ocjena
            avg_grade = min(raw_avg, 10.0)
            student_gpa_list.append({
                'member': m,
                'passed_count': passed_exams.count(),
                'gpa': round(avg_grade, 2)
            })




    # Sort students by GPA descending to find top 3 and bottom 1
    student_gpa_list.sort(key=lambda x: x['gpa'], reverse=True)
    top_3_students = student_gpa_list[:3]
    worst_student = student_gpa_list[-1] if student_gpa_list else None

    context = {
        't': t,
        'exams': exams,
        'all_books': all_books,
        'top_3_students': top_3_students,
        'worst_student': worst_student,
        'has_enough_gpa_data': len(student_gpa_list) > 0,
    }
    return render(request, 'erp/exams.html', context)


import csv
from django.http import HttpResponse
from django.core.paginator import Paginator

def financial_view(request):
    """
    Financial Ledger supporting detailed categories, 4 payment methods, 
    robust filtering, pagination, CSV export, and totals calculation.
    """
    lang = request.session.get('lang', request.session.get('django_language', 'en'))
    t = TRANSLATIONS.get(lang, TRANSLATIONS['en'])
    
    transactions = Transaction.objects.select_related('member').order_by('-date')

    # Filtering parameters from GET request
    filter_type = request.GET.get('type')
    filter_category = request.GET.get('category')
    filter_method = request.GET.get('method')
    items_per_page = request.GET.get('per_page', '10')
    export_format = request.GET.get('export')

    if filter_type:
        transactions = transactions.filter(transaction_type=filter_type)
    if filter_category:
        transactions = transactions.filter(category=filter_category)
    if filter_method:
        transactions = transactions.filter(payment_method=filter_method)

    # Ako je zatražen CSV izvoz, generiramo datoteku na temelju filtriranih podataka
    if export_format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="financial_transactions.csv"'
        
        writer = csv.writer(response)
        # Zaglavlje CSV-a
        writer.writerow(['ID', 'Date', 'Type', 'Category', 'Amount (EUR)', 'Payment Method', 'Member', 'Verified', 'Description'])
        
        for tr in transactions:
            member_name = tr.member.full_name if tr.member else 'N/A'
            writer.writerow([
                tr.id,
                tr.date.strftime('%Y-%m-%d %H:%M'),
                tr.transaction_type,
                tr.category,
                tr.amount,
                tr.payment_method,
                member_name,
                tr.is_verified,
                tr.description or ''
            ])
        return response

    # Calculate totals based on filtered verified transactions
    total_income = sum(tr.amount for tr in transactions if tr.transaction_type == 'INCOME' and tr.is_verified)
    total_expense = sum(tr.amount for tr in transactions if tr.transaction_type == 'EXPENSE' and tr.is_verified)
    net_balance = total_income - total_expense

    # Paginacija (strančenje)
    try:
        per_page_int = int(items_per_page)
    except ValueError:
        per_page_int = 10

    paginator = Paginator(transactions, per_page_int)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        't': t,
        'transactions': page_obj,
        'total_income': total_income,
        'total_expense': total_expense,
        'net_balance': net_balance,
        'selected_type': filter_type,
        'selected_category': filter_category,
        'selected_method': filter_method,
        'selected_per_page': str(per_page_int),
        'income_categories': Transaction.INCOME_CATEGORIES,
        'expense_categories': Transaction.EXPENSE_CATEGORIES,
    }

    return render(request, 'erp/financial.html', context)