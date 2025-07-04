import pandas as pd
from datetime import date
import uuid

# --- Fonctions de calcul de prêt ---

def calculate_monthly_payment(principal, annual_rate_pct, duration_years):
    """Calcule la mensualité d'un prêt."""
    if duration_years == 0 or annual_rate_pct is None or principal == 0:
        return 0.0
    
    monthly_rate = (annual_rate_pct / 100) / 12
    total_months = duration_years * 12

    if monthly_rate == 0:
        return principal / total_months if total_months > 0 else 0

    payment = principal * (monthly_rate * (1 + monthly_rate)**total_months) / ((1 + monthly_rate)**total_months - 1)
    return payment

def calculate_crd(principal, annual_rate_pct, duration_years, start_date):
    """Calcule le Capital Restant Dû (CRD) à la date d'aujourd'hui."""
    if not all([principal > 0, annual_rate_pct is not None, duration_years > 0, start_date]):
        return principal

    today = date.today()
    if start_date > today:
        return principal

    months_passed = (today.year - start_date.year) * 12 + (today.month - start_date.month)
    total_months = duration_years * 12
    
    if months_passed >= total_months:
        return 0.0

    monthly_payment = calculate_monthly_payment(principal, annual_rate_pct, duration_years)
    monthly_rate = (annual_rate_pct / 100) / 12
    remaining_months = total_months - months_passed
    
    if monthly_rate == 0:
        return principal - (months_passed * monthly_payment)

    crd = monthly_payment * (1 - (1 + monthly_rate)**-remaining_months) / monthly_rate
    return max(0, crd)

