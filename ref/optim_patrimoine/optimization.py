# Fichier: optimization.py (version corrigée)
import streamlit as st
import numpy as np
from scipy.optimize import minimize, NonlinearConstraint
from .simulation import run_unified_simulation # MODIFIÉ: Import relatif

def objective_function(optimization_vars, *args_for_simulation):
    final_net_worth, _, _, _, _, _, _ = run_unified_simulation(optimization_vars, *args_for_simulation)
    return -final_net_worth

def cash_flow_constraint(optimization_vars, *args_for_simulation):
    _, _, _, _, _, _, cash_flow_history = run_unified_simulation(optimization_vars, *args_for_simulation)
    return np.array(cash_flow_history)

def setup_and_run_optimization(params):
    """
    Configure et lance l'optimisation pour les actifs financiers.
    """
    active_financial_assets = params['df_options_financiers_edited'][params['df_options_financiers_edited']['Actif']].drop(columns=['Actif'])
    asset_names = active_financial_assets.index.tolist()

    if not asset_names:
        st.warning("Veuillez sélectionner au moins un actif financier pour l'optimisation.")
        return None, None
        
    # Arguments pour la simulation (sans immobilier)
    args_for_simulation = (
        asset_names,
        params['initial_capital'],
        params['monthly_investment'],
        params['investment_horizon'],
        active_financial_assets,
        None,  # immo_params
        None,  # loan_params
        params['marginal_tax_rate'],
        params['per_deduction_limit']
    )
    
    num_alloc_vars = len(asset_names)
    
    # Configuration pour l'optimisation des actifs financiers uniquement
    initial_guess = np.array([1.0/num_alloc_vars] * num_alloc_vars)
    bounds = [(0, 1)] * num_alloc_vars
    
    # Contraintes: la somme des poids doit être 1 et le cash-flow doit être positif
    constraints = [
        {'type': 'eq', 'fun': lambda x: 1 - np.sum(x)},
        # La fonction de contrainte est appelée par scipy avec `x` uniquement.
        # Nous utilisons une lambda pour capturer les `args_for_simulation` et les passer.
        NonlinearConstraint(lambda x: cash_flow_constraint(x, *args_for_simulation), 0, np.inf)
    ]
    
    # Ajout de la contrainte pour le plafond PER
    if 'PER' in asset_names:
        per_index = asset_names.index('PER')
        # On se base sur l'épargne annuelle prévue pour contraindre l'allocation
        annual_investment = params['monthly_investment'] * 12
        per_constraint = {
            'type': 'ineq', # La fonction doit être >= 0
            'fun': lambda x: params['per_deduction_limit'] - (x[per_index] * annual_investment)
        }
        constraints.append(per_constraint)

    objective_to_pass = objective_function

    opt_result = minimize(
        objective_to_pass,
        initial_guess,
        args=args_for_simulation,
        method='SLSQP',
        bounds=bounds,
        constraints=constraints,
        options={'maxiter': 500, 'ftol': 1e-9}
    )
    
    return opt_result, args_for_simulation