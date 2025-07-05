# utils/openfisca_utils.py
import streamlit as st
import pandas as pd
try:
    from openfisca_france import FranceTaxBenefitSystem
    from openfisca_core.simulation_builder import SimulationBuilder
    OPENFISCA_READY = True
except ImportError:
    OPENFISCA_READY = False

@st.cache_data
def calculer_impot_openfisca(annee, parents, enfants, revenus_annuels, revenu_foncier_net=0, est_parent_isole=False):
    """
    Calcule l'impôt sur le revenu pour une année donnée en utilisant OpenFisca-France.
    Cette fonction est adaptée à la structure de données de l'application (st.session_state).

    Args:
        annee (int): L'année de la simulation.
        parents (list): Liste de dictionnaires, un pour chaque parent (depuis st.session_state.parents).
                        Chaque dict doit contenir 'prenom' et 'date_naissance'.
        enfants (list): Liste de dictionnaires, un pour chaque enfant (depuis st.session_state.enfants).
                        Chaque dict doit contenir 'prenom' et 'date_naissance'.
        revenus_annuels (dict): Dictionnaire des revenus pour l'année, avec les prénoms comme clés.
                                Ex: {'Jean': 50000, 'Marie': 45000}
        revenu_foncier_net (float): Montant total du revenu foncier net imposable pour l'année.
        est_parent_isole (bool): True si le foyer est monoparental (pour la case T).

    Returns:
        float: Le montant de l'impôt net calculé.
    """
    total_revenus = sum(revenus_annuels.values())

    if not OPENFISCA_READY:
        st.warning(f"Année {annee}: OpenFisca non installé, utilisation d'un calcul simplifié.")
        # Utilise un taux forfaitaire simple comme fallback
        return total_revenus * 0.15

    tax_benefit_system = FranceTaxBenefitSystem()
    simulation_builder = SimulationBuilder()

    individus = {}
    declarants = []

    # --- Traitement des parents ---
    for parent in parents:
        prenom = parent.get('prenom')
        dob = parent.get('date_naissance')

        if not prenom or not dob:
            st.error(f"Données incomplètes (prénom ou date de naissance) pour un parent pour l'année {annee}. Calcul d'impôt approximatif utilisé.")
            return total_revenus * 0.15  # Fallback

        date_naissance_formatee = dob.strftime('%Y-%m-%d')
        revenu_parent = revenus_annuels.get(prenom, 0)

        individus[prenom] = {
            'salaire_imposable': {str(annee): revenu_parent},
            'date_naissance': {'ETERNITY': date_naissance_formatee}
        }

        declarants.append(prenom)

    # --- Traitement des enfants ---
    personnes_a_charge = []
    for enfant in enfants:
        prenom = enfant.get('prenom')
        dob = enfant.get('date_naissance')

        if not prenom or not dob:
            st.warning(f"Données incomplètes pour l'enfant {prenom or 'inconnu'} pour l'année {annee}. Enfant ignoré pour le calcul d'impôt.")
            continue

        date_naissance_formatee = dob.strftime('%Y-%m-%d')
        individus[prenom] = {'date_naissance': {'ETERNITY': date_naissance_formatee}}
        personnes_a_charge.append(prenom)

    # --- Construction du foyer fiscal ---
    if not declarants:
        st.warning(f"Année {annee}: Aucun déclarant trouvé. Impossible de calculer l'impôt.")
        return 0

    foyer_fiscal = {'foyerfiscal1': {
        'declarants': declarants,
        'personnes_a_charge': personnes_a_charge
    }}

    # Les revenus fonciers sont rattachés au foyer fiscal, et non à un individu.
    # On fournit directement le revenu net calculé à la variable 'revenu_categoriel_foncier'.
    if revenu_foncier_net > 0:
        foyer_fiscal['foyerfiscal1']['revenu_categoriel_foncier'] = {str(annee): revenu_foncier_net}

    if est_parent_isole:
        foyer_fiscal['foyerfiscal1']['caseT'] = {str(annee): True}

    CASE = {'individus': individus, 'foyers_fiscaux': foyer_fiscal, 'menages': {'menage1': {'personne_de_reference': declarants[0]}}}

    try:
        simulation = simulation_builder.build_from_entities(tax_benefit_system, CASE)
        resultat = simulation.calculate('ip_net', str(annee))
        return float(resultat[0]) if resultat.size > 0 else 0.0
    except Exception as e:
        st.error(f"Erreur OpenFisca pour l'année {annee}: {e}")
        st.json({'openfisca_input': CASE})
        return 0