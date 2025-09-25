import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import date
import plotly.express as px

import sys
import os
# Add project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.patrimoine_logic import (
    calculate_gross_yield,
    calculate_net_yield_charges,
    calculate_property_tax,
    calculate_net_yield_tax,
    calculate_savings_effort,
    find_associated_loans,
    calculate_loan_annual_breakdown,
    calculate_lmnp_amortissement_annuel
) 

# Import des fonctions centralisées pour les graphiques immobiliers
from core.immobilier_charts import (
    calculate_property_metrics,
    create_waterfall_fig,
    generate_projection_data,
    create_cash_flow_projection_fig,
    create_leverage_projection_fig,
    create_amortissement_projection_fig,
    create_non_productive_waterfall_fig
) 

def display_property_analysis(asset, metrics, passifs, tmi, social_tax, projection_duration, selected_year):
    """Affiche les métriques de rentabilité pré-calculées pour un bien immobilier."""

    with st.expander(f"Analyse de : {asset.get('libelle', 'Sans nom')} (Année {selected_year})", expanded=True):
        # --- Affichage des métriques principales ---
        main_cols = st.columns(5 if asset.get('mode_exploitation') == 'Location Meublée' else 4)

        with main_cols[0]:
            st.metric(
                label="Rentabilité Brute",
                value=f"{metrics['gross_yield']:.2f} %",
                help="Loyers annuels / Prix d'achat"
            )
        with main_cols[1]:
            st.metric(
                label="Rentabilité Nette de charges",
                value=f"{metrics['net_yield_charges']:.2f} %",
                help="(Loyers - Charges - Taxe Foncière) / Prix d'achat"
            )
        with main_cols[2]:
            st.metric(
                label="Rentabilité Nette de fiscalité",
                value=f"{metrics['net_yield_after_tax']:.2f} %",
                help="Rentabilité nette après déduction de l'impôt sur les revenus fonciers et des prélèvements sociaux."
            )
        
        if asset.get('mode_exploitation') == 'Location Meublée':
            with main_cols[3]:
                st.metric(
                    label="Amortissement Annuel",
                    value=f"{metrics['amortissement_annuel_potentiel']:,.0f} €",
                    help="Montant annuel de la dépréciation du bien, des travaux et des meubles, déductible des revenus locatifs."
                )
        
        with main_cols[-1]: # Toujours la dernière colonne
            st.metric(
                label="Effort d'épargne mensuel",
                value=f"{metrics['savings_effort']:,.2f} €",
                delta=f"{metrics['savings_effort']:,.2f}",
                #delta_color="inverse",
                help="Flux de trésorerie mensuel après paiement des charges, de la taxe foncière, du crédit et des impôts. Un nombre négatif représente l'effort d'épargne à réaliser."
            )
        
        # --- Graphique en cascade ---
        st.markdown("---")
        
        is_lmnp = asset.get('mode_exploitation') == 'Location Meublée'
        fig = create_waterfall_fig(metrics, selected_year, is_lmnp=is_lmnp)
        st.plotly_chart(fig, use_container_width=True)

        # --- Métriques de synthèse post-graphique ---
        if metrics.get('loan_found'):
            st.markdown("---")
            st.subheader("Indicateurs clés de l'investissement")
            
            m1, m2, m3 = st.columns(3)

            m1.metric(
                label="Cash-flow Annuel",
                value=f"{metrics['cash_flow_annuel']:,.2f} €",
                help="Trésorerie nette générée par le bien sur une année."
            )
            
            m2.metric(
                label="Capital Remboursé Annuel",
                value=f"{metrics['capital_rembourse_annuel']:,.2f} €",
                help="Part du crédit remboursée qui augmente votre patrimoine net."
            )

            m3.metric(
                label="Effet de levier du cash-flow",
                value=metrics['leverage_display'],
                help=metrics['leverage_help_text']
            )

        # --- Projections ---
        loans = find_associated_loans(asset.get('id'), passifs)
        df_projection = generate_projection_data(asset, loans, tmi, social_tax, projection_duration)
        if not df_projection.empty:
            display_projection_charts(df_projection, projection_duration)
            
            if asset.get('mode_exploitation') == 'Location Meublée':
                st.markdown("---")
                st.subheader("📊 Projections Spécifiques LMNP")
                st.info("Ce graphique montre l'évolution de votre **réserve d'amortissement**. C'est le stock d'amortissement que vous n'avez pas pu utiliser les années précédentes (car vos revenus étaient trop faibles) et que vous pouvez reporter pour réduire vos impôts futurs.")
                fig_amortissement = create_amortissement_projection_fig(df_projection)
                st.plotly_chart(fig_amortissement, use_container_width=True)

