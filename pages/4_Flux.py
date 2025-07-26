import streamlit as st

from core.flux_logic import sync_all_flux_data
from core.flux_display import (
    display_revenus_ui,
    display_depenses_ui,
    display_summary
)

# --- Exécution Principale ---

st.title("🌊 Flux Mensuels (Revenus & Dépenses)")
st.markdown("Renseignez ici vos revenus et vos dépenses mensuelles pour calculer votre capacité d'épargne.")

if 'parents' not in st.session_state or not st.session_state.parents or not st.session_state.parents[0].get('prenom'):
    st.warning("⚠️ Veuillez d'abord renseigner les informations du foyer dans la page **1_Famille**.")
    st.stop()

sync_all_flux_data()

col1, col2 = st.columns(2)
with col1:
    display_revenus_ui()
with col2:
    display_depenses_ui()

display_summary()

