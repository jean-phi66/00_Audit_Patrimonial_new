import pandas as pd
from datetime import date
import uuid
import streamlit as st

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

# --- Fonctions de gestion des données du patrimoine ---

def get_patrimoine_df(actifs, passifs):
    """
    Crée un DataFrame consolidé du patrimoine avec les valeurs brutes et nettes.
    """
    if not actifs:
        return pd.DataFrame()

    # Crée un dictionnaire qui mappe l'ID de chaque actif à sa dette totale (CRD)
    dette_par_actif = {}
    for p in passifs:
        asset_id = p.get('actif_associe_id')
        if asset_id:
            crd = p.get('crd_calcule', 0)
            dette_par_actif[asset_id] = dette_par_actif.get(asset_id, 0) + crd

    # Construit le DataFrame
    data = []
    for a in actifs:
        asset_id = a.get('id')
        valeur_brute = a.get('valeur', 0.0)
        dette_associee = dette_par_actif.get(asset_id, 0.0)
        valeur_nette = valeur_brute - dette_associee
        data.append({
            'Libellé': a.get('libelle') or 'Actif sans nom',
            'Type': a.get('type', 'Indéfini'),
            'Valeur Brute': valeur_brute,
            'Valeur Nette': valeur_nette
        })

    return pd.DataFrame(data)

def add_item(category):
    """Ajoute un élément à la liste des actifs ou passifs."""
    if category == 'actifs':
        st.session_state.actifs.append({
            'id': str(uuid.uuid4()),
            'libelle': '', 
            'type': 'Immobilier de jouissance', 
            'valeur': 0.0
        })
    elif category == 'passifs':
        st.session_state.passifs.append({
            'libelle': '', 
            'montant_initial': 100000.0,
            'taux_annuel': 1.5,
            'duree_annees': 20,
            'date_debut': date.today(),
            'actif_associe_id': None
        })

def remove_item(category, index):
    """Supprime un élément d'une liste à un index donné."""
    if category == 'actifs':
        asset_to_remove_id = st.session_state.actifs[index].get('id')
        st.session_state.actifs.pop(index)
        if asset_to_remove_id:
            for passif in st.session_state.passifs:
                if passif.get('actif_associe_id') == asset_to_remove_id:
                    passif['actif_associe_id'] = None
    elif category == 'passifs':
        st.session_state.passifs.pop(index)
    st.rerun()