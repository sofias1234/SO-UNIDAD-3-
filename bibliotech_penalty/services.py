# core/services.py
from decimal import Decimal
from django.utils import timezone
from .models import Loan, Fine

DAILY_FINE = Decimal("15.00")  # $15 por día vencido

def update_loan_status_and_fines():
    """Actualiza estatus y crea multas para préstamos vencidos."""
    today = timezone.localdate()
    for loan in Loan.objects.filter(status__in=["activo", "vencido"]):
        if today > loan.due_date and loan.status != "cerrado":
            # marcar como vencido
            if loan.status != "vencido":
                loan.status = "vencido"
                loan.save()
            # calcular multa pendiente (por días vencidos no multados aún)
            existing_days = sum(max(0, f.loan.days_overdue()) for f in loan.fines.all())
            # Multa lineal por día vencido actual (simple): crear/actualizar la multa del día
            days = loan.days_overdue()
            if days > 0:
                # crear una multa acumulativa por el total vencido actual
                # evitar duplicados: si existe una multa no pagada, actualizar su monto
                fine = loan.fines.filter(paid=False).first()
                total = DAILY_FINE * days
                if fine:
                    fine.amount = total
                    fine.save()
                else:
                    Fine.objects.create(loan=loan, amount=total)
        elif today <= loan.due_date and loan.status != "cerrado":
            loan.status = "activo"
            loan.save()

def summarize_student_loans(student):
    loans = Loan.objects.filter(student=student)
    activos = loans.filter(status="activo").count()
    vencidos = sum(1 for l in loans if l.is_overdue())
    multas_pendientes = sum(float(f.amount) for f in Fine.objects.filter(loan__student=student, paid=False))
    return {
        "total_activos": activos,
        "prestamos_vencidos": vencidos,
        "multas_pendientes": multas_pendientes,
    }

