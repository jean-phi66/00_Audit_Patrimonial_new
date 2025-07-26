import streamlit as st
from datetime import date

from core.projection_logic import (
    generate_gantt_data,
    generate_financial_projection,
    OPENFISCA_UTILITY_AVAILABLE
)
from core.projection_display import (
    display_settings_ui,
    display_gantt_chart,
    display_loan_crd_chart,
    display_projection_table,
    display_projection_chart,
    display_annual_tax_chart,
    display_cumulative_tax_at_retirement
)

# --- Exécution Principale ---

st.title("🗓️ Projection des grandes étapes de vie")
st.markdown("Définissez les âges clés pour chaque membre du foyer afin de visualiser une frise chronologique de leurs activités.")

if 'parents' not in st.session_state or not st.session_state.parents or not st.session_state.parents[0].get('prenom'):
    st.warning("⚠️ Veuillez d'abord renseigner les informations du foyer dans la page **1_Famille**.")
    st.stop()

if 'projection_settings' not in st.session_state:
    st.session_state.projection_settings = {}

parents = st.session_state.parents
enfants = st.session_state.enfants

duree_projection, settings = display_settings_ui(parents, enfants)

gantt_data = generate_gantt_data(parents, enfants, settings, duree_projection)
display_gantt_chart(gantt_data, duree_projection, parents, enfants)

passifs = st.session_state.get('passifs', [])
df_projection = generate_financial_projection(parents, enfants, passifs, settings, duree_projection)

st.header("📈 Projection Financière Annuelle")
if not OPENFISCA_UTILITY_AVAILABLE:
    error_msg = st.session_state.get('openfisca_import_error', "Erreur inconnue.")
    st.warning(
        "**Le module OpenFisca n'a pas pu être chargé.** Les calculs d'impôts seront des estimations simplifiées (taux forfaitaire de 15%).\n\n"
        f"**Erreur technique :** `{error_msg}`\n\n"
        "Pour un calcul précis, assurez-vous que le package `openfisca-france` est bien installé dans votre environnement."
    )

if df_projection.empty:
    st.info("Aucune donnée de projection financière à afficher.")
else:
    with st.expander("Détails de la projection financière"):
        display_projection_table(df_projection)
    display_projection_chart(df_projection)

    # Nouveaux graphiques et métriques pour la fiscalité
    st.markdown("---")
    st.header("🔎 Focus Fiscalité")
    display_annual_tax_chart(df_projection)
    display_cumulative_tax_at_retirement(df_projection, parents, settings)
    
    st.markdown("---")
    st.header("🔎 Focus Emprunts")
    display_loan_crd_chart(df_projection, passifs)

# --- Exécution Principale ---

"""Fonction principale pour exécuter la page de projection."""
st.title("🗓️ Projection des grandes étapes de vie")
st.markdown("Définissez les âges clés pour chaque membre du foyer afin de visualiser une frise chronologique de leurs activités.")

if 'parents' not in st.session_state or not st.session_state.parents or not st.session_state.parents[0].get('prenom'):
    st.warning("⚠️ Veuillez d'abord renseigner les informations du foyer dans la page **1_Famille**.")
    st.stop()

if 'projection_settings' not in st.session_state:
    st.session_state.projection_settings = {}

parents = st.session_state.parents
enfants = st.session_state.enfants

duree_projection, settings = display_settings_ui(parents, enfants)

gantt_data = generate_gantt_data(parents, enfants, settings, duree_projection)
display_gantt_chart(gantt_data, duree_projection, parents, enfants)

passifs = st.session_state.get('passifs', [])
df_projection = generate_financial_projection(parents, enfants, passifs, settings, duree_projection)

st.header("📈 Projection Financière Annuelle")
if not OPENFISCA_UTILITY_AVAILABLE:
    error_msg = st.session_state.get('openfisca_import_error', "Erreur inconnue.")
    st.warning(
        "**Le module OpenFisca n'a pas pu être chargé.** Les calculs d'impôts seront des estimations simplifiées (taux forfaitaire de 15%).\n\n"
        f"**Erreur technique :** `{error_msg}`\n\n"
        "Pour un calcul précis, assurez-vous que le package `openfisca-france` est bien installé dans votre environnement."
    )

if df_projection.empty:
    st.info("Aucune donnée de projection financière à afficher.")
else:
    with st.expander("Détails de la projection financière"):
        display_projection_table(df_projection)
    display_projection_chart(df_projection)

    # Nouveaux graphiques et métriques pour la fiscalité
    st.markdown("---")
    st.header("🔎 Focus Fiscalité")
    display_annual_tax_chart(df_projection)
    display_cumulative_tax_at_retirement(df_projection, parents, settings)
    
    st.markdown("---")
    st.header("🔎 Focus Emprunts")
    display_loan_crd_chart(df_projection, passifs)
