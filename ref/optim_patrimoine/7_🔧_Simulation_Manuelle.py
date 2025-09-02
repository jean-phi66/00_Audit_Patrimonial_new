# pages/8_🕹️_Simulation_Manuelle.py
import streamlit as st
import pandas as pd
import numpy as np
from utils.optim_patrimoine.ui_components import setup_sidebar, display_results, display_kpis, display_allocations_and_charts
from utils.optim_patrimoine.simulation import run_unified_simulation
from utils.state_manager import initialize_session

st.set_page_config(layout="wide", page_title="Simulation Manuelle d'Investissement")
st.title("🕹️ Simulation Manuelle d'Investissement")
st.write("""
Testez vous-même une stratégie d'investissement en définissant manuellement la répartition de votre épargne 
et les caractéristiques d'un éventuel projet immobilier. Les paramètres sont configurés dans la barre latérale.
""")

# Initialiser la session au début du script
initialize_session()

# Le nom de la page est passé à setup_sidebar
params = setup_sidebar(page_name="simulation") # Important pour afficher les sliders d'allocation manuelle
st.session_state.sim_manual_params = params

active_financial_assets_df = params['df_options_financiers_edited'][params['df_options_financiers_edited']['Actif']]
asset_names = active_financial_assets_df.index.tolist()

if st.button("Lancer la Simulation Manuelle", type="primary", use_container_width=True):
    if not asset_names and not params['include_immo']:
        st.warning("Veuillez sélectionner au moins un actif financier ou inclure un projet immobilier pour lancer la simulation.")
    else:
        manual_alloc_sum = sum(params['manual_allocations'].values())
        if asset_names and not (99 <= manual_alloc_sum <= 101): # Tolérance pour les arrondis
            st.error(f"La somme des allocations manuelles pour les actifs financiers doit être de 100%. Actuellement : {manual_alloc_sum:.0f}%")
        else:
            with st.spinner("Simulation de votre stratégie manuelle en cours..."):
                # Préparer les variables d'optimisation pour run_unified_simulation
                # Pour la simulation manuelle, les "poids" sont les allocations divisées par 100
                alloc_weights = []
                if asset_names:
                    alloc_weights = [params['manual_allocations'].get(name, 0) / 100.0 for name in asset_names]
                
                optimization_vars_manual = np.array(alloc_weights)

                if params['include_immo']:
                    # Si le prix est fixé, on l'utilise, sinon on prend le milieu de la fourchette comme exemple
                    immo_price_manual = params['fixed_immo_price'] if params['fix_immo_price'] else np.mean(params['immo_price_range'])
                    if immo_price_manual == 0 and params['immo_price_range'][1] > 0 : # Si prix fixe est 0 mais range est > 0
                        immo_price_manual = params['immo_price_range'][1] # Prendre le max du range si prix fixe est 0
                    
                    optimization_vars_manual = np.append(optimization_vars_manual, immo_price_manual)


                simulation_args_manual = (
                    asset_names, params['initial_capital'], params['monthly_investment'], params['investment_horizon'],
                    active_financial_assets_df.drop(columns=['Actif']) if not active_financial_assets_df.empty else pd.DataFrame(), # S'assurer que c'est un DataFrame
                    params['immo_params'] if params['include_immo'] else None,
                    params['loan_params'] if params['include_immo'] else None,
                    params['marginal_tax_rate'], params['per_deduction_limit']
                )
                
                # Exécuter la simulation
                final_net_worth, final_patrimoine, final_crd, historique, event_logs, kpis, _ = run_unified_simulation(
                    optimization_vars_manual, *simulation_args_manual
                )
                
                st.session_state.manual_sim_results = {
                    "final_net_worth": final_net_worth,
                    "final_patrimoine": final_patrimoine,
                    "final_crd": final_crd,
                    "historique": historique,
                    "event_logs": event_logs,
                    "kpis": kpis,
                    "optimal_vars": optimization_vars_manual, # Garder une trace des "vars" utilisées
                    "simulation_args": simulation_args_manual
                }

                # Afficher les résultats
                st.subheader("📊 Résultat de la Simulation Manuelle")
                st.success(f"**Patrimoine Net Final Estimé : {final_net_worth:,.0f} €**")
                display_kpis(historique, final_net_worth, kpis, params['initial_capital'], params['monthly_investment'])
                display_allocations_and_charts(final_patrimoine, final_crd, historique, event_logs, kpis, optimization_vars_manual, simulation_args_manual)

elif 'manual_sim_results' in st.session_state:
    st.info("Affichage des derniers résultats de simulation manuelle. Modifiez les paramètres et relancez pour une nouvelle analyse.")
    res = st.session_state.manual_sim_results
    st.subheader("📊 Résultat de la Simulation Manuelle")
    st.success(f"**Patrimoine Net Final Estimé : {res['final_net_worth']:,.0f} €**")
    display_kpis(res['historique'], res['final_net_worth'], res['kpis'], res['simulation_args'][1], res['simulation_args'][2])
    display_allocations_and_charts(res['final_patrimoine'], res['final_crd'], res['historique'], res['event_logs'], res['kpis'], res['optimal_vars'], res['simulation_args'])
