import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import date

import sys
import os

# Add project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.fiscal_logic import get_revenus_imposables

try:
    from utils.openfisca_utils import analyser_optimisation_per, add_bracket_lines_to_fig
    OPENFISCA_UTILITY_AVAILABLE = True
except ImportError as e:
    OPENFISCA_UTILITY_AVAILABLE = False
    st.session_state.openfisca_import_error = str(e)

def format_space_thousand_sep(num, trailing=" €"):
    """Formats a number with spaces as thousand separators."""
    return '{:,}'.format(np.round(num, 0)).replace(',', ' ') + trailing

def create_base_tax_evolution_fig(results):
    """Crée la figure de base de l'évolution de l'impôt avec les tranches."""
    fig = px.line(results['df_income_tax_evol'], x='Revenu', y='IR', labels={'Revenu': 'Revenu net imposable', 'IR': "Montant de l'IR"})
    add_bracket_lines_to_fig(fig, results['df_income_tax_evol'], results['bareme_annee_simulation'])
    fig.update_layout(xaxis_ticksuffix='€', yaxis_ticksuffix='€', xaxis_range=[0, results['length_simu']])
    return fig

def display_one_shot_tab(results, salary):
    """Affiche l'onglet 'Synthèse de l'impôt'."""
    st.subheader("Synthèse de votre impôt actuel")
    df_one_shot = results['df_one_shot']
    if df_one_shot.empty:
        st.error("Impossible de calculer l'impôt pour le revenu spécifié. Essayez d'augmenter le revenu max pour les graphiques.")
        return

    IR_one_shot = df_one_shot['IR'].values[0]
    avantage_qf = df_one_shot['Reduction QF'].values[0]
    IR_ss_qf = df_one_shot['IR sans QF'].values[0]
    TMI = df_one_shot['TMI'].values[0]
    taux_moyen = df_one_shot['Taux moyen d imposition'].values[0]
    decote = df_one_shot['Decote'].values[0]

    col1, col2, col3 = st.columns(3)
    col1.metric("Revenu net imposable", format_space_thousand_sep(salary))
    col2.metric("Nombre de parts", f"{results['nb_part_one_shot']:.2f}")
    col3.metric("Impôt sur le revenu", format_space_thousand_sep(IR_one_shot))
    
    if IR_ss_qf > 0:
        col1.metric("Effet du quotient familial", format_space_thousand_sep(avantage_qf), f"{np.round(avantage_qf / IR_ss_qf * 100, 1)} %", delta_color='inverse')
    else:
        col1.metric("Effet du quotient familial", format_space_thousand_sep(avantage_qf))

    col2.metric("Tranche Marginale d'Imposition", f"{np.round(TMI * 100, 0):.0f} %")
    col3.metric("Taux moyen d'imposition", f"{np.round(taux_moyen * 100, 1)} %")
    if decote > 0:
        ir_avant_decote = IR_one_shot + decote
        col1.metric("Gain de la décote", format_space_thousand_sep(decote), f"{np.round(decote / max(1, ir_avant_decote) * 100, 1)} %", delta_color='inverse')

    st.divider()
    st.subheader("Évolution de l'impôt selon le revenu")
    fig = create_base_tax_evolution_fig(results)
    fig.add_scatter(x=[salary], y=[IR_one_shot], text=format_space_thousand_sep(IR_one_shot), marker=dict(color='red', size=10), name='Votre situation')
    st.plotly_chart(fig, use_container_width=True)

