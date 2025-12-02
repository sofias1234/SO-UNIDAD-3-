
# core/models.py
from django.db import models
from django.utils import timezone
from datetime import timedelta
import hashlib

class Student(models.Model):
    name = models.CharField(max_length=120)
    student_id = models.CharField(max_length=20, unique=True)
    wallet_address = models.CharField(max_length=64, blank=True, null=True)  # dirección Algorand opcional

    def __str__(self):
        return f"{self.name} ({self.student_id})"

class Book(models.Model):
    title = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return f"{self.title}"

class Loan(models.Model):
    STATUS_CHOICES = [
        ("activo", "Activo"),
        ("vencido", "Vencido"),
        ("cerrado", "Cerrado"),
    ]
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    start_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="activo")
    onchain_txid = models.CharField(max_length=128, blank=True, null=True)  # txid de registro en Algorand

    def is_overdue(self):
        return timezone.localdate() > self.due_date and self.status != "cerrado"

    def days_overdue(self):
        if not self.is_overdue():
            return 0
        delta = timezone.localdate() - self.due_date
        return delta.days

    def content_hash(self):
        payload = f"{self.book.code}|{self.student.student_id}|{self.start_date}|{self.due_date}"
        return hashlib.sha256(payload.encode()).hexdigest()

class Fine(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name="fines")
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    paid = models.BooleanField(default=False)
    onchain_txid = models.CharField(max_length=128, blank=True, null=True)

    def __str__(self):
        return f"Multa {self.amount} por {self.loan}"
