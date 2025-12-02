# core/urls.py
from django.urls import path
from . import views  # Importas el módulo views

urlpatterns = [
    # Página principal
    path("", views.inicio, name="inicio"),

    # Préstamos
    path("prestamos/activos/", views.loans_active, name="loans_active"),
    path("prestamos/historial/", views.loans_history, name="loans_history"),
    path("prestamos/registrar/<int:loan_id>/", views.register_loan, name="register_loan"),

    # Contratos
    path("contrato/", views.contract_view, name="contract"),

    # Multas
    path("multas/pagar/<int:fine_id>/", views.pay_fine, name="pay_fine"),
]