def display_per_optim_tab(results, salary, ir_residuel_min):
    """Affiche l'onglet 'Versement Optimal PER'."""
    df_one_shot = results['df_one_shot']
    if df_one_shot.empty:
        st.error("Impossible de calculer l'impôt pour le revenu spécifié. Les calculs PER ne peuvent être effectués.")
        return

    IR_one_shot = df_one_shot['IR'].values[0]
    versement_optimal = results['versement_optimal_PER']
    impot_final = results['impot_avec_versement']
    versement_tmi = results['versement_PER_TMI']

    st.subheader("Optimisation du versement PER")
    col1, col2, col3 = st.columns(3)
    col1.metric("Versement PER optimal", format_space_thousand_sep(versement_optimal), help="Versement maximisant la baisse d'impôt, tout en respectant votre plafond PER et l'IR résiduel minimum.")
    col2.metric("Impôt après versement", format_space_thousand_sep(impot_final))
    
    economie = IR_one_shot - impot_final
    if versement_optimal > 0:
        col3.metric("Économie d'impôt", format_space_thousand_sep(economie), f"{np.round(economie / versement_optimal * 100, 1)} % du versement")
    else:
        col3.metric("Économie d'impôt", format_space_thousand_sep(economie))

    if versement_tmi > 0 and versement_tmi <= results.get('plafond_per_input', versement_tmi):
        st.info(f"Un versement de **{format_space_thousand_sep(versement_tmi)}** est suffisant pour changer de Tranche Marginale d'Imposition (TMI).", icon="💡")

    st.divider()
    st.subheader("Visualisation de l'optimisation")
    fig = create_base_tax_evolution_fig(results)
    fig.add_scatter(x=[salary], y=[IR_one_shot], text=format_space_thousand_sep(IR_one_shot), marker=dict(color='red', size=10), name='IR initial')
    
    if not results['df_income_tax_evol'].empty and versement_optimal > 0:
        # Trouve le point sur la courbe d'impôt originale qui correspond à l'impôt après versement PER
        equivalent_row = results['df_income_tax_evol'].iloc[(results['df_income_tax_evol']['IR'] - impot_final).abs().argmin()]
        fig.add_scatter(x=[equivalent_row['Revenu']], y=[equivalent_row['IR']], text=format_space_thousand_sep(impot_final), marker=dict(color='green', size=10), name='IR après versement')
    
    if ir_residuel_min > 0:
        fig.add_hline(
            y=ir_residuel_min,
            line_dash="dot",
            line_color="tomato",
            line_width=2,
            annotation_text=f"IR Résiduel Min: {format_space_thousand_sep(ir_residuel_min)}",
            annotation_position="bottom right"
        )
    
    fig.update_layout(title="Impact du versement PER optimal sur la courbe d'imposition")
    st.plotly_chart(fig, use_container_width=True)

def display_per_effect_tab(results, salary, plafond_PER, ir_residuel_min):
    """Affiche l'onglet 'Effet Versement PER'."""
    df_one_shot = results['df_one_shot']
    df_per = results['df_income_tax_PER']
    if df_one_shot.empty or df_per.empty:
        st.info("Les données de simulation PER ne sont pas disponibles.")
        return

    IR_one_shot = df_one_shot['IR'].values[0]
    versement_input = st.slider("Montant du versement PER", 0, int(plafond_PER), 0, 100)
    
    row_selected = df_per.iloc[(df_per['Versement_PER'] - versement_input).abs().argmin()]
    ir_versement = row_selected['IR']
    economie = IR_one_shot - ir_versement
    effort = versement_input - economie

    st.subheader("Impact de votre versement")
    col1, col2, col3 = st.columns(3)
    col1.metric("Impôt après versement", format_space_thousand_sep(ir_versement))
    col2.metric("Économie d'impôt", format_space_thousand_sep(economie))
    col3.metric("Effort d'épargne réel", format_space_thousand_sep(effort), help="Versement moins l'économie d'impôt.")

    # --- Ajout du graphique d'impact sur la courbe d'imposition ---
    st.subheader("Impact du versement sur la courbe d'imposition")
    fig_impact = create_base_tax_evolution_fig(results)
    
    # Point de départ
    fig_impact.add_scatter(x=[salary], y=[IR_one_shot], text=format_space_thousand_sep(IR_one_shot), marker=dict(color='red', size=10), name='IR initial')
    
    # Point d'arrivée après versement
    if not results['df_income_tax_evol'].empty and versement_input > 0:
        equivalent_row = results['df_income_tax_evol'].iloc[(results['df_income_tax_evol']['IR'] - ir_versement).abs().argmin()]
        fig_impact.add_scatter(x=[equivalent_row['Revenu']], y=[equivalent_row['IR']], text=format_space_thousand_sep(ir_versement), marker=dict(color='green', size=10), name='IR après versement')
    
    if ir_residuel_min > 0:
        fig_impact.add_hline(
            y=ir_residuel_min,
            line_dash="dot",
            line_color="tomato",
            line_width=2,
            annotation_text=f"IR Résiduel Min: {format_space_thousand_sep(ir_residuel_min)}",
            annotation_position="bottom right"
        )
    
    fig_impact.update_layout(title="Impact du versement PER sur la courbe d'imposition")
    st.plotly_chart(fig_impact, use_container_width=True)

    st.divider()
    st.subheader("Analyse de l'économie d'impôt")
    df_per_filtered = df_per[df_per['Versement_PER'] <= plafond_PER].copy()
    df_per_filtered["Economie_IR"] = IR_one_shot - df_per_filtered['IR']
    
    fig_eco = px.line(df_per_filtered, x='Versement_PER', y='Economie_IR', labels={'Versement_PER': 'Versement PER', 'Economie_IR': "Économie d'impôt"})
    fig_eco.add_scatter(x=[versement_input], y=[economie], text=format_space_thousand_sep(economie), marker=dict(color='green', size=10), name='Votre sélection', showlegend=False)
    fig_eco.update_layout(title="Économie d'impôt en fonction du versement PER", xaxis_ticksuffix='€', yaxis_ticksuffix='€')
    st.plotly_chart(fig_eco, use_container_width=True)

