import streamlit as st
from datetime import date
from .patrimoine_logic import find_associated_loans, calculate_loan_annual_breakdown

try:
    from utils.openfisca_utils import analyser_fiscalite_foyer
    OPENFISCA_AVAILABLE = True
except ImportError:
    OPENFISCA_AVAILABLE = False

def calculate_monthly_income_tax():
    """
    Calcule l'impôt sur le revenu mensuel basé sur les revenus du foyer.
    Retourne 0 si les données sont insuffisantes ou en cas d'erreur.
    """
    if not OPENFISCA_AVAILABLE:
        # Calcul approximatif si OpenFisca n'est pas disponible
        return calculate_simple_income_tax_monthly()
    
    try:
        # Récupération des données du foyer
        parents = st.session_state.get('parents', [])
        enfants = st.session_state.get('enfants', [])
        
        if not parents:
            return 0
        
        # Calcul des revenus annuels
        revenus_annuels = {}
        for revenu in st.session_state.get('revenus', []):
            if revenu.get('type') == 'Salaire' and revenu.get('montant', 0) > 0:
                prenom = revenu.get('libelle', 'Inconnu').split(' ')[-1]
                revenus_annuels[prenom] = revenu.get('montant', 0) * 12
        
        # Calcul du revenu foncier net
        _, revenu_foncier_net = get_revenus_imposables(date.today().year)
        
        # Appel à OpenFisca
        fiscalite_results = analyser_fiscalite_foyer(
            annee=date.today().year,
            parents=parents,
            enfants=enfants,
            revenus_annuels=revenus_annuels,
            revenu_foncier_net=revenu_foncier_net,
            est_parent_isole=(len(parents) == 1)
        )
        
        # Retour de l'IR mensuel
        ir_annuel = fiscalite_results.get('ir_net', 0)
        return round(ir_annuel / 12, 2)
        
    except Exception as e:
        # En cas d'erreur, utiliser le calcul simplifié
        return calculate_simple_income_tax_monthly()

def calculate_simple_income_tax_monthly():
    """
    Calcul simplifié de l'impôt sur le revenu mensuel (fallback).
    Utilise une approximation basée sur les tranches d'imposition 2024.
    """
    try:
        # Calcul du revenu total annuel
        total_revenus_annuel = 0
        for revenu in st.session_state.get('revenus', []):
            if revenu.get('type') == 'Salaire' and revenu.get('montant', 0) > 0:
                total_revenus_annuel += revenu.get('montant', 0) * 12
        
        # Revenus fonciers
        _, revenu_foncier_net = get_revenus_imposables(date.today().year)
        total_revenus_annuel += revenu_foncier_net
        
        # Estimation du nombre de parts fiscales
        parents = st.session_state.get('parents', [])
        enfants = st.session_state.get('enfants', [])
        parts_fiscales = len(parents) if parents else 1
        parts_fiscales += len(enfants) * 0.5
        
        # Calcul simplifié avec les tranches 2024
        revenu_par_part = total_revenus_annuel / parts_fiscales
        
        # Tranches d'imposition 2024 (approximation)
        if revenu_par_part <= 11294:
            ir_annuel = 0
        elif revenu_par_part <= 28797:
            ir_annuel = (revenu_par_part - 11294) * 0.11 * parts_fiscales
        elif revenu_par_part <= 82341:
            ir_annuel = (1925.33 + (revenu_par_part - 28797) * 0.30) * parts_fiscales
        elif revenu_par_part <= 177106:
            ir_annuel = (17988.63 + (revenu_par_part - 82341) * 0.41) * parts_fiscales
        else:
            ir_annuel = (56851.28 + (revenu_par_part - 177106) * 0.45) * parts_fiscales
        
        return round(max(0, ir_annuel) / 12, 2)
        
    except Exception:
        return 0

def get_revenus_imposables(year_of_analysis):
    """
    Calcule les revenus imposables (salaires et fonciers) pour une année donnée.
    Cette fonction est partagée par les pages d'analyse fiscale.
    """
    # 1. Revenus du travail
    revenus_salaires = {}
    for revenu in st.session_state.get('revenus', []):
        if revenu.get('type') == 'Salaire':
            # Suppose que le libellé est "Salaire Prénom"
            prenom = revenu.get('libelle', 'Inconnu').split(' ')[-1]
            revenus_salaires[prenom] = revenu.get('montant', 0) * 12

    # 2. Revenus fonciers (hors LMNP)
    total_loyers_bruts_annee = 0
    total_charges_deductibles_annee = 0
    passifs = st.session_state.get('passifs', [])
    actifs_productifs = [a for a in st.session_state.get('actifs', []) if a.get('type') == 'Immobilier productif' and a.get('mode_exploitation') != 'Location Meublée']

    for asset in actifs_productifs:
        loyers_annuels = asset.get('loyers_mensuels', 0) * 12
        charges_annuelles = asset.get('charges', 0) * 12
        taxe_fonciere = asset.get('taxe_fonciere', 0)
        loans = find_associated_loans(asset.get('id'), passifs)
        interets_emprunt = sum(calculate_loan_annual_breakdown(l, year=year_of_analysis).get('interest', 0) for l in loans)
        total_loyers_bruts_annee += loyers_annuels
        total_charges_deductibles_annee += (charges_annuelles + taxe_fonciere + interets_emprunt)

    revenu_foncier_net = max(0, total_loyers_bruts_annee - total_charges_deductibles_annee)
    return revenus_salaires, revenu_foncier_net