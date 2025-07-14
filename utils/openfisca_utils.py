from openfisca_france import FranceTaxBenefitSystem
from openfisca_core.simulation_builder import SimulationBuilder
from datetime import date

def analyser_fiscalite_foyer(annee, parents, enfants, revenus_annuels, revenu_foncier_net=0, est_parent_isole=False):
    """
    Analyse complète de la fiscalité d'un foyer en utilisant OpenFisca.
    Inspiré de la structure de V2_IR_simulator.py et openfisca_utils_ref.py.
    Retourne un dictionnaire détaillé avec les principaux indicateurs fiscaux.
    """
    tax_benefit_system = FranceTaxBenefitSystem()
    period = str(annee)

    # --- 1. Préparation et validation des données ---
    def format_date(d, member_name):
        if isinstance(d, date):
            return d.strftime('%Y-%m-%d')
        # Lève une erreur claire si les données sont manquantes
        raise ValueError(f"La date de naissance pour '{member_name}' est manquante ou invalide.")

    individus = {}
    declarants = []
    personnes_a_charge = []

    # --- Traitement des parents ---
    for parent in parents:
        prenom = parent.get('prenom')
        dob = parent.get('date_naissance')

        if not prenom:
            raise ValueError(f"Prénom manquant pour un parent pour l'année {annee}.")

        date_naissance_formatee = format_date(dob, prenom)
        revenu_parent = revenus_annuels.get(prenom, 0)

        individus[prenom] = {
            'salaire_imposable': {period: revenu_parent},
            'date_naissance': {'ETERNITY': date_naissance_formatee}
        }
        declarants.append(prenom)

    # --- Traitement des enfants ---
    for enfant in enfants:
        prenom = enfant.get('prenom')
        dob = enfant.get('date_naissance')

        if not prenom:
            print(f"Warning: Prénom manquant pour un enfant pour l'année {annee}. Enfant ignoré.")
            continue

        date_naissance_formatee = format_date(dob, prenom)
        individus[prenom] = {'date_naissance': {'ETERNITY': date_naissance_formatee}}
        personnes_a_charge.append(prenom)

    # --- 2. Construction du dictionnaire de simulation ---
    if not declarants:
        raise ValueError(f"Année {annee}: Aucun déclarant trouvé. Impossible de calculer l'impôt.")

    foyer_fiscal = {'foyerfiscal1': {
        'declarants': declarants,
        'personnes_a_charge': personnes_a_charge
    }}

#    if revenu_foncier_net > 0:
#        foyer_fiscal['foyerfiscal1']['revenus_fonciers'] = {period: revenu_foncier_net}
    if revenu_foncier_net > 0:
        foyer_fiscal['foyerfiscal1']['revenu_categoriel_foncier'] = {period: revenu_foncier_net}

    if est_parent_isole:
        foyer_fiscal['foyerfiscal1']['caseT'] = {period: True}

    menage = {'menage1': {
        'personne_de_reference': [declarants[0]],
        'enfants': personnes_a_charge
    }}
    if len(declarants) > 1:
        menage['menage1']['conjoint'] = [declarants[1]]

    simulation_data = {
        'individus': individus,
        'foyers_fiscaux': foyer_fiscal,
        'familles': {'famille1': {
            'parents': declarants,
            'enfants': personnes_a_charge
        }},
        'menages': menage
    }

    # --- 3. Simulation ---
    simulation_builder = SimulationBuilder()
    simulation = simulation_builder.build_from_entities(tax_benefit_system, simulation_data)

    # --- 4. Calcul des indicateurs ---
    ir_net = simulation.calculate('ip_net', period)
    ps_foncier = revenu_foncier_net * .172#simulation.calculate('prelevements_sociaux_revenus_du_patrimoine', period)[0]
    tmi = simulation.calculate('ir_taux_marginal', period) * 100
    parts_fiscales = simulation.calculate('nbptr', period)
    revenu_brut_global = 0#simulation.calculate('revenu_brut_global', period)[0]
    revenu_net_imposable = 0#simulation.calculate('revenu_net_imposable', period)[0]
    ir_sans_quotient = simulation.calculate('ir_ss_qf', period)
    gain_quotient = -simulation.calculate('avantage_qf', period)
    #gain_quotient = max(0, ir_sans_quotient - ir_net)

    # --- 5. Calculs finaux ---
    total_revenus_bruts = sum(revenus_annuels.values()) + revenu_foncier_net
    total_imposition = ir_net + ps_foncier
    taux_imposition_global = (total_imposition / total_revenus_bruts) * 100 if total_revenus_bruts > 0 else 0

    return {
        'ir_net': float(ir_net),
        'ps_foncier': float(ps_foncier),
        'total_imposition': 0, #float(total_imposition),
        'tmi': float(tmi),
        'parts_fiscales': float(parts_fiscales),
        'ir_sans_quotient': float(ir_sans_quotient),
        'gain_quotient': float(gain_quotient),
        'revenu_brut_global': float(revenu_brut_global),
        'revenu_net_imposable': float(revenu_net_imposable),
        'taux_imposition_global': float(taux_imposition_global),
        'simulation_data': simulation_data,
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
