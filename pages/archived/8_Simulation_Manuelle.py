import streamlit as st
import pandas as pd
import numpy as np
from ref.optim_patrimoine.ui_components import setup_sidebar, display_results, display_kpis, display_allocations_and_charts
from ref.optim_patrimoine.simulation import run_unified_simulation
#from ref.state_manager import initialize_session

#st.set_page_config(layout="wide", page_title="Simulation Manuelle d'Investissement")
st.title("🕹️ Simulation Manuelle d'Investissement")
st.write("""
Testez vous-même une stratégie d'investissement en définissant manuellement la répartition de votre épargne 
et les caractéristiques d'un éventuel projet immobilier. Les paramètres sont configurés dans la barre latérale.
""")

# Initialiser la session au début du script
#initialize_session()

# Le nom de la page est passé à setup_sidebar
params = setup_sidebar(page_name="simulation")  # Important pour afficher les sliders d'allocation manuelle
st.session_state.sim_manual_params = params

# Filtrer les actifs financiers actifs
active_financial_assets_df = params['df_options_financiers_edited'][params['df_options_financiers_edited']['Actif']]
asset_names = active_financial_assets_df.index.tolist()

# Vérification que asset_names est bien une liste
if not isinstance(asset_names, list):
    raise TypeError(f"'asset_names' doit être une liste, mais une valeur de type {type(asset_names).__name__} a été reçue : {asset_names}")

# Ajout des sliders pour les répartitions initiales et mensuelles
st.sidebar.header("Répartition des Investissements")
st.sidebar.subheader("Répartition Initiale")
params['manual_allocations_initial'] = {}
for asset in asset_names:
    params['manual_allocations_initial'][asset] = st.sidebar.slider(
        f"Allocation Initiale {asset} (%)", 0, 100, 100 // len(asset_names), 1, key=f"initial_{asset}"
    )

st.sidebar.subheader("Répartition Mensuelle")
params['manual_allocations_monthly'] = {}
for asset in asset_names:
    params['manual_allocations_monthly'][asset] = st.sidebar.slider(
        f"Allocation Mensuelle {asset} (%)", 0, 100, 100 // len(asset_names), 1, key=f"monthly_{asset}"
    )

# Vérification des répartitions
initial_alloc_sum = sum(params['manual_allocations_initial'].values())
monthly_alloc_sum = sum(params['manual_allocations_monthly'].values())

# Ajout d'un affichage pour déboguer les valeurs des sliders
st.sidebar.write(f"Somme des allocations initiales : {initial_alloc_sum}%")
st.sidebar.write(f"Somme des allocations mensuelles : {monthly_alloc_sum}%")

# Définir les arguments nécessaires pour la simulation manuelle
simulation_args_manual = (
    params['initial_capital'],  # Capital initial
    params['monthly_investment'],  # Épargne mensuelle
    params['investment_horizon'],  # Horizon d'investissement
    None,  # Paramètres immobiliers
    params['loan_params'] if params['include_immo'] else None,  # Paramètres du prêt
    params['marginal_tax_rate'],  # Taux marginal d'imposition
    params['per_deduction_limit'],  # Plafond annuel PER
    active_financial_assets_df  # Données des actifs financiers actifs
)

if st.button("Lancer la Simulation Manuelle", type="primary", use_container_width=True):
    if not asset_names :
        st.warning("Veuillez sélectionner au moins un actif financier ou inclure un projet immobilier pour lancer la simulation.")
    else:
        # Vérification des répartitions
        if asset_names and not (99 <= initial_alloc_sum <= 101):  # Tolérance pour les arrondis
            st.error(f"La somme des allocations initiales pour les actifs financiers doit être de 100%. Actuellement : {initial_alloc_sum:.0f}%")
        elif asset_names and not (99 <= monthly_alloc_sum <= 101):  # Tolérance pour les arrondis
            st.error(f"La somme des allocations mensuelles pour les actifs financiers doit être de 100%. Actuellement : {monthly_alloc_sum:.0f}%")
        elif len(params['manual_allocations_initial']) != len(asset_names) or len(params['manual_allocations_monthly']) != len(asset_names):
            st.error("Erreur : Le nombre d'allocations ne correspond pas au nombre d'actifs financiers sélectionnés.")
        else:
            with st.spinner("Simulation de votre stratégie manuelle en cours..."):
                # Préparer les variables d'optimisation pour run_unified_simulation
                # Pour la simulation manuelle, les "poids" sont les allocations divisées par 100
                initial_alloc_weights = [params['manual_allocations_initial'].get(name, 0) / 100.0 for name in asset_names]
                monthly_alloc_weights = [params['manual_allocations_monthly'].get(name, 0) / 100.0 for name in asset_names]
                
                # Vérification de la cohérence des tailles
                if len(initial_alloc_weights) != len(asset_names) or len(monthly_alloc_weights) != len(asset_names):
                    st.error("Erreur : Les allocations ne correspondent pas au nombre d'actifs financiers sélectionnés.")
                    st.stop()

                # Construction des variables d'optimisation
                optimization_vars_manual = np.array(initial_alloc_weights + monthly_alloc_weights)

                # Déplacement des affichages de débogage dans un expander
                with st.expander("🔍 Débogage : Inputs de la simulation", expanded=False):
                    st.write(f"Actifs financiers : {asset_names}")
                    st.write(f"Capital initial : {params['initial_capital']}")
                    st.write(f"Épargne mensuelle : {params['monthly_investment']}")
                    st.write(f"Horizon d'investissement : {params['investment_horizon']} ans")
                    st.write(f"Tableau des actifs financiers actifs :")
                    st.dataframe(active_financial_assets_df)
                    st.write(f"Paramètres du prêt : {params['loan_params'] if params['include_immo'] else 'Non inclus'}")
                    st.write(f"Taux marginal d'imposition : {params['marginal_tax_rate']}%")
                    st.write(f"Plafond annuel PER : {params['per_deduction_limit']} €")
                    st.write(f"Variables d'optimisation : {optimization_vars_manual}")

                # Vérification que asset_names est une liste valide
                if not isinstance(asset_names, list):
                    st.error("Erreur : 'asset_names' doit être une liste d'actifs financiers.")
                    st.stop()

                # Vérification que les éléments de asset_names sont des chaînes de caractères
                if not all(isinstance(name, str) for name in asset_names):
                    st.error("Erreur : Tous les éléments de 'asset_names' doivent être des chaînes de caractères.")
                    st.stop()

                # Exécuter la simulation
                final_net_worth, final_patrimoine, final_crd, historique, event_logs, kpis, _ = run_unified_simulation(
                    optimization_vars_manual, *simulation_args_manual, params['per_deduction_limit']
                )
                
                st.session_state.manual_sim_results = {
                    "final_net_worth": final_net_worth,
                    "final_patrimoine": final_patrimoine,
                    "final_crd": final_crd,
                    "historique": historique,
                    "event_logs": event_logs,
                    "kpis": kpis,
                    "optimal_vars": optimization_vars_manual,  # Garder une trace des "vars" utilisées
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

    # Déplacement des affichages de débogage dans un expander
    with st.expander("🔍 Débogage : Inputs pour display_allocations_and_charts", expanded=False):
        st.write(f"Final Patrimoine : {res['final_patrimoine']}")
        st.write(f"Final CRD : {res['final_crd']}")
        st.write(f"Historique : {res['historique']}")
        st.write(f"Event Logs : {res['event_logs']}")
        st.write(f"KPIs : {res['kpis']}")
        st.write(f"Optimal Vars : {res['optimal_vars']}")
        st.write(f"Simulation Args : {res['simulation_args']}")
