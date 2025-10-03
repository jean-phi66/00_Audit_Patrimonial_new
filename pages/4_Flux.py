import streamlit as st
import pandas as pd

from core.flux_logic import sync_all_flux_data
from core.flux_display import (
    display_revenus_ui,
    display_depenses_ui,
    display_summary,
    display_detailed_tables
)

# --- Exécution Principale ---

st.title("🌊 Flux Mensuels (Revenus & Dépenses)")
st.markdown("Renseignez ici vos revenus et vos dépenses mensuelles pour calculer votre capacité d'épargne.")

# --- Options dans la sidebar ---
st.sidebar.header("⚙️ Options")
if 'auto_ir_enabled' not in st.session_state:
    st.session_state.auto_ir_enabled = True

auto_ir_enabled = st.sidebar.checkbox(
    "🏛️ Calcul automatique de l'impôt sur le revenu", 
    value=st.session_state.auto_ir_enabled,
    help="Si activé, l'impôt sur le revenu est calculé automatiquement en fonction des salaires et revenus fonciers."
)
st.session_state.auto_ir_enabled = auto_ir_enabled

if not auto_ir_enabled:
    st.sidebar.info("💡 Le calcul automatique de l'IR est désactivé. Vous pouvez l'ajouter manuellement dans les dépenses.")

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

# Affichage des tableaux détaillés
display_detailed_tables()

