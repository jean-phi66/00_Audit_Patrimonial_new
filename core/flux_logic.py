import streamlit as st
import uuid
import pandas as pd
from datetime import date
from core.patrimoine_logic import calculate_monthly_payment

# --- Constantes ---
INSEE_DECILES_2021 = {
    "D1 (10%)": 11580, "D2 (20%)": 14660, "D3 (30%)": 17350,
    "D4 (40%)": 19980, "D5 (Médiane)": 22850, "D6 (60%)": 25990,
    "D7 (70%)": 29810, "D8 (80%)": 35020, "D9 (90%)": 42960,
}

# Taux d'épargne par décile de niveau de vie. Source: Insee, enquête Budget de famille 2017.
INSEE_SAVINGS_RATE_2017 = {
    1: -20.1, 2: -3.8, 3: 1.8, 4: 5.7, 5: 8.8,
    6: 11.6, 7: 14.3, 8: 17.5, 9: 22.1, 10: 35.1
}

# --- Fonctions de calcul ---
def calculate_age(born):
    """Calcule l'âge à partir d'une date de naissance."""
    if not born: return 0
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

def find_decile(niveau_de_vie, deciles_data):
    """Trouve le décile de niveau de vie (de 1 à 10)."""
    decile_bounds = sorted(deciles_data.values())
    for i, upper_bound in enumerate(decile_bounds):
        if niveau_de_vie <= upper_bound:
            return i + 1
    return 10

def calculate_consumption_units(parents, enfants):
    """Calcule le nombre d'unités de consommation (UC) du foyer."""
    if not parents: return 1.0
    all_members = parents[1:] + enfants
    return 1.0 + sum(0.3 if calculate_age(m.get('date_naissance')) < 14 else 0.5 for m in all_members)

def sync_all_flux_data():
    """
    Synchronise les revenus et dépenses avec les données des autres pages (Famille, Patrimoine).
    - Salaires des parents.
    - Loyers, charges, et taxes des biens immobiliers.
    - Mensualités des prêts.
    Cette fonction reconstruit les listes à chaque exécution pour garantir la cohérence.
    """
    if 'revenus' not in st.session_state:
        st.session_state.revenus = []
    if 'depenses' not in st.session_state:
        st.session_state.depenses = []

    # --- 1. Conserver les entrées manuelles et séparer les salaires ---
    manual_revenus = [r for r in st.session_state.revenus if 'source_id' not in r and r.get('type') != 'Salaire']
    manual_depenses = [d for d in st.session_state.depenses if 'source_id' not in d]
    
    # On commence avec une liste vide pour les flux automatiques
    auto_revenus = []
    auto_depenses = []

    # --- 2. Synchronisation des salaires ---
    sync_salaires(auto_revenus) # Modifie la liste auto_revenus directement

    # --- 3. Synchronisation avec le patrimoine ---
    # Actifs immobiliers -> Revenus (loyers) et Dépenses (charges, taxe)
    for asset in st.session_state.get('actifs', []):
        asset_id = asset['id']
        asset_type = asset.get('type')

        # Traitement commun à tous les biens immobiliers (taxe foncière)
        if asset_type in ['Immobilier productif', 'Immobilier de jouissance']:
            if asset.get('taxe_fonciere', 0.0) > 0:
                auto_depenses.append({'id': f"taxe_{asset_id}", 'libelle': f"Taxe Foncière de '{asset.get('libelle', 'N/A')}'", 'montant': asset['taxe_fonciere'] / 12, 'categorie': 'Impôts et taxes', 'source_id': asset_id})

        # Traitement spécifique aux biens productifs (loyers, charges)
        if asset_type == 'Immobilier productif':
            if asset.get('loyers_mensuels', 0.0) > 0:
                auto_revenus.append({'id': f"revenu_{asset_id}", 'libelle': f"Loyers de '{asset.get('libelle', 'N/A')}'", 'montant': asset['loyers_mensuels'], 'type': 'Patrimoine', 'source_id': asset_id})
            if asset.get('charges', 0.0) > 0:
                auto_depenses.append({'id': f"charges_{asset_id}", 'libelle': f"Charges de '{asset.get('libelle', 'N/A')}'", 'montant': asset['charges'], 'categorie': 'Logement', 'source_id': asset_id})

    # Passifs (prêts) -> Dépenses (mensualités)
    for passif in st.session_state.get('passifs', []):
        passif_id = passif.get('id', str(uuid.uuid4()))
        if 'id' not in passif: passif['id'] = passif_id
        mensualite = calculate_monthly_payment(passif.get('montant_initial', 0), passif.get('taux_annuel', 0), passif.get('duree_mois', 0))
        if mensualite > 0:
            auto_depenses.append({'id': f"pret_{passif_id}", 'libelle': f"Mensualité de '{passif.get('libelle', 'Prêt N/A')}'", 'montant': mensualite, 'categorie': 'Remboursement de prêts', 'source_id': passif_id})

    # --- 4. Réassemblage des listes ---
    st.session_state.revenus = auto_revenus + manual_revenus
    st.session_state.depenses = auto_depenses + manual_depenses

def sync_salaires(auto_revenus_list):
    """
    S'assure que chaque parent a une entrée de salaire et l'ajoute à la liste fournie.
    """
    # On s'assure que chaque parent a une entrée de salaire
    parent_prenoms = {p['prenom'] for p in st.session_state.get('parents', []) if p.get('prenom')}
    salaire_prenoms = {r['libelle'].split(' ')[1] for r in st.session_state.revenus if r.get('type') == 'Salaire'}

    # Ajouter les salaires manquants
    for prenom in parent_prenoms - salaire_prenoms:
        st.session_state.revenus.insert(0, {
            'id': f"salaire_{prenom}",
            'libelle': f"Salaire {prenom}",
            'montant': 0.0,
            'type': 'Salaire'
        })
    
    # Ajoute les salaires existants et corrects à la liste des revenus auto
    for r in st.session_state.revenus:
        if r.get('type') == 'Salaire' and r['libelle'].split(' ')[1] in parent_prenoms:
            auto_revenus_list.append(r)

def add_flux_item(category):
    """Ajoute un revenu (non-salaire) ou une dépense."""
    if category == 'revenus':
        st.session_state.revenus.append({
            'id': str(uuid.uuid4()),
            'libelle': '',
            'montant': 0.0,
            'type': 'Autre'
        })
    elif category == 'depenses':
        st.session_state.depenses.append({
            'id': str(uuid.uuid4()),
            'libelle': '',
            'montant': 0.0,
            'categorie': 'Dépenses courantes'
        })

def remove_flux_item(category, item_id):
    """Supprime un item de flux par son ID."""
    if category == 'revenus':
        st.session_state.revenus = [r for r in st.session_state.revenus if r['id'] != item_id]
    elif category == 'depenses':
        st.session_state.depenses = [d for d in st.session_state.depenses if d['id'] != item_id]
    st.rerun()
