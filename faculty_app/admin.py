"""
Django admin configuration for faculty_app models.
Coded and commented entirely in English.
"""

from django.contrib import admin
from .models import Member, Book, Subject, Loan, CanteenMeal, ExamRegistration, Transaction


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'role', 'card_number', 'is_tuition_paid', 'is_fee_exempt', 'created_at')
    search_fields = ('full_name', 'card_number', 'jmbg', 'email')
    list_filter = ('role', 'is_tuition_paid', 'is_fee_exempt', 'is_external')



@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'author', 'quantity', 'is_available', 'created_at')
    search_fields = ('title', 'author')
    list_filter = ('is_available',)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'name', 'professor', 'external_professor', 'fee_amount')
    search_fields = ('name', 'code')
    list_filter = ('professor', 'external_professor')


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('id', 'member', 'book', 'issue_date', 'due_date', 'is_returned')
    list_filter = ('is_returned',)
    search_fields = ('member__full_name', 'book__title')


@admin.register(CanteenMeal)
class CanteenMealAdmin(admin.ModelAdmin):
    list_display = ('id', 'member', 'meal_type', 'price', 'date')
    list_filter = ('meal_type',)
    search_fields = ('member__full_name',)


@admin.register(ExamRegistration)
class ExamRegistrationAdmin(admin.ModelAdmin):
    list_display = ('id', 'member', 'exam_name', 'subject', 'grade', 'is_passed', 'is_fee_paid', 'exam_date')
    list_filter = ('member', 'is_passed', 'is_fee_paid', 'subject')
    search_fields = ('member__full_name', 'exam_name')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'transaction_type', 'category', 'amount', 'payment_method', 'member', 'is_verified', 'date')
    list_filter = ('transaction_type', 'category', 'payment_method', 'is_verified', 'date')
    search_fields = ('description', 'member__full_name', 'member__card_number')
    autocomplete_fields = ['member']  # Omogućuje pretraživanje članova po imenu ili broju kartice!
