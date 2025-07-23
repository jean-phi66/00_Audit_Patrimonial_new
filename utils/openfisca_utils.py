# utils/openfisca_utils.py

from datetime import date
import pandas as pd
import numpy as np
import plotly.graph_objects as go

try:
    from openfisca_france import FranceTaxBenefitSystem
    from openfisca_core.simulation_builder import SimulationBuilder
    OPENFISCA_READY = True
except ImportError:
    OPENFISCA_READY = False

def analyser_fiscalite_foyer(annee, parents, enfants, revenus_annuels, revenu_foncier_net=0, est_parent_isole=False):
    """
    Analyse complète de la fiscalité d'un foyer pour une année donnée avec OpenFisca.
    """
    if not OPENFISCA_READY:
        # Fallback simple si OpenFisca n'est pas disponible
        total_revenus = sum(revenus_annuels.values()) + revenu_foncier_net
        return {
            'ir_net': total_revenus * 0.15, 'ps_foncier': revenu_foncier_net * 0.172,
            'tmi': 15.0, 'taux_imposition_global': 15.0, 'parts_fiscales': len(parents) + len(enfants) * 0.5,
            'ir_sans_quotient': total_revenus * 0.15, 'gain_quotient': 0,
            'revenu_brut_global': total_revenus, 'revenu_net_imposable': total_revenus * 0.9,
            'simulation_data': {'error': 'OpenFisca not available'}
        }

    tax_benefit_system = FranceTaxBenefitSystem()
    
    # --- 1. Séparation des enfants en fonction de la garde alternée ---
    enfants_a_charge_plein = [e for e in enfants if not e.get('garde_alternee')]
    enfants_en_garde_alternee = [e for e in enfants if e.get('garde_alternee')]

    # --- 2. Construction des entités OpenFisca ---
    individus = {}
    declarants = []
    all_children_names = []

    # Parents
    for i, parent in enumerate(parents):
        prenom = parent.get('prenom', f'parent_{i+1}')
        dob = parent.get('date_naissance')
        date_naissance_formatee = dob.strftime('%Y-%m-%d') if dob else date(1980, 1, 1).strftime('%Y-%m-%d')
        revenu_parent = revenus_annuels.get(prenom, 0)
        
        individus[prenom] = {
            'salaire_imposable': {str(annee): revenu_parent},
            'date_naissance': {'ETERNITY': date_naissance_formatee}
        }
        declarants.append(prenom)

    # Enfants (tous les enfants sont des individus)
    for i, enfant in enumerate(enfants):
        prenom = enfant.get('prenom', f'enfant_{i+1}')
        dob = enfant.get('date_naissance')
        date_naissance_formatee = dob.strftime('%Y-%m-%d') if dob else date(2010, 1, 1).strftime('%Y-%m-%d')
        
        individus[prenom] = {
            'date_naissance': {'ETERNITY': date_naissance_formatee}
        }
        all_children_names.append(prenom)

    # Foyer Fiscal
    foyer_fiscal = {'foyerfiscal1': {
        'declarants': declarants,
        # nb_pac: Nombre d'enfants à charge exclusive
        'nb_pac': {str(annee): len(enfants_a_charge_plein)},
        # nbH: Nombre d'enfants en garde alternée
        'nbH': {str(annee): len(enfants_en_garde_alternee)},
    }}

    if revenu_foncier_net > 0:
        foyer_fiscal['foyerfiscal1']['revenu_categoriel_foncier'] = {str(annee): revenu_foncier_net}

    if est_parent_isole:
        foyer_fiscal['foyerfiscal1']['caseT'] = {str(annee): True}

    # Famille et Ménage (nécessaire pour certaines variables)
    famille = {'famille1': {'parents': declarants, 'enfants': all_children_names}}
    menage = {'menage1': {'personne_de_reference': [declarants[0]]}}
    if len(declarants) > 1:
        menage['menage1']['conjoint'] = declarants[1:]

    CASE = {'individus': individus, 'foyers_fiscaux': foyer_fiscal, 'familles': famille, 'menages': menage}

    # --- 3. Simulation ---
    sb = SimulationBuilder()
    simulation = sb.build_from_entities(tax_benefit_system, CASE)
    
    annee_str = str(annee)
    variables_to_calc = ['ip_net', 'ir_taux_marginal', 'nbptr', 'ir_ss_qf', 'avantage_qf']#, 'revenu_brut_global', 'revenu_net_imposable']
    results_openfisca = {var: simulation.calculate(var, annee_str)[0] for var in variables_to_calc}

    # --- 4. Formatage des résultats ---
    ir_net = results_openfisca.get('ip_net', 0)
    ps_foncier = revenu_foncier_net * 0.172
    total_revenus_bruts = sum(revenus_annuels.values()) + revenu_foncier_net
    taux_imposition_global = ((ir_net + ps_foncier) / max(1, total_revenus_bruts) * 100)
    gain_quotient = -results_openfisca.get('avantage_qf', 0)

    return {
        'ir_net': ir_net,
        'ps_foncier': ps_foncier,
        'tmi': results_openfisca.get('ir_taux_marginal', 0) * 100,
        'taux_imposition_global': taux_imposition_global,
        'parts_fiscales': results_openfisca.get('nbptr', 0),
        'ir_sans_quotient': results_openfisca.get('ir_ss_qf', 0),
        'gain_quotient': gain_quotient,
        'revenu_brut_global': 0, #results_openfisca.get('revenu_brut_global', 0),
        'revenu_net_imposable': 0, #results_openfisca.get('revenu_net_imposable', 0),
        'simulation_data': CASE
    }

