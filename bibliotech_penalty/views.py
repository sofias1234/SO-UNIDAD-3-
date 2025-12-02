# core/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from .models import Student, Loan, Fine
from .services import update_loan_status_and_fines, summarize_student_loans
from .algorand import register_loan_onchain, pay_fine_onchain

def inicio(request):
    return render(request, "index.html")

def _get_demo_student():
    # Carga o crea un estudiante demo "Juan Pérez"
    student, _ = Student.objects.get_or_create(
        student_id="EST001",
        defaults={"name": "Juan Pérez", "wallet_address": ""}
    )
    return student

def loans_active(request):
    student = _get_demo_student()
    update_loan_status_and_fines()
    loans = Loan.objects.filter(student=student).order_by("-start_date")
    summary = summarize_student_loans(student)

    return render(request, "loans_active.html", {
        "student": student,
        "loans": loans,
        "summary": summary,
        "today": timezone.localdate(),
    })

def loans_history(request):
    student = _get_demo_student()
    loans = Loan.objects.filter(student=student).order_by("-start_date")
    fines = Fine.objects.filter(loan__student=student).order_by("-created_at")
    return render(request, "loans_history.html", {
        "student": student,
        "loans": loans,
        "fines": fines,
    })

def contract_view(request):
    student = _get_demo_student()
    fines = Fine.objects.filter(loan__student=student, paid=False)
    loans = Loan.objects.filter(student=student)
    return render(request, "contract.html", {
        "student": student,
        "fines": fines,
        "loans": loans,
    })

def register_loan(request, loan_id: int):
    loan = get_object_or_404(Loan, id=loan_id)
    try:
        txid = register_loan_onchain(loan)
        loan.onchain_txid = txid
        loan.save()
        messages.success(request, f"Préstamo registrado en Algorand (txid: {txid})")
    except Exception as e:
        messages.error(request, f"Error al registrar en Algorand: {e}")
    return redirect("loans_active")

def pay_fine(request, fine_id: int):
    fine = get_object_or_404(Fine, id=fine_id)
    student = fine.loan.student
    try:
        txid = pay_fine_onchain(student.wallet_address or "", float(fine.amount))
        fine.paid = True
        fine.onchain_txid = txid
        fine.save()
        messages.success(request, f"Multa pagada y registrada (txid: {txid})")
    except Exception as e:
        messages.error(request, f"Error al registrar pago: {e}")
    return redirect("contract")

