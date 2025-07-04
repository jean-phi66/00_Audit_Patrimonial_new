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

def calculate_crd(principal, annual_rate_pct, duration_years, start_date, on_date=None):
    """Calcule le Capital Restant Dû (CRD) à une date donnée."""
    if not all([principal > 0, annual_rate_pct is not None, duration_years > 0, start_date]):
        return principal

    if on_date is None:
        on_date = date.today()
        
    if start_date > on_date:
        return principal

    # On ne compte que les mois pleins écoulés
    months_passed = (on_date.year - start_date.year) * 12 + (on_date.month - start_date.month)
    total_months = duration_years * 12
    
    if months_passed >= total_months:
        return 0.0

    monthly_payment = calculate_monthly_payment(principal, annual_rate_pct, duration_years)
    monthly_rate = (annual_rate_pct / 100) / 12
    remaining_months = total_months - months_passed
    
    if monthly_rate == 0:
        return max(0, principal - (months_passed * monthly_payment))

    crd = monthly_payment * (1 - (1 + monthly_rate)**-remaining_months) / monthly_rate
    return max(0, crd)

def calculate_loan_annual_breakdown(loan, year=None):
    """
    Calcule la répartition annuelle du capital et des intérêts pour un prêt donné.

    Args:
        loan (dict): Dictionnaire contenant les informations du prêt.
                     Doit contenir 'montant_initial', 'taux_annuel', 'duree_annees', 'date_debut'.
        year (int, optional): L'année pour laquelle faire le calcul. 
                              Par défaut, l'année actuelle.

    Returns:
        dict: Un dictionnaire avec 'capital', 'interest', et 'total_paid' pour l'année.
    """
    if not loan:
        return {'capital': 0, 'interest': 0, 'total_paid': 0}

    if year is None:
        year = date.today().year

    # Extraire les détails du prêt
    principal = loan.get('montant_initial', 0)
    annual_rate_pct = loan.get('taux_annuel')
    duration_years = loan.get('duree_annees', 0)
    start_date = loan.get('date_debut')

    if not all([principal > 0, annual_rate_pct is not None, duration_years > 0, start_date]):
        return {'capital': 0, 'interest': 0, 'total_paid': 0}

    # --- 1. Calcul du capital remboursé (méthode la plus fiable) ---
    # On prend la fin de l'année N-1 et la fin de l'année N pour capturer tous les paiements de l'année N
    date_debut_annee = date(year - 1, 12, 31)
    date_fin_annee = date(year, 12, 31)

    crd_debut_annee = calculate_crd(principal, annual_rate_pct, duration_years, start_date, on_date=date_debut_annee)
    crd_fin_annee = calculate_crd(principal, annual_rate_pct, duration_years, start_date, on_date=date_fin_annee)
    capital_rembourse = crd_debut_annee - crd_fin_annee

    # --- 2. Calcul du total payé (nombre de mensualités) ---
    mensualite = calculate_monthly_payment(principal, annual_rate_pct, duration_years)
    total_duration_months = duration_years * 12
    
    def get_months_passed(current_date):
        if start_date > current_date: return 0
        return (current_date.year - start_date.year) * 12 + (current_date.month - start_date.month)

    months_passed_start = min(get_months_passed(date_debut_annee), total_duration_months)
    months_passed_end = min(get_months_passed(date_fin_annee), total_duration_months)

    nombre_paiements_annee = months_passed_end - months_passed_start
    total_paye_annee = nombre_paiements_annee * mensualite

    # --- 3. Calcul des intérêts par déduction ---
    interets_payes = total_paye_annee - capital_rembourse

    return {'capital': max(0, capital_rembourse), 'interest': max(0, interets_payes), 'total_paid': max(0, total_paye_annee)}

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

# --- Fonctions d'analyse immobilière ---

def find_associated_loan(asset_id, passifs):
    """Trouve le premier prêt associé à un ID d'actif."""
    if not asset_id:
        return None
    for p in passifs:
        if p.get('actif_associe_id') == asset_id:
            return p
    return None

def calculate_gross_yield(asset):
    """Calcule la rentabilité brute en %."""
    loyers_annuels = asset.get('loyers_mensuels', 0) * 12
    valeur_achat = asset.get('valeur', 0)
    if not valeur_achat: return 0.0
    return (loyers_annuels / valeur_achat) * 100

