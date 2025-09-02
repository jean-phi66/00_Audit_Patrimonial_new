# pages/7_🚀_Optimisation_Investissement.py
import streamlit as st
from utils.optim_patrimoine.ui_components import setup_sidebar, display_results
from utils.optim_patrimoine.optimization import setup_and_run_optimization
from utils.state_manager import initialize_session

st.set_page_config(layout="wide", page_title="Optimisation d'Investissement")
st.title("🚀 Optimisation d'Investissement")
st.write("""
Laissez l'algorithme trouver la meilleure allocation d'actifs pour atteindre vos objectifs financiers 
en fonction de vos paramètres définis dans la barre latérale.
""")

# Initialiser la session au début du script
initialize_session()

# Le nom de la page est passé à setup_sidebar pour un comportement conditionnel si nécessaire
params = setup_sidebar(page_name="optimisation")
st.session_state.optim_params = params # Sauvegarder les paramètres pour un accès facile

if st.button("Lancer l'Optimisation", type="primary", use_container_width=True):
    if not params['df_options_financiers_edited'][params['df_options_financiers_edited']['Actif']].empty or params['include_immo']:
        with st.spinner("Recherche de la stratégie optimale en cours..."):
            opt_result, simulation_args = setup_and_run_optimization(params)
            if opt_result is not None and simulation_args is not None:
                st.session_state.opt_result = opt_result
                st.session_state.simulation_args = simulation_args
                display_results(opt_result, simulation_args)
            elif opt_result is None and simulation_args is None and not params['fix_immo_price']: # Cas où aucun actif n'est sélectionné
                 st.warning("Veuillez sélectionner au moins un actif financier ou inclure un projet immobilier pour lancer l'optimisation.")
            # Le cas de l'erreur de mensualité pour prix fixe est géré dans setup_and_run_optimization
            
    else:
        st.warning("Veuillez sélectionner au moins un actif financier ou inclure un projet immobilier pour lancer l'optimisation.")

elif 'opt_result' in st.session_state and 'simulation_args' in st.session_state:
    st.info("Affichage des derniers résultats d'optimisation. Modifiez les paramètres et relancez pour une nouvelle analyse.")
    display_results(st.session_state.opt_result, st.session_state.simulation_args)