def calculer_impot_openfisca(annee, parents, enfants, revenus_annuels, revenu_foncier_net=0, est_parent_isole=False):
    """
    Calcule l'impôt sur le revenu net pour une année donnée.
    Wrapper simple autour de `analyser_fiscalite_foyer` pour la rétro-compatibilité.
    """
    try:
        resultats = analyser_fiscalite_foyer(
            annee=annee, parents=parents, enfants=enfants,
            revenus_annuels=revenus_annuels, revenu_foncier_net=revenu_foncier_net,
            est_parent_isole=est_parent_isole
        )
        return resultats.get('ir_net', 0)
    except Exception as e:
        print(f"Erreur dans calculer_impot_openfisca: {e}")
        return 0

def add_bracket_lines_to_fig(fig, df_simulation, bareme_annee_simulation):
    """
    Ajoute des lignes verticales au graphique aux points où la tranche de TMI change.
    """
    tmi_bracket_changes = df_simulation['ir_tranche'].diff().ne(0)
    change_points = df_simulation[tmi_bracket_changes]

    for _, row in change_points.iterrows():
        bracket_index = int(row['ir_tranche'])
        rbg_threshold = row['Revenu']
        if bracket_index > 0 and bareme_annee_simulation:
            official_rate = bareme_annee_simulation.rates[bracket_index]
            fig.add_vline(x=rbg_threshold, line_width=1, line_dash="dash", line_color="grey", annotation_text=f"TMI {int(official_rate*100)}%", annotation_position="top right", annotation_font_size=10)
    return fig

