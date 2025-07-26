import streamlit as st
from datetime import date
import os
import io
import pandas as pd
import numpy as np
import plotly.io as pio
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
import importlib

from core.report_generator import generate_report_safe

# --- Vérification de la disponibilité des modules et fonctions ---

def import_from(module_name, func_name):
    """Tente d'importer une fonction depuis un module de page."""
    try:
        module = importlib.import_module(f"pages.{module_name}")
        return getattr(module, func_name), True
    except (ImportError, AttributeError):
        return None, False

# --- Fonctions importées des autres pages ---
generate_immo_projection_data, FOCUS_IMMO_AVAILABLE = import_from("3_Focus_Immobilier", "generate_projection_data")
create_cash_flow_projection_fig, _ = import_from("3_Focus_Immobilier", "create_cash_flow_projection_fig")

calculate_weighted_income, CAP_ENDETTEMENT_AVAILABLE = import_from("7_Capacite_Endettement", "calculate_weighted_income")
calculate_current_debt_service, _ = import_from("7_Capacite_Endettement", "calculate_current_debt_service")

generate_gantt_data, PROJECTION_AVAILABLE = import_from("4_Projection", "generate_gantt_data")
generate_financial_projection, _ = import_from("4_Projection", "generate_financial_projection")
# create_gantt_chart_fig, _ = import_from("4_Projection", "create_gantt_chart_fig")

get_revenus_imposables_fiscalite, FOCUS_FISCALITE_AVAILABLE = import_from("8_Focus_Fiscalite", "get_revenus_imposables")
analyser_fiscalite_foyer_fiscalite, _ = import_from("8_Focus_Fiscalite", "analyser_fiscalite_foyer")
simuler_evolution_fiscalite, _ = import_from("8_Focus_Fiscalite", "simuler_evolution_fiscalite")
display_income_evolution_chart, _ = import_from("8_Focus_Fiscalite", "display_income_evolution_chart")

analyser_optimisation_per, OPTIMISATION_PER_AVAILABLE = import_from("9_Optimisation_PER", "analyser_optimisation_per")

# --- Vérification des dépendances critiques ---
try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False

try:
    from utils.openfisca_utils import analyser_fiscalite_foyer
    OPENFISCA_AVAILABLE = True
except ImportError:
    OPENFISCA_AVAILABLE = False

# --- Interface Streamlit ---

st.title("📄 Génération de Rapport")
st.markdown("Cochez les sections que vous souhaitez inclure dans votre rapport PDF personnalisé.")

if not FPDF_AVAILABLE:
    st.error("La bibliothèque `fpdf2` est nécessaire. Installez-la avec `pip install fpdf2`.")
    st.stop()
if 'parents' not in st.session_state or not st.session_state.parents:
    st.warning("⚠️ Veuillez d'abord renseigner les informations du foyer (page **1_Famille**).")
    st.stop()

# --- Sélection des sections ---
st.markdown("---")
st.subheader("Choix des sections du rapport")

cols = st.columns(2)
with cols[0]:
    st.markdown("##### 📋 Blocs principaux")
    selections = {
        'famille': st.checkbox("1. Composition du Foyer", value=True, key="cb_famille"),
        'patrimoine': st.checkbox("2. Bilan Patrimonial", value=True, key="cb_patrimoine"),
        'flux': st.checkbox("3. Flux Financiers", value=True, key="cb_flux"),
        'endettement': st.checkbox("4. Capacité d'Endettement", value=True, disabled=not CAP_ENDETTEMENT_AVAILABLE, key="cb_endettement"),
    }
with cols[1]:
    st.markdown("##### 🔎 Analyses & Projections")
    selections['projection'] = st.checkbox("5. Projection des Étapes de Vie", value=True, disabled=not PROJECTION_AVAILABLE, key="cb_projection")
    selections['immo'] = st.checkbox("6. Focus Immobilier Locatif", value=True, disabled=not FOCUS_IMMO_AVAILABLE, key="cb_immo")
    selections['fiscalite'] = st.checkbox("7. Focus Fiscalité", value=True, disabled=not OPENFISCA_AVAILABLE, key="cb_fiscalite")
    
    per_sim_done = 'per_simulation_results' in st.session_state and "error" not in st.session_state.per_simulation_results
    selections['per'] = st.checkbox("8. Optimisation PER", value=True, disabled=not OPENFISCA_AVAILABLE or not per_sim_done, help="Nécessite d'avoir lancé une simulation sur la page Optimisation PER.", key="cb_per")

