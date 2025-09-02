# Fichier: simulation.py (version mise à jour)
import pandas as pd
import numpy_financial as npf

def calculate_monthly_payment(loan_amount, rate_pct, duration_years):
    """
    Calcule la mensualité d'un prêt à taux fixe.
    """
    if loan_amount <= 0 or duration_years <= 0 or rate_pct < 0:
        return 0
    monthly_rate = (rate_pct / 100) / 12
    n_months = duration_years * 12
    if n_months <= 0:
        return float('inf')
    return -npf.pmt(monthly_rate, n_months, loan_amount)

def run_unified_simulation(optimization_vars, asset_names, initial_capital, monthly_investment,
                           investment_horizon, df_options_financiers, immo_params, loan_params,
                           marginal_tax_rate, per_deduction_limit):
    """
    Exécute une simulation complète de la croissance du patrimoine sur l'horizon de temps.
    """
    # Vérification que asset_names est une liste valide
    if not isinstance(asset_names, list):
        raise TypeError(f"'asset_names' doit être une liste, mais une valeur de type {type(asset_names).__name__} a été reçue.")
    
    asset_names = list(asset_names)

    # Détermine si un projet immobilier est inclus
    include_immo = immo_params is not None
    financial_asset_names = [name for name in asset_names if name != 'Projet Immobilier']

    # Sépare les variables d'optimisation entre les actifs financiers et le prix cible de l'immobilier
    if include_immo:
        allocation_weights = optimization_vars[:-1] if len(financial_asset_names) > 0 else []
        target_immo_price = optimization_vars[-1]
    else:
        allocation_weights, target_immo_price = optimization_vars, 0

    # Crée un dictionnaire pour les allocations des actifs financiers
    allocation = dict(zip(financial_asset_names, allocation_weights))

    # Initialisation du patrimoine pour chaque actif financier et immobilier
    patrimoine = {asset: 0.0 for asset in financial_asset_names}
    patrimoine['Immobilier (Bien)'] = 0.0

    # Colonnes pour l'historique des flux financiers et des détails immobiliers
    flow_cols = [f"Flux {name}" for name in financial_asset_names]
    immo_detail_cols = ['Remboursement Annuel Prêt', 'Loyers Bruts', "Intérêts d'Emprunt", 'Impôt Locatif', 'Cash-Flow Net Immo']
    base_cols = list(patrimoine.keys()) + ['Dette Immobilière', 'Total Net']
    hist_cols = base_cols + immo_detail_cols + ['Soutien Épargne Immo'] + flow_cols
    historique = pd.DataFrame(0.0, index=range(investment_horizon + 1), columns=hist_cols)

    # Initialisation des indicateurs clés de performance (KPIs)
    kpi_trackers = {'total_tax_saving_per': 0, 'total_rental_tax': 0, 'total_interest_paid': 0, 'total_rent_received': 0, 'leaked_cash': 0}

    # Liste pour enregistrer les événements importants et le cash-flow annuel
    event_logs = []
    cash_flow_history = []

    # Variables pour gérer le prêt immobilier
    loan_crd, annuite_pret, immo_purchase_done = 0, 0, False

    # Initialisation des actifs financiers avec le capital de départ
    for asset, weight in allocation.items():
        if asset in patrimoine:
            frais_entree = df_options_financiers.loc[asset, 'Frais Entrée (%)'] / 100
            capital_flow = initial_capital * weight
            patrimoine[asset] += capital_flow * (1 - frais_entree)
            historique.loc[0, f"Flux {asset}"] = capital_flow

    # Simulation année par année
    for year in range(1, investment_horizon + 1):
        # Initialisation explicite du cash disponible pour l'investissement
        cash_for_investment = 0

        # Achat immobilier à l'année 1 si inclus
        if include_immo and not immo_purchase_done and year == 1:
            immo_purchase_done = True
            event_logs.append(f"Année 1: Achat d'un bien de {target_immo_price:,.0f} €.")
            patrimoine['Immobilier (Bien)'] = target_immo_price * (1 - immo_params['frais_notaire_pct'] / 100)
            loan_crd = target_immo_price
            annuite_pret = calculate_monthly_payment(loan_crd, loan_params['rate'], loan_params['duration']) * 12

        # Mise à jour des rendements des actifs financiers
        for asset in df_options_financiers.index:
            if asset in patrimoine and patrimoine[asset] > 0:
                rendement = df_options_financiers.loc[asset, 'Rendement Annuel (%)'] / 100
                
                # Gestion spécifique pour SCPI (ajout des loyers nets au cash-flow)
                if asset == "SCPI":
                    loyers_scpi = patrimoine[asset] * rendement
                    impot_scpi = loyers_scpi * (marginal_tax_rate / 100 + 0.172)  # TMI + prélèvements sociaux
                    net_loyers_scpi = loyers_scpi - impot_scpi
                    cash_for_investment += net_loyers_scpi
                    historique.loc[year, 'Loyers SCPI'] = loyers_scpi
                    historique.loc[year, 'Impôt SCPI'] = impot_scpi
                else:
                    patrimoine[asset] *= (1 + rendement)
        
        # Mise à jour de la valeur de l'immobilier
        if immo_purchase_done:
            patrimoine['Immobilier (Bien)'] *= (1 + immo_params['immo_reval_rate'] / 100)

        # Calcul de l'épargne annuelle et du cash-flow immobilier
        annual_savings = monthly_investment * 12
        net_immo_cash_flow = 0
        if immo_purchase_done:
            loyer_annuel = target_immo_price * (immo_params['rendement_locatif_brut'] / 100)
            interets = loan_crd * (loan_params['rate'] / 100)
            charges_deductibles = (loyer_annuel * immo_params['charges_pct'] / 100) + interets
            revenu_imposable = loyer_annuel - charges_deductibles
            impot_locatif = max(0, revenu_imposable) * (marginal_tax_rate / 100 + 0.172)
            
            remb_capital = min(loan_crd, annuite_pret - interets)
            paiement_annuel_pret = interets + remb_capital
            
            loan_crd = max(0, loan_crd - remb_capital)
            net_immo_cash_flow = loyer_annuel - paiement_annuel_pret - (loyer_annuel * immo_params['charges_pct'] / 100) - impot_locatif
            
            # Mise à jour des KPIs pour l'immobilier
            kpi_trackers.update({
                'total_rent_received': kpi_trackers['total_rent_received'] + loyer_annuel, 
                'total_interest_paid': kpi_trackers['total_interest_paid'] + interets, 
                'total_rental_tax': kpi_trackers['total_rental_tax'] + impot_locatif
            })
            
            # Mise à jour de l'historique pour l'immobilier
            historique.loc[year, 'Remboursement Annuel Prêt'] = paiement_annuel_pret
            historique.loc[year, 'Loyers Bruts'] = loyer_annuel
            historique.loc[year, "Intérêts d'Emprunt"] = interets
            historique.loc[year, 'Impôt Locatif'] = impot_locatif
            historique.loc[year, 'Cash-Flow Net Immo'] = net_immo_cash_flow
            historique.loc[year, 'Soutien Épargne Immo'] = max(0, -net_immo_cash_flow)
        
        # Ajout du cash-flow annuel au cash disponible pour l'investissement
        cash_for_investment += annual_savings + net_immo_cash_flow
        cash_flow_history.append(cash_for_investment)

        # --- Logique d'investissement annuel (simplifiée) ---
        per_contribution_this_year = 0
        if cash_for_investment > 0:
            # L'optimiseur est maintenant responsable de s'assurer que l'allocation respecte les contraintes (ex: plafond PER).
            # La simulation applique simplement les poids d'allocation fournis.
            for asset, weight in allocation.items():
                flow_amount = cash_for_investment * weight
                if asset == 'PER':
                    per_contribution_this_year = flow_amount
                
                frais_entree = df_options_financiers.loc[asset, 'Frais Entrée (%)'] / 100
                patrimoine[asset] += flow_amount * (1 - frais_entree)
                if f"Flux {asset}" in historique.columns:
                    historique.loc[year, f"Flux {asset}"] = flow_amount

        # Réinvestissement des économies fiscales liées au PER
        tax_saving = per_contribution_this_year * (marginal_tax_rate / 100)
        if tax_saving > 0:
            kpi_trackers['total_tax_saving_per'] += tax_saving
            reinvested_tax_saving = 0
            for asset, weight in allocation.items():
                reinvestment_amount = tax_saving * weight
                patrimoine[asset] += reinvestment_amount * (1 - (df_options_financiers.loc[asset, 'Frais Entrée (%)'] / 100))
                if f"Flux {asset}" in historique.columns:
                    historique.loc[year, f"Flux {asset}"] += reinvestment_amount
                reinvested_tax_saving += reinvestment_amount
            if tax_saving > reinvested_tax_saving:
                kpi_trackers['leaked_cash'] += (tax_saving - reinvested_tax_saving)

        # Mise à jour de l'historique pour l'année en cours
        for col in patrimoine: 
            historique.loc[year, col] = patrimoine.get(col, 0)
        historique.loc[year, 'Dette Immobilière'] = -loan_crd
        historique.loc[year, 'Total Net'] = sum(patrimoine.values()) - loan_crd

    # Calcul du patrimoine net final
    final_net_worth = historique['Total Net'].iloc[-1]
    return final_net_worth, patrimoine, loan_crd, historique, event_logs, kpi_trackers, cash_flow_history