def simuler_evolution_fiscalite(annee, parents, enfants, revenu_foncier_net=0, est_parent_isole=False, revenu_max_simu=150000, step=1000):
    """
    Simule l'évolution de l'impôt sur le revenu en fonction du revenu du travail.
    """
    if not OPENFISCA_READY:
        return pd.DataFrame(), None

    tax_benefit_system = FranceTaxBenefitSystem()
    
    # --- 1. Construction des entités (similaire à analyser_fiscalite_foyer) ---
    enfants_a_charge_plein = [e for e in enfants if not e.get('garde_alternee')]
    enfants_en_garde_alternee = [e for e in enfants if e.get('garde_alternee')]

    individus = {}
    declarants = []
    all_children_names = []

    for i, parent in enumerate(parents):
        prenom = parent.get('prenom', f'parent_{i+1}')
        dob = parent.get('date_naissance')
        date_naissance_formatee = dob.strftime('%Y-%m-%d') if dob else date(1980, 1, 1).strftime('%Y-%m-%d')
        individus[prenom] = {'date_naissance': {'ETERNITY': date_naissance_formatee}}
        declarants.append(prenom)

    for i, enfant in enumerate(enfants):
        prenom = enfant.get('prenom', f'enfant_{i+1}')
        dob = enfant.get('date_naissance')
        date_naissance_formatee = dob.strftime('%Y-%m-%d') if dob else date(2010, 1, 1).strftime('%Y-%m-%d')
        individus[prenom] = {'date_naissance': {'ETERNITY': date_naissance_formatee}}
        all_children_names.append(prenom)

    foyer_fiscal = {'foyerfiscal1': {
        'declarants': declarants,
        'nb_pac': {str(annee): len(enfants_a_charge_plein)},
        'nbH': {str(annee): len(enfants_en_garde_alternee)},
    }}
    if revenu_foncier_net > 0:
        foyer_fiscal['foyerfiscal1']['revenu_categoriel_foncier'] = {str(annee): revenu_foncier_net}
    if est_parent_isole:
        foyer_fiscal['foyerfiscal1']['caseT'] = {str(annee): True}

    famille = {'famille1': {'parents': declarants, 'enfants': all_children_names}}
    menage = {'menage1': {'personne_de_reference': [declarants[0]]}}
    if len(declarants) > 1:
        menage['menage1']['conjoint'] = declarants[1:]

    # --- 2. Définition de l'axe de simulation ---
    axis_count = int(revenu_max_simu / step) if step > 0 else 1
    
    CASE = {
        'individus': individus, 'foyers_fiscaux': foyer_fiscal, 'familles': famille, 'menages': menage,
        'axes': [[{'count': axis_count, 'name': 'salaire_imposable', 'min': 0, 'max': revenu_max_simu, 'period': str(annee)}]]
    }

    # --- 3. Simulation ---
    sb = SimulationBuilder()
    simulation = sb.build_from_entities(tax_benefit_system, CASE)
    
    annee_str = str(annee)
    #n_reshape = len(declarants) + len(all_children_names)
    n_reshape_out = 1 + len(all_children_names)
    n_reshape = 1

    # L'axe s'applique à chaque individu. On somme les revenus des déclarants.
    n_reshape_salary = int(simulation.calculate_add('salaire_imposable', annee_str).shape[0] / axis_count)
    salaire_foyer = simulation.calculate_add('salaire_imposable', annee_str).reshape(axis_count, n_reshape_salary)[:, :len(declarants)].sum(axis=1)

    # Les variables du foyer sont diffusées à tous les individus. On prend la première valeur.    
    n_reshape_loc = int(simulation.calculate_add('ip_net', annee_str).shape[0] / axis_count)

    ir_net_evol = simulation.calculate('ip_net', annee_str).reshape(axis_count, n_reshape_loc)[:, 0]
    ir_tranche_evol = simulation.calculate('ir_tranche', annee_str).reshape(axis_count, n_reshape_loc)[:, 0]

    df_evolution = pd.DataFrame({
        'Revenu': salaire_foyer,
        'IR': ir_net_evol,
        'ir_tranche': ir_tranche_evol
    })
    
    try:
        bareme = tax_benefit_system.parameters.impot_revenu.bareme_ir_depuis_1945.bareme(annee_str)
    except:
        bareme = None
    
    return df_evolution, bareme

