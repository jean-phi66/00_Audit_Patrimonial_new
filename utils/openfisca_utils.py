# utils/openfisca_utils.py

from datetime import date

try:
    from openfisca_france import FranceTaxBenefitSystem
    from openfisca_core.simulation_builder import SimulationBuilder
    OPENFISCA_READY = True
except ImportError:
    OPENFISCA_READY = False

def analyser_fiscalite_foyer(annee, parents, enfants, revenus_annuels, revenu_foncier_net=0, est_parent_isole=False):
    """
    Analyse complète de la fiscalité d'un foyer pour une année donnée avec OpenFisca.
    Prend en compte la garde alternée.
    """
    if not OPENFISCA_READY:
        # Fallback simple si OpenFisca n'est pas disponible
        total_revenus = sum(revenus_annuels.values()) + revenu_foncier_net
        return {
            'ir_net': total_revenus * 0.15, 'ps_foncier': revenu_foncier_net * 0.172,
            'tmi': 15.0, 'taux_imposition_global': 15.0, 'parts_fiscales': 1.0,
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
        'personnes_a_charge': all_children_names,
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
    menage = {'menage1': {'personne_de_reference': declarants[0]}}
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
    taux_imposition_global = ((ir_net + ps_foncier) / total_revenus_bruts * 100) if total_revenus_bruts > 0 else 0
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
        'revenu_net_imposable': 0,#results_openfisca.get('revenu_net_imposable', 0),
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