st.markdown("---")

if st.sidebar.button("🚀 Générer mon rapport PDF", use_container_width=True, type="primary"):
    with st.spinner("Création du rapport en cours..."):
        # --- Récupération de toutes les données et paramètres nécessaires ---
        parents = st.session_state.get('parents', [])
        enfants = st.session_state.get('enfants', [])
        actifs = st.session_state.get('actifs', [])
        passifs = st.session_state.get('passifs', [])
        revenus = st.session_state.get('revenus', [])
        depenses = st.session_state.get('depenses', [])
        per_results = st.session_state.get('per_simulation_results', {})

        # Récupération des paramètres des autres pages
        settings = {
            'max_debt_ratio': st.session_state.get('endettement_max_debt_ratio', 35),
            'projection_settings': st.session_state.get('projection_settings', {}),
            'duree_projection': st.session_state.get('projection_duree', 25),
            'immo_tmi': st.session_state.get('immo_tmi', 30),
            'immo_projection_duration': st.session_state.get('immo_projection_duration', 10),
            'annee_fiscalite': st.session_state.get('fiscalite_annee', date.today().year),
            'revenu_max_fiscalite': st.session_state.get('fiscalite_revenu_max', 150000),
            'est_parent_isole_fiscalite': st.session_state.get('fiscalite_parent_isole', False)
        }

        # Dictionnaire des fonctions et disponibilités à passer au générateur
        funcs = {
            'FOCUS_IMMO_AVAILABLE': FOCUS_IMMO_AVAILABLE,
            'generate_immo_projection_data': generate_immo_projection_data,
            'create_cash_flow_projection_fig': create_cash_flow_projection_fig,
            'CAP_ENDETTEMENT_AVAILABLE': CAP_ENDETTEMENT_AVAILABLE,
            'calculate_weighted_income': calculate_weighted_income,
            'calculate_current_debt_service': calculate_current_debt_service,
            'PROJECTION_AVAILABLE': PROJECTION_AVAILABLE,
            'generate_gantt_data': generate_gantt_data,
            'generate_financial_projection': generate_financial_projection,
            'FOCUS_FISCALITE_AVAILABLE': FOCUS_FISCALITE_AVAILABLE,
            'get_revenus_imposables_fiscalite': get_revenus_imposables_fiscalite,
            'analyser_fiscalite_foyer_fiscalite': analyser_fiscalite_foyer_fiscalite,
            'simuler_evolution_fiscalite': simuler_evolution_fiscalite,
            'display_income_evolution_chart': display_income_evolution_chart,
            'OPTIMISATION_PER_AVAILABLE': OPTIMISATION_PER_AVAILABLE,
            'analyser_optimisation_per': analyser_optimisation_per,
            'OPENFISCA_AVAILABLE': OPENFISCA_AVAILABLE
        }

        # Génération du rapport
        pdf_data, pdf_error = generate_report_safe(selections, parents, enfants, actifs, passifs, revenus, depenses, per_results, settings, funcs)
        
        # Création du nom de fichier dynamique
        client_name = parents[0].get('prenom', 'client') if parents else 'client'
        file_name = f"Rapport_Patrimonial_{client_name}_{date.today().strftime('%Y-%m-%d')}.pdf"
        if pdf_error:
            st.error(pdf_error)
        else:
            with cols[0]:
                st.success("✅ Rapport généré avec succès !")
                st.sidebar.download_button(
                    label="📥 Télécharger le rapport PDF",
                    data=pdf_data,
                    file_name=file_name,
                    mime="application/pdf",
                    use_container_width=False)