# --- Logique principale de la page ---

st.title("💡 Optimisation PER")
st.markdown("Simulez l'impact d'un versement sur un Plan d'Épargne Retraite (PER) sur votre impôt sur le revenu et déterminez le montant optimal.")

if not OPENFISCA_UTILITY_AVAILABLE:
    error_msg = st.session_state.get('openfisca_import_error', "Erreur inconnue.")
    st.error(f"**Le module OpenFisca n'a pas pu être chargé.** L'analyse ne peut pas être effectuée.\n\n**Erreur technique :** `{error_msg}`")
    st.stop()

if 'parents' not in st.session_state or not st.session_state.parents:
    st.warning("⚠️ Veuillez d'abord renseigner les informations du foyer dans la page **1_Famille**.")
    st.stop()

parents = st.session_state.get('parents', [])
enfants = st.session_state.get('enfants', [])

# Vérification des revenus sans lancer le calcul complet
total_salary_check = sum(r.get('montant', 0) for r in st.session_state.get('revenus', []) if r.get('type') == 'Salaire')

if total_salary_check == 0:
    st.warning("⚠️ Veuillez renseigner les salaires dans la page **4_Flux** pour lancer l'analyse.")
    st.stop()

st.sidebar.header("Paramètres de l'optimisation PER")
is_single_parent_auto = len(parents) == 1 and len(enfants) > 0
if is_single_parent_auto:
    est_parent_isole = st.sidebar.checkbox("Cocher la case T (Parent isolé)", value=is_single_parent_auto, key="per_isole")
else:
    est_parent_isole = False

# Récupération des paramètres sauvegardés s'ils existent
per_params = st.session_state.get('per_input_parameters', {})

input_plafond_PER = st.sidebar.number_input(
    "Votre Plafond PER disponible (€)", 
    value=per_params.get('plafond_per', 10000), 
    step=100, 
    min_value=0
)
input_ir_residuel_min = st.sidebar.number_input(
    "IR résiduel minimum souhaité (€)", 
    value=per_params.get('ir_residuel_min', 0), 
    step=100, 
    min_value=0, 
    help="L'optimisation ne cherchera pas à faire baisser l'impôt en dessous de ce montant."
)

run_simulation = st.sidebar.button("🚀 Lancer la simulation PER", use_container_width=True, type="primary")