def display_non_productive_analysis(asset, passifs, selected_year):
    """Affiche l'analyse du coût de possession pour un bien de jouissance pour une année donnée."""
    with st.expander(f"Analyse de : {asset.get('libelle', 'Sans nom')} (Année {selected_year})", expanded=True):
        # 1. Trouver le prêt associé
        loans = find_associated_loans(asset.get('id'), passifs)

        # 2. Calculer les coûts annuels
        charges_annuelles = asset.get('charges', 0) * 12
        taxe_fonciere = asset.get('taxe_fonciere', 0)
        
        # Agréger les données de tous les prêts
        interets_annuels = sum(calculate_loan_annual_breakdown(l, year=selected_year).get('interest', 0) for l in loans)
        capital_rembourse_annuel = sum(calculate_loan_annual_breakdown(l, year=selected_year).get('capital', 0) for l in loans)

        cout_charges_taxes = charges_annuelles + taxe_fonciere
        cout_possession_annuel = cout_charges_taxes + interets_annuels
        decaissement_total_annuel = cout_possession_annuel + capital_rembourse_annuel

        # --- Calcul de l'effet de levier ---
        if decaissement_total_annuel > 0 and capital_rembourse_annuel > 0:
            leverage_value = capital_rembourse_annuel / decaissement_total_annuel
            leverage_display = f"{leverage_value:.2f}"
            leverage_help_text = f"Pour chaque euro décaissé pour ce bien, {leverage_value:.2f} € sont directement convertis en patrimoine (capital remboursé)."
        else:
            leverage_display = "N/A"
            leverage_help_text = "L'effet de levier n'est pas applicable (pas de décaissement ou pas de capital remboursé)."

        # --- Affichage des métriques principales ---
        col1, col2, col3, col4 = st.columns(4)
        col1.metric(
            label="Décaissement Annuel Total",
            value=f"{decaissement_total_annuel:,.0f} €",
            help="Sortie de trésorerie totale pour ce bien sur l'année (charges + taxes + mensualités de prêt)."
        )
        col2.metric(
            label="Coût de possession annuel",
            value=f"{cout_possession_annuel:,.0f} €",
            help="Coût annuel incluant les charges, la taxe foncière et les intérêts du prêt. Le remboursement du capital est un enrichissement et non un coût."
        )
        col3.metric(
            label="Enrichissement annuel",
            value=f"{capital_rembourse_annuel:,.0f} €",
            help="Part du capital de l'emprunt remboursée cette année, qui constitue un enrichissement net."
        )
        col4.metric(
            label="Effet de levier",
            value=leverage_display,
            help=leverage_help_text
        )

        # --- Graphique en cascade ---
        st.markdown("---")
        
        fig = create_non_productive_waterfall_fig(asset, passifs, selected_year)
        st.plotly_chart(fig, use_container_width=True)

