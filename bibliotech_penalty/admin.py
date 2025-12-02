# core/admin.py
from django.contrib import admin
from .models import Student, Book, Loan, Fine

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("name", "student_id", "wallet_address")
    search_fields = ("name", "student_id")

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "code")
    search_fields = ("title", "code")

@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ("book", "student", "start_date", "due_date", "status", "onchain_txid")
    list_filter = ("status",)
    search_fields = ("book__title", "student__name", "student__student_id")

@admin.register(Fine)
class FineAdmin(admin.ModelAdmin):
    list_display = ("loan", "amount", "paid", "onchain_txid", "created_at")
    list_filter = ("paid",)