with st.sidebar.expander("Options", expanded=False):
    annee_simulation = st.number_input(
        "Année d'imposition", 
        min_value=2020, 
        max_value=date.today().year, 
        value=per_params.get('annee_simulation', date.today().year), 
        key="per_annee"
    )
    # On calcule les revenus ici pour les valeurs par défaut des inputs
    revenus_salaires, revenu_foncier_net = get_revenus_imposables(annee_simulation)
    total_salary = sum(revenus_salaires.values())
    input_revenu_max_simu = st.number_input(
        "Revenu max. pour les graphiques (€)", 
        value=per_params.get('revenu_max_simu', max(150000, int(total_salary * 1.2))), 
        step=1000, 
        min_value=int(total_salary if total_salary > 0 else 1)
    )

# Sauvegarde des paramètres d'entrée dans le session_state
st.session_state.per_input_parameters = {
    'plafond_per': input_plafond_PER,
    'ir_residuel_min': input_ir_residuel_min,
    'annee_simulation': annee_simulation,
    'revenu_max_simu': input_revenu_max_simu
}

if run_simulation:
    with st.spinner("Calculs d'optimisation en cours avec OpenFisca..."):
        try:
            # On recalcule les revenus avec l'année de simulation au cas où elle aurait changé
            revenus_salaires, revenu_foncier_net = get_revenus_imposables(annee_simulation)
            results = analyser_optimisation_per(annee=annee_simulation, parents=parents, enfants=enfants, revenus_annuels=revenus_salaires, revenu_foncier_net=revenu_foncier_net, est_parent_isole=est_parent_isole, plafond_per=input_plafond_PER, ir_residuel_min=input_ir_residuel_min, revenu_max_simu=input_revenu_max_simu)
            st.session_state.per_simulation_results = results
            st.session_state.per_simulation_results['plafond_per_input'] = input_plafond_PER
            st.session_state.per_simulation_results['total_salary_input'] = total_salary
        except Exception as e:
            import traceback
            st.error(f"Une erreur est survenue lors de la simulation : {e}")
            st.session_state.per_simulation_results = {
                "error": str(e),
                "traceback": traceback.format_exc(),
                "simulation_inputs": {
                    "annee": annee_simulation,
                    "parents": parents,
                    "enfants": enfants,
                    "revenus_annuels": revenus_salaires,
                    "revenu_foncier_net": revenu_foncier_net,
                    "est_parent_isole": est_parent_isole,
                    "plafond_per": input_plafond_PER,
                    "ir_residuel_min": input_ir_residuel_min,
                    "revenu_max_simu": input_revenu_max_simu
                }
            }

if 'per_simulation_results' in st.session_state:
    results = st.session_state.per_simulation_results

    if "error" not in results:
        salary = results['total_salary_input']
        plafond_per = results['plafond_per_input']
        tab_one_shot, tab_per_optim, tab_per_effect = st.tabs(["Synthèse de l'impôt", "Versement Optimal PER", "Effet d'un versement"])
        with tab_one_shot:
            display_one_shot_tab(results, salary)
        with tab_per_optim:
            display_per_optim_tab(results, salary, input_ir_residuel_min)
        with tab_per_effect:
            display_per_effect_tab(results, salary, plafond_per, input_ir_residuel_min)

    # Le bloc de débogage est maintenant en dehors de la condition de succès
    # et est développé par défaut en cas d'erreur.
    with st.expander("Voir les données de débogage", expanded=("error" in results)):
        if "error" in results:
            st.subheader("Erreur et Données d'Entrée")
            st.write("La simulation a échoué. Voici les données d'entrée qui ont été utilisées :")
            st.json(results.get("simulation_inputs"))
            st.subheader("Traceback de l'erreur")
            st.text(results.get("traceback"))
        else:
            st.subheader("Données envoyées à OpenFisca")
            st.json({
                "Données pour la simulation (courbe d'impôt vs Revenu)": results.get("simulation_input_income"),
                "Données pour la simulation (courbe d'impôt vs Versement PER)": results.get("simulation_input_per")
            })