def display_projection_charts(df_projection, projection_duration):
    """Affiche les graphiques de projection."""
    st.markdown("---")
    st.subheader(f"📈 Projections sur {projection_duration} ans")

    col1, col2 = st.columns(2)

    with col1:
        fig_cash_flow = create_cash_flow_projection_fig(df_projection)
        st.plotly_chart(fig_cash_flow, use_container_width=True)

    with col2:
        fig_leverage = create_leverage_projection_fig(df_projection)
        st.plotly_chart(fig_leverage, use_container_width=True)
        st.caption("L'effet de levier est calculé uniquement lorsque le cash-flow est négatif (effort d'épargne positif). Un ratio de 2 signifie que pour 1€ d'effort, 2€ de capital sont créés.")

    # --- Graphique d'amortissement pour les biens LMNP ---
    if not df_projection.empty and df_projection['Amortissement Utilisé'].sum() > 0:
        fig_amortissement = create_amortissement_projection_fig(df_projection)
        st.plotly_chart(fig_amortissement, use_container_width=True)

"""Fonction principale pour exécuter la page Focus Immobilier."""
st.title("🔎 Focus Immobilier")
st.markdown("Analysez en détail la performance de vos investissements immobiliers locatifs.")

# --- Vérification des données ---
if 'actifs' not in st.session_state or not st.session_state.actifs:
    st.warning("⚠️ Veuillez d'abord renseigner vos actifs dans la page **2_Patrimoine**.")
    st.stop()

productive_assets = [a for a in st.session_state.actifs if a.get('type') == "Immobilier productif"]

if not productive_assets:
    st.info("Vous n'avez pas d'actif de type 'Immobilier productif' à analyser.")
    #st.stop()

non_productive_assets = [a for a in st.session_state.actifs if a.get('type') == "Immobilier de jouissance"]

# --- Paramètres de simulation ---
st.sidebar.header("Hypothèses de calcul")
# Initialisation dans le session_state pour les rendre accessibles au rapport
if 'immo_tmi' not in st.session_state:
    st.session_state.immo_tmi = 30
if 'immo_projection_duration' not in st.session_state:
    st.session_state.immo_projection_duration = 10

st.session_state.immo_tmi = st.sidebar.selectbox(
    "Votre Taux Marginal d'Imposition (TMI)",
    options=[0, 11, 30, 41, 45],
    #value=st.session_state.immo_tmi,
    index=[0, 11, 30, 41, 45].index(int(st.session_state.immo_tmi)),
    help="Le TMI est le taux d'imposition qui s'applique à la dernière tranche de vos revenus."
)
social_tax = 17.2 # Taux des prélèvements sociaux
st.sidebar.info(f"Les prélèvements sociaux sont fixés à **{social_tax}%**.")

st.sidebar.markdown("---")
st.sidebar.header("Paramètres de Projection")
projection_duration = st.sidebar.number_input(
    "Durée de la projection (ans)",
    min_value=1, max_value=40, value=10, step=1
)

start_year = date.today().year
analysis_years = list(range(start_year, start_year + projection_duration + 1))
selected_year = st.sidebar.selectbox(
    "Année d'analyse pour les métriques",
    options=analysis_years,
    index=0
)

st.markdown("---")

# --- Affichage par bien ---
passifs = st.session_state.get('passifs', [])


if productive_assets:
    st.subheader("Biens Immobiliers Productifs")
    for asset in productive_assets:
        # Vérifier que les données nécessaires sont présentes
        if asset.get('loyers_mensuels') is not None:
            metrics = calculate_property_metrics(asset, passifs, st.session_state.immo_tmi, social_tax, selected_year)
            display_property_analysis(asset, metrics, passifs, st.session_state.immo_tmi, social_tax, projection_duration, selected_year)
        else:
            st.warning(f"Les données de loyers pour **{asset.get('libelle')}** ne sont pas renseignées dans la page Patrimoine.")


if non_productive_assets:
    st.markdown("---")
    st.subheader("Biens Immobiliers de Jouissance")
    st.info("Cette section affiche les biens qui ne génèrent pas de revenus locatifs, comme votre résidence principale. Le graphique ci-dessous détaille le coût de possession annuel.")
    for asset in non_productive_assets:
        display_non_productive_analysis(asset, passifs, selected_year)