def calculate_net_yield_charges(asset):
    """Calcule la rentabilité nette de charges en %."""
    loyers_annuels = asset.get('loyers_mensuels', 0) * 12
    charges_annuelles = asset.get('charges', 0) * 12
    taxe_fonciere = asset.get('taxe_fonciere', 0)
    valeur_achat = asset.get('valeur', 0)
    if not valeur_achat: return 0.0
    
    revenu_net_charges = loyers_annuels - charges_annuelles - taxe_fonciere
    return (revenu_net_charges / valeur_achat) * 100

def calculate_property_tax(asset, loan, tmi_pct, social_tax_pct):
    """Calcule l'impôt total (IR + PS) sur les revenus fonciers au régime réel."""
    loyers_annuels = asset.get('loyers_mensuels', 0) * 12
    charges_annuelles = asset.get('charges', 0) * 12
    taxe_fonciere = asset.get('taxe_fonciere', 0)
    
    # Calcul des intérêts d'emprunt (simplifié)
    interets_emprunt = 0
    if loan:
        mensualite = calculate_monthly_payment(loan['montant_initial'], loan['taux_annuel'], loan['duree_annees'])
        current_year = date.today().year
        # On calcule pour l'année N-1 car les revenus fonciers se déclarent sur l'année passée
        previous_year = current_year - 1
        start_of_year = date(previous_year, 1, 1)
        end_of_year = date(previous_year, 12, 31)

        # On s'assure de ne pas calculer avant le début du prêt
        calc_date_start = max(start_of_year, loan['date_debut'])
        calc_date_end = max(end_of_year, loan['date_debut'])

        crd_debut_annee = calculate_crd(loan['montant_initial'], loan['taux_annuel'], loan['duree_annees'], loan['date_debut'], on_date=calc_date_start)
        crd_fin_annee = calculate_crd(loan['montant_initial'], loan['taux_annuel'], loan['duree_annees'], loan['date_debut'], on_date=calc_date_end)
        
        capital_rembourse_annee = crd_debut_annee - crd_fin_annee
        
        # On ne compte les mensualités que si le prêt a effectivement couru sur la période
        if loan['date_debut'] < end_of_year:
            # Calcul simple des paiements sur l'année
            interets_emprunt = max(0, (mensualite * 12) - capital_rembourse_annee)

    charges_deductibles = charges_annuelles + taxe_fonciere + interets_emprunt
    revenu_foncier_imposable = max(0, loyers_annuels - charges_deductibles)
    
    impot_sur_revenu = revenu_foncier_imposable * (tmi_pct / 100)
    prelevements_sociaux = revenu_foncier_imposable * (social_tax_pct / 100)
    
    return {
        'total': impot_sur_revenu + prelevements_sociaux,
        'ir': impot_sur_revenu,
        'ps': prelevements_sociaux
    }

def calculate_net_yield_tax(asset, total_annual_tax):
    """Calcule la rentabilité nette de fiscalité en %."""
    loyers_annuels = asset.get('loyers_mensuels', 0) * 12
    charges_annuelles = asset.get('charges', 0) * 12
    taxe_fonciere = asset.get('taxe_fonciere', 0)
    valeur_achat = asset.get('valeur', 0)
    if not valeur_achat: return 0.0

    revenu_final = loyers_annuels - charges_annuelles - taxe_fonciere - total_annual_tax
    return (revenu_final / valeur_achat) * 100

def calculate_savings_effort(asset, loan, total_annual_tax):
    """Calcule le cash-flow mensuel (effort d'épargne)."""
    loyers_mensuels = asset.get('loyers_mensuels', 0)
    charges_mensuelles = asset.get('charges', 0)
    taxe_fonciere_mensuelle = asset.get('taxe_fonciere', 0) / 12
    mensualite_pret = calculate_monthly_payment(loan['montant_initial'], loan['taux_annuel'], loan['duree_annees']) if loan else 0
    
    cash_flow = loyers_mensuels - charges_mensuelles - taxe_fonciere_mensuelle - mensualite_pret - (total_annual_tax / 12)
    return cash_flow