def _calculate_optimal_per_payment(df_per, df_one_shot, plafond_per, ir_residuel_min):
    """Calcule le versement PER optimal en fonction du changement de TMI et de l'IR résiduel."""
    if df_one_shot.empty or df_per.empty:
        return 0., df_one_shot['IR'].values[0] if not df_one_shot.empty else 0., 0.

    current_tmi_bracket = int(df_one_shot['ir_tranche'].values[0])
    ir_initial = df_one_shot['IR'].values[0]

    # 1. Trouver le versement minimal pour changer de TMI
    lower_brackets = df_per['ir_tranche'][df_per['ir_tranche'] < current_tmi_bracket]
    versement_tmi_opt = 0.
    if not lower_brackets.empty:
        target_bracket = lower_brackets.max()
        df_target_bracket = df_per[df_per['ir_tranche'] == target_bracket]
        if not df_target_bracket.empty:
            versement_tmi_opt = df_target_bracket['Versement_PER'].iloc[0]

    # 2. Trouver le versement optimal qui respecte l'IR résiduel
    candidates = df_per[df_per['IR'] >= ir_residuel_min]
    
    if not candidates.empty:
        # On cherche le plus grand versement possible qui respecte la contrainte
        optimal_row = candidates.iloc[-1]
        versement_optimal = optimal_row['Versement_PER']
        impot_final = optimal_row['IR']
    else:
        # Aucun versement ne respecte la contrainte, donc pas de versement
        versement_optimal = 0.
        impot_final = ir_initial

    # 3. Le versement final est plafonné par le plafond de l'utilisateur
    versement_final = min(versement_optimal, plafond_per)
    
    # Recalculer l'impôt final si le versement a été plafonné
    if versement_final < versement_optimal and not df_per.empty:
        capped_row = df_per.iloc[(df_per['Versement_PER'] - versement_final).abs().argmin()]
        impot_final = capped_row['IR']

    return versement_final, impot_final, versement_tmi_opt

