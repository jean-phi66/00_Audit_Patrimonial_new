import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

import sys
import os
# Add project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.patrimoine_logic import calculate_monthly_payment
from core.endettement_charts import (
    calculate_weighted_income,
    calculate_current_debt_service, 
    calculate_endettement_metrics,
    create_debt_gauge_chart,
    create_debt_breakdown_chart,
    generate_endettement_charts,
    RENTAL_INCOME_WEIGHT
)

# --- Constantes de calcul ---
# RENTAL_INCOME_WEIGHT maintenant importée du module centralisé

# --- Fonctions de calcul ---

# calculate_weighted_income maintenant importée du module centralisé

# calculate_current_debt_service maintenant importée du module centralisé

def calculate_loan_principal(monthly_payment, annual_rate_pct, duration_months):
    """
    Calcule le capital d'un prêt à partir de la mensualité, du taux et de la durée.
    Inverse de `calculate_monthly_payment`.
    """
    if duration_months <= 0 or annual_rate_pct is None or monthly_payment <= 0:
        return 0.0

    monthly_rate = (annual_rate_pct / 100) / 12

    if monthly_rate == 0:
        return monthly_payment * duration_months

    principal = monthly_payment * (1 - (1 + monthly_rate)**-duration_months) / monthly_rate
    return principal

# --- Fonctions d'UI ---

def display_results(weighted_income, current_debt, max_debt_ratio_pct):
    """Affiche les résultats du calcul."""
    
    st.subheader("📊 Résultats")
    
    if weighted_income == 0:
        st.warning("Les revenus pondérés sont de 0. Impossible de calculer le taux d'endettement.")
        return

    # Calculs
    max_debt_service = weighted_income * (max_debt_ratio_pct / 100)
    current_debt_ratio_pct = (current_debt / weighted_income) * 100 if weighted_income > 0 else 0
    remaining_capacity = max(0, max_debt_service - current_debt)

    # Affichage des métriques
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Revenus Pondérés", f"{weighted_income:,.0f} €/mois")
    col2.metric("Charges de Prêts", f"{current_debt:,.0f} €/mois")
    col3.metric(
        "Taux d'Endettement Actuel",
        f"{current_debt_ratio_pct:.2f} %",
        delta=f"{current_debt_ratio_pct - max_debt_ratio_pct:.2f} % pts",
        delta_color="inverse"
    )
    col4.metric("Capacité d'Emprunt Restante", f"{remaining_capacity:,.0f} €/mois")

    # Jauge de visualisation (utilise la fonction centralisée)
    metrics_data = calculate_endettement_metrics([], [], max_debt_ratio_pct)
    metrics_data.update({
        'weighted_income': weighted_income,
        'current_debt': current_debt,
        'current_debt_ratio_pct': current_debt_ratio_pct,
        'max_debt_ratio_pct': max_debt_ratio_pct
    })
    fig = create_debt_gauge_chart(metrics_data)
    fig.update_layout(height=300, margin=dict(t=50, b=50, l=50, r=50))
    st.plotly_chart(fig, use_container_width=True)

    return remaining_capacity

def display_debt_ratio_breakdown_chart(debt_details, weighted_income, max_debt_ratio_pct):
    """Affiche un graphique de la répartition du taux d'endettement par prêt (utilise les fonctions centralisées)."""
    st.subheader("Répartition du Taux d'Endettement par Prêt")
    
    if not debt_details:
        st.info("Aucun prêt en cours à afficher.")
        return
    
    if weighted_income == 0:
        st.warning("Revenus pondérés nuls, impossible de calculer la répartition.")
        return

    # Utiliser la fonction centralisée
    metrics_data = {
        'debt_details': debt_details,
        'weighted_income': weighted_income,
        'max_debt_ratio_pct': max_debt_ratio_pct
    }
    fig = create_debt_breakdown_chart(metrics_data)
    fig.update_layout(height=300)  # Ajuster la hauteur pour l'interface GUI
    st.plotly_chart(fig, use_container_width=True)

def display_loan_simulator(remaining_capacity):
    """Affiche un simulateur de prêt basé sur la capacité restante."""
    st.subheader("🏦 Simulation de nouveau prêt")
    if remaining_capacity <= 0:
        st.info("Votre capacité d'emprunt restante est nulle ou négative. Vous ne pouvez pas contracter de nouveau prêt selon ces critères.")
        return

    st.markdown(f"Avec une capacité de remboursement de **{remaining_capacity:,.2f} €/mois**, voici ce que vous pourriez emprunter :")
    
    sim_col1, sim_col2 = st.columns(2)
    with sim_col1:
        sim_duree_annees = st.slider("Durée du nouveau prêt (années)", min_value=5, max_value=30, value=25, step=1)
    with sim_col2:
        sim_taux_annuel = st.slider("Taux d'intérêt annuel (%)", min_value=0.5, max_value=8.0, value=3.5, step=0.1)

    sim_duree_mois = sim_duree_annees * 12
    
    montant_empruntable = calculate_loan_principal(remaining_capacity, sim_taux_annuel, sim_duree_mois)

    st.metric(
        label=f"Montant empruntable sur {sim_duree_annees} ans à {sim_taux_annuel}%",
        value=f"{montant_empruntable:,.0f} €"
    )

# --- Exécution Principale ---

#def main():
st.title("🏦 Capacité d'Endettement")
st.markdown("Cette page analyse votre capacité à contracter de nouveaux prêts en fonction de vos revenus et de vos charges de crédits existantes.")

# Vérification des données
if 'revenus' not in st.session_state or 'passifs' not in st.session_state:
    st.warning("⚠️ Veuillez d'abord renseigner vos revenus (page **4_Flux**) et vos passifs (page **2_Patrimoine**).")
    st.stop()

# --- Paramètres ---
st.sidebar.header("Paramètres de Calcul")
max_debt_ratio = st.sidebar.radio(
    "Taux d'endettement maximum",
    options=[35, 40],
    format_func=lambda x: f"{x} %",
    index=0,
    help="Le taux d'endettement maximum autorisé par les banques. La norme est de 35%."
)

# --- Calculs ---
revenus = st.session_state.get('revenus', [])
passifs = st.session_state.get('passifs', [])

weighted_income_data = calculate_weighted_income(revenus)
debt_data = calculate_current_debt_service(passifs)
total_weighted_income = weighted_income_data["total"]
total_current_debt = debt_data["total"]

# --- Affichage ---
with st.expander("Détail des revenus pris en compte", expanded=False):
    st.markdown(f"""
    - **Salaires totaux :** `{weighted_income_data["salaires"]:,.2f} €` (pris à 100%)
    - **Loyers bruts totaux :** `{weighted_income_data["loyers_bruts"]:,.2f} €`
    - **Loyers pondérés ({RENTAL_INCOME_WEIGHT:.0%}) :** `{weighted_income_data["loyers_ponderes"]:,.2f} €`
    - **Total des revenus pondérés :** `{total_weighted_income:,.2f} €`
    
    *Les "Autres revenus" ne sont pas pris en compte dans ce calcul.*
    """)

remaining_capacity = display_results(total_weighted_income, total_current_debt, max_debt_ratio)

if remaining_capacity is not None:
    st.markdown("---")
    display_debt_ratio_breakdown_chart(debt_data["details"], total_weighted_income, max_debt_ratio)

    st.markdown("---")
    display_loan_simulator(remaining_capacity)


#if __name__ == "__main__":
#    main()