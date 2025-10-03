import streamlit as st

import sys
import os
# Add project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.endettement_charts import (
    calculate_weighted_income,
    calculate_current_debt_service
)
from core.endettement_display import (
    display_results,
    display_debt_ratio_breakdown_chart,
    display_loan_simulator,
    display_weighted_income_details
)
# --- Exécution Principale ---

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
display_weighted_income_details(weighted_income_data)

remaining_capacity = display_results(total_weighted_income, total_current_debt, max_debt_ratio)

if remaining_capacity is not None:
    st.markdown("---")
    display_debt_ratio_breakdown_chart(debt_data["details"], total_weighted_income, max_debt_ratio)

    st.markdown("---")
    display_loan_simulator(remaining_capacity)
