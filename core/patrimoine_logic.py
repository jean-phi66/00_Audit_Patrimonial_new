import pandas as pd
from datetime import date
import uuid
import streamlit as st
from datetime import date
# --- Fonctions de calcul de prêt ---

def calculate_monthly_payment(principal, annual_rate_pct, duration_months):
    """Calcule la mensualité d'un prêt."""
    if duration_months == 0 or annual_rate_pct is None or principal == 0:
        return 0.0
    
    monthly_rate = (annual_rate_pct / 100) / 12
    total_months = duration_months

    if monthly_rate == 0:
        return principal / total_months if total_months > 0 else 0

    payment = principal * (monthly_rate * (1 + monthly_rate)**total_months) / ((1 + monthly_rate)**total_months - 1)
    return payment

def calculate_crd(principal, annual_rate_pct, duration_months, start_date, on_date=None):
    """Calcule le Capital Restant Dû (CRD) à une date donnée."""
    if not all([principal > 0, annual_rate_pct is not None, duration_months > 0, start_date]):
        return principal

    if on_date is None:
        on_date = date.today()
        
    if start_date > on_date:
        return principal

    # On ne compte que les mois pleins écoulés
    months_passed = (on_date.year - start_date.year) * 12 + (on_date.month - start_date.month)
    total_months = duration_months
    
    if months_passed >= total_months:
        return 0.0

    monthly_payment = calculate_monthly_payment(principal, annual_rate_pct, duration_months)
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
                     Doit contenir 'montant_initial', 'taux_annuel', 'duree_mois', 'date_debut'.
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
    duration_months = loan.get('duree_mois', 0)
    start_date = loan.get('date_debut')

    if not all([principal > 0, annual_rate_pct is not None, duration_months > 0, start_date]):
        return {'capital': 0, 'interest': 0, 'total_paid': 0}

    # --- 1. Calcul du capital remboursé (méthode la plus fiable) ---
    # On prend la fin de l'année N-1 et la fin de l'année N pour capturer tous les paiements de l'année N
    date_debut_annee = date(year - 1, 12, 31)
    date_fin_annee = date(year, 12, 31)

    crd_debut_annee = calculate_crd(principal, annual_rate_pct, duration_months, start_date, on_date=date_debut_annee)
    crd_fin_annee = calculate_crd(principal, annual_rate_pct, duration_months, start_date, on_date=date_fin_annee)
    capital_rembourse = crd_debut_annee - crd_fin_annee

    # --- 2. Calcul du total payé (nombre de mensualités) ---
    mensualite = calculate_monthly_payment(principal, annual_rate_pct, duration_months)
    total_duration_months = duration_months
    
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
            'Passif': dette_associee,
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
            'duree_mois': 240,
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

def calculate_property_tax(asset, loan, tmi_pct, social_tax_pct, year=None):
    """Calcule l'impôt total (IR + PS) sur les revenus fonciers au régime réel."""
    if year is None:
        year = date.today().year

    loyers_annuels = asset.get('loyers_mensuels', 0) * 12
    charges_annuelles = asset.get('charges', 0) * 12
    taxe_fonciere = asset.get('taxe_fonciere', 0)
    
    # Utilisation de la fonction précise pour les intérêts
    loan_breakdown = calculate_loan_annual_breakdown(loan, year=year)
    interets_emprunt = loan_breakdown['interest']

    charges_deductibles = charges_annuelles + taxe_fonciere + interets_emprunt
    revenu_foncier_imposable = max(0, loyers_annuels - charges_deductibles)
    
    impot_sur_revenu = revenu_foncier_imposable * (tmi_pct / 100)
    prelevements_sociaux = revenu_foncier_imposable * (social_tax_pct / 100)

    # --- Calcul de la réduction d'impôt (Pinel) ---
    reduction_pinel = 0
    if asset.get('dispositif_fiscal') == 'Pinel':
        annee_debut = asset.get('annee_debut_dispositif')
        duree = asset.get('duree_dispositif')
        
        if annee_debut and duree and (annee_debut <= year < annee_debut + duree):
            # Le calcul de la réduction se base sur la valeur d'achat, plafonnée à 300 000 €
            base_calcul = min(asset.get('valeur', 0), 300000)
            
            # Taux annuel : 2% les 9 premières années, 1% de la 10e à la 12e
            annees_ecoulees = year - annee_debut
            if 0 <= annees_ecoulees < 9:
                taux_reduction_annuel = 0.02
            elif 9 <= annees_ecoulees < 12 and duree == 12:
                taux_reduction_annuel = 0.01
            else:
                taux_reduction_annuel = 0 # Ne devrait pas arriver dans la condition de l'année
            
            reduction_pinel = base_calcul * taux_reduction_annuel

    total_impot = impot_sur_revenu + prelevements_sociaux - reduction_pinel
    
    return {
        'total': total_impot,
        'ir': impot_sur_revenu,
        'ps': prelevements_sociaux,
        'reduction_pinel': reduction_pinel
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

def calculate_savings_effort(asset, loan, total_annual_tax, year=None):
    """Calcule le cash-flow mensuel (effort d'épargne) pour une année donnée."""
    if year is None:
        year = date.today().year
        
    loyers_mensuels = asset.get('loyers_mensuels', 0)
    charges_mensuelles = asset.get('charges', 0)
    taxe_fonciere_mensuelle = asset.get('taxe_fonciere', 0) / 12

    # Calculer la mensualité pour l'année donnée. Elle est de 0 si le prêt est terminé.
    paiement_annuel_pret = calculate_loan_annual_breakdown(loan, year=year).get('total_paid', 0) if loan else 0
    mensualite_pret = paiement_annuel_pret / 12

    cash_flow = loyers_mensuels - charges_mensuelles - taxe_fonciere_mensuelle - mensualite_pret - (total_annual_tax / 12)
    return cash_flow