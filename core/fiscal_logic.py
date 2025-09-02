import streamlit as st
from .patrimoine_logic import find_associated_loans, calculate_loan_annual_breakdown

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