def analyser_optimisation_per(annee, parents, enfants, revenus_annuels, revenu_foncier_net, est_parent_isole, plafond_per, ir_residuel_min, revenu_max_simu, step=100):
    """
    Analyse complète de l'optimisation PER pour un foyer.
    """
    if not OPENFISCA_READY:
        return {'error': 'OpenFisca not available'}

    tax_benefit_system = FranceTaxBenefitSystem()
    annee_str = str(annee)

    # --- 1. Création des entités de base ---
    enfants_a_charge_plein = [e for e in enfants if not e.get('garde_alternee')]
    enfants_en_garde_alternee = [e for e in enfants if e.get('garde_alternee')]
    individus, declarants, all_children_names = {}, [], []

    for i, p in enumerate(parents):
        prenom = p.get('prenom', f'parent_{i+1}')
        dob = p.get('date_naissance')
        date_naissance_formatee = dob.strftime('%Y-%m-%d') if dob else date(1980, 1, 1).strftime('%Y-%m-%d')
        individus[prenom] = {'date_naissance': {'ETERNITY': date_naissance_formatee}}
        declarants.append(prenom)

    for i, e in enumerate(enfants):
        prenom = e.get('prenom', f'enfant_{i+1}')
        dob = e.get('date_naissance')
        date_naissance_formatee = dob.strftime('%Y-%m-%d') if dob else date(2010, 1, 1).strftime('%Y-%m-%d')
        individus[prenom] = {'date_naissance': {'ETERNITY': date_naissance_formatee}}
        all_children_names.append(prenom)

    foyer_fiscal = {'foyerfiscal1': {
        'declarants': declarants,
        'nb_pac': {annee_str: len(enfants_a_charge_plein)}, 'nbH': {annee_str: len(enfants_en_garde_alternee)},
    }}
    if revenu_foncier_net > 0: foyer_fiscal['foyerfiscal1']['revenu_categoriel_foncier'] = {annee_str: revenu_foncier_net}
    if est_parent_isole: foyer_fiscal['foyerfiscal1']['caseT'] = {annee_str: True}
    
    famille = {'famille1': {'parents': declarants, 'enfants': all_children_names}}
    menage = {'menage1': {'personne_de_reference': [declarants[0]]}}
    if len(declarants) > 1: menage['menage1']['conjoint'] = declarants[1:]

    base_case = {'individus': individus, 'foyers_fiscaux': foyer_fiscal, 'familles': famille, 'menages': menage}
    n_individus = len(declarants) + len(all_children_names)

    # --- 2. Simulation de l'évolution de l'IR en fonction du revenu ---
    axis_count_income = int(revenu_max_simu / step) if step > 0 else 1
    case_income_sim = base_case.copy()
    case_income_sim['axes'] = [[{'count': axis_count_income, 'name': 'salaire_imposable', 'min': 0, 'max': revenu_max_simu, 'period': annee_str}]]
    
    sb_income = SimulationBuilder()
    sim_income = sb_income.build_from_entities(tax_benefit_system, case_income_sim)
    
    salaire_foyer = sim_income.calculate_add('salaire_imposable', annee_str).reshape(axis_count_income, n_individus)[:, :len(declarants)].sum(axis=1)
    vars_to_calc = ['ip_net', 'ir_taux_marginal', 'ir_tranche', 'ir_ss_qf', 'avantage_qf', 'decote_gain_fiscal', 'taux_moyen_imposition']
    results_income = {var: sim_income.calculate(var, annee_str).reshape(axis_count_income, 
                                                                        int(sim_income.calculate(var, annee_str).shape[0]/axis_count_income))[:, 0] for var in vars_to_calc}

    df_income_evol = pd.DataFrame({
        'Revenu': salaire_foyer, 'IR': results_income['ip_net'], 'TMI': results_income['ir_taux_marginal'],
        'ir_tranche': results_income['ir_tranche'], 'IR sans QF': results_income['ir_ss_qf'],
        'Reduction QF': -results_income['avantage_qf'], 'Decote': results_income['decote_gain_fiscal'],
        'Taux moyen d imposition': results_income['taux_moyen_imposition']
    })
    df_income_evol['Revenu'] = df_income_evol['Revenu'].apply(lambda x: int(np.round(x, -2)))

    # --- 3. Simulation de l'effet du versement PER ---
    total_salary = sum(revenus_annuels.values())
    case_per_sim = base_case.copy()
    # Assigner les salaires réels pour cette simulation
    for prenom, revenu in revenus_annuels.items():
        case_per_sim['individus'][prenom]['salaire_imposable'] = {annee_str: revenu}

    axis_count_per = int(total_salary / step) if step > 0 else 1
    if axis_count_per > 0:
        case_per_sim['axes'] = [[{'count': axis_count_per, 'name': 'f6rs', 'min': 0, 'max': total_salary, 'period': annee_str}]]
        print(case_per_sim)
        
        sb_per = SimulationBuilder()
        sim_per = sb_per.build_from_entities(tax_benefit_system, case_per_sim)
        versement_per_axis = sim_per.calculate_add('f6rs', annee_str).reshape(axis_count_per, n_individus)[:, :len(declarants)].sum(axis=1)
        ir_per_evol = sim_per.calculate('ip_net', annee_str).reshape(axis_count_per, 1 + len(all_children_names))[:, 0]
        ir_tranche_per_evol = sim_per.calculate('ir_tranche', annee_str).reshape(axis_count_per, 1 + len(all_children_names))[:, 0]
        df_per_evol = pd.DataFrame({'Versement_PER': versement_per_axis, 'IR': ir_per_evol, 'ir_tranche': ir_tranche_per_evol})
    else:
        df_per_evol = pd.DataFrame(columns=['Versement_PER', 'IR', 'ir_tranche'])

    # --- 4. Calculs finaux ---
    df_one_shot = df_income_evol[df_income_evol['Revenu'] == int(np.round(total_salary, -2))].head(1)
    versement_optimal, impot_final, versement_tmi = _calculate_optimal_per_payment(df_per_evol, df_one_shot, plafond_per, ir_residuel_min)
    
    try:
        bareme = tax_benefit_system.parameters.impot_revenu.bareme_ir_depuis_1945.bareme(annee_str)
        nb_parts = analyser_fiscalite_foyer(annee, parents, enfants, revenus_annuels, revenu_foncier_net, est_parent_isole)['parts_fiscales']
    except:
        bareme, nb_parts = None, len(parents)

    return {
        "df_income_tax_evol": df_income_evol,
        "df_income_tax_PER": df_per_evol,
        "df_one_shot": df_one_shot,
        "nb_part_one_shot": nb_parts,
        "bareme_annee_simulation": bareme,
        "versement_optimal_PER": versement_optimal,
        "impot_avec_versement": impot_final,
        "versement_PER_TMI": versement_tmi,
        "length_simu": revenu_max_simu,
        "simulation_input_income": case_income_sim,
        "simulation_input_per": case_per_sim,
    }