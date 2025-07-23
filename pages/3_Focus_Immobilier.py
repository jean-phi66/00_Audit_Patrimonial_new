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

def calculate_property_metrics(asset, passifs, tmi, social_tax, year_of_analysis):
    """Calcule toutes les métriques de performance pour un bien immobilier."""
    metrics = {}
    
    # 1. Trouver le prêt associé
    loans = find_associated_loans(asset.get('id'), passifs)
    metrics['loan_found'] = bool(loans)

    # 2. Calculer les différentes rentabilités
    metrics['gross_yield'] = calculate_gross_yield(asset)
    metrics['net_yield_charges'] = calculate_net_yield_charges(asset)
    metrics['amortissement_annuel_potentiel'] = 0

    # Calcul de l'amortissement si LMNP
    if asset.get('mode_exploitation') == 'Location Meublée':
        amortissement_info = calculate_lmnp_amortissement_annuel(asset)
        metrics['amortissement_annuel_potentiel'] = amortissement_info['total']
    
    # 3. Calculer l'impôt et la rentabilité nette de fiscalité
    tax_info = calculate_property_tax(asset, loans, tmi, social_tax, amortissement_annuel_utilise=metrics['amortissement_annuel_potentiel'], year=year_of_analysis)
    metrics['tax_info'] = tax_info
    metrics['net_yield_after_tax'] = calculate_net_yield_tax(asset, tax_info['total'])

    # 4. Calculer l'effort d'épargne mensuel (cash-flow)
    savings_effort = calculate_savings_effort(asset, loans, tax_info['total'], year=year_of_analysis)
    metrics['savings_effort'] = savings_effort
    metrics['cash_flow_annuel'] = savings_effort * 12

    # 5. Calculs pour le graphique en cascade et les indicateurs clés
    metrics['capital_rembourse_annuel'] = sum(calculate_loan_annual_breakdown(l, year=year_of_analysis).get('capital', 0) for l in loans)
    metrics['interets_annuels'] = sum(calculate_loan_annual_breakdown(l, year=year_of_analysis).get('interest', 0) for l in loans)

    metrics['loyers_annuels'] = asset.get('loyers_mensuels', 0) * 12
    metrics['charges_annuelles'] = asset.get('charges', 0) * 12
    metrics['taxe_fonciere'] = asset.get('taxe_fonciere', 0)
    
    metrics['loyers_nets_de_charges'] = metrics['loyers_annuels'] - metrics['charges_annuelles'] - metrics['taxe_fonciere']
    metrics['revenus_fonciers_nets'] = metrics['loyers_nets_de_charges'] - metrics['interets_annuels']
    metrics['reduction_pinel'] = tax_info.get('reduction_pinel', 0)
    
    metrics['resultat_avant_remboursement_capital'] = metrics['revenus_fonciers_nets'] - tax_info['ir'] - tax_info['ps'] + metrics['reduction_pinel']

    # 6. Calcul de l'effet de levier
    if metrics['cash_flow_annuel'] >= 0:
        metrics['leverage_display'] = "∞ (Autofinancé)"
        metrics['leverage_help_text'] = "Le bien s'autofinance (cash-flow positif ou nul), l'effet de levier est donc maximal."
    elif metrics['capital_rembourse_annuel'] > 0:
        effort_epargne_annuel = -metrics['cash_flow_annuel']
        leverage_value = metrics['capital_rembourse_annuel'] / effort_epargne_annuel
        metrics['leverage_display'] = f"{leverage_value:.2f}"
        metrics['leverage_help_text'] = f"Pour chaque euro d'effort d'épargne que vous investissez, vous créez {leverage_value:.2f} € de patrimoine (capital remboursé)."
    else:
        metrics['leverage_display'] = "N/A"
        metrics['leverage_help_text'] = "Le calcul de l'effet de levier n'est pas applicable (pas de capital remboursé ou effort d'épargne nul)."

    return metrics

def _create_waterfall_fig(metrics, year_of_analysis, is_lmnp=False):
    """Crée le graphique en cascade pour une location nue ou meublée."""
    # Définir le libellé final en fonction du résultat pour plus de clarté
    final_label = "Cash-flow Net Annuel"
    if metrics['cash_flow_annuel'] < 0:
        final_label = "Effort d'Épargne Annuel"

    # Base commune du graphique
    revenus_nets_label = "Revenus LMNP nets" if is_lmnp else "Revenus Fonciers Nets"
    base_x = ["Loyers Bruts", "Charges", "Taxe Foncière", "Loyers Nets de Charges", "Intérêts d'emprunt", revenus_nets_label]
    base_y = [
        metrics['loyers_annuels'], -metrics['charges_annuelles'], -metrics['taxe_fonciere'], 
        None,  # Total: Loyers Nets de Charges
        -metrics['interets_annuels'],
        None   # Total: Revenus Fonciers Nets
    ]
    base_text = [
        f"{metrics['loyers_annuels']:,.0f} €", f"{-metrics['charges_annuelles']:,.0f} €", f"{-metrics['taxe_fonciere']:,.0f} €",
        f"{metrics['loyers_nets_de_charges']:,.0f} €",
        f"{-metrics['interets_annuels']:,.0f} €",
        f"{metrics['revenus_fonciers_nets']:,.0f} €",
    ]
    base_measures = ["absolute", "relative", "relative", "total", "relative", "total"]

    if is_lmnp:
        # Cas LMNP : pas de réduction d'impôt affichée
        x_labels = base_x + ["Impôt (IR)", "Prélèv. Sociaux", "Résultat avant capital", "Remboursement du Capital", final_label]
        measures = base_measures + ["relative", "relative", "total", "relative", "total"]
        y_values = base_y + [
            -metrics['tax_info']['ir'], -metrics['tax_info']['ps'],
            None,  # Total: Résultat avant capital
            -metrics['capital_rembourse_annuel'],
            None   # Total final
        ]
        text_values = base_text + [
            f"{-metrics['tax_info']['ir']:,.0f} €", f"{-metrics['tax_info']['ps']:,.0f} €",
            f"{metrics['resultat_avant_remboursement_capital']:,.0f} €",
            f"{-metrics['capital_rembourse_annuel']:,.0f} €",
            f"{metrics['cash_flow_annuel']:,.0f} €"
        ]
    else:
        # Cas Location Nue : avec réduction d'impôt
        x_labels = base_x + ["Impôt (IR)", "Prélèv. Sociaux", "Réduction d'impôt", "Résultat avant capital", "Remboursement du Capital", final_label]
        measures = base_measures + ["relative", "relative", "relative", "total", "relative", "total"]
        y_values = base_y + [
            -metrics['tax_info']['ir'], -metrics['tax_info']['ps'], metrics['reduction_pinel'],
            None,  # Total: Résultat avant capital
            -metrics['capital_rembourse_annuel'],
            None   # Total final
        ]
        text_values = base_text + [
            f"{-metrics['tax_info']['ir']:,.0f} €", f"{-metrics['tax_info']['ps']:,.0f} €",
            f"+{metrics['reduction_pinel']:,.0f} €" if metrics['reduction_pinel'] > 0 else " ",
            f"{metrics['resultat_avant_remboursement_capital']:,.0f} €",
            f"{-metrics['capital_rembourse_annuel']:,.0f} €",
            f"{metrics['cash_flow_annuel']:,.0f} €"
        ]

    fig = go.Figure(go.Waterfall(
        name="Cash-flow",
        orientation="v",
        measure=measures,
        x=x_labels,
        y=y_values,
        textposition="outside",
        text=text_values,
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        textfont=dict(size=16),
    ))

    # Calculer les limites de l'axe Y pour assurer la visibilité des labels
    # On reconstruit la liste des totaux à partir des métriques calculées,
    # car la liste y_values contient des 'None' pour les barres de totaux, ce qui causait l'erreur.
    all_totals = [
        metrics['loyers_annuels'],
        metrics['loyers_nets_de_charges'],
        metrics['revenus_fonciers_nets'],
        metrics['resultat_avant_remboursement_capital'],
        metrics['cash_flow_annuel']
    ]

    # On filtre les éventuelles valeurs None avant de passer à max() et min() pour éviter le TypeError.
    valid_totals = [t for t in all_totals if t is not None]
    max_y = max(0, *valid_totals)
    min_y = min(0, *valid_totals)
    y_padding = (max_y - min_y) * 0.1
    if y_padding == 0:  # Cas où toutes les valeurs sont nulles
        y_padding = 1000  # Une valeur par défaut pour créer un peu d'espace

    fig.update_layout(title=f"Décomposition du Cash-flow pour l'année {year_of_analysis}", showlegend=False, yaxis_title="Montant (€)", title_font_size=18, xaxis_tickfont_size=16, yaxis_range=[min_y - y_padding, max_y + y_padding])

    return fig

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
        fig = _create_waterfall_fig(metrics, selected_year, is_lmnp=is_lmnp)
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
        
        fig = go.Figure(go.Waterfall(
            name = "Coût de possession", 
            orientation = "v",
            measure = [
                "relative", "relative", "relative", "total", # -> Coût de possession annuel
                "relative", "total"                          # -> Décaissement total
            ],
            x = [
                "Charges", "Taxe Foncière", 
                "Intérêts d'emprunt",
                "Coût de Possession Annuel",
                "Remboursement du Capital",
                "Décaissement Annuel Total"
            ],
            textposition = "outside",
            text = [
                f"{-charges_annuelles:,.0f} €", f"{-taxe_fonciere:,.0f} €",
                f"{-interets_annuels:,.0f} €",
                f"{-cout_possession_annuel:,.0f} €",
                f"{-capital_rembourse_annuel:,.0f} €",
                f"{-decaissement_total_annuel:,.0f} €"
            ],
            y = [ -charges_annuelles, -taxe_fonciere, -interets_annuels, None, -capital_rembourse_annuel, None ],
            connector = {"line":{"color":"rgb(63, 63, 63)"}},
        ))

        fig.update_layout(title=f"Décomposition du Décaissement pour l'année {selected_year}", showlegend=False, yaxis_title="Montant (€)")
        st.plotly_chart(fig, use_container_width=True)

def generate_projection_data(asset, loans, tmi_pct, social_tax_pct, projection_duration):
    """Génère les données de projection pour le cash-flow et l'effet de levier."""
    projection_data = []
    start_year = date.today().year
    reserve_amortissement_reportee = 0

    # --- Initialisation pour la logique d'amortissement LMNP ---
    is_lmnp = asset.get('mode_exploitation') == 'Location Meublée'
    stock_amortissement_restant = {'immeuble': 0, 'travaux': 0, 'meubles': 0}
    amortissement_annuel = {'immeuble': 0, 'travaux': 0, 'meubles': 0}

    if is_lmnp:
        # Durées d'amortissement
        DUREE_AMORTISSEMENT_IMMEUBLE = 30
        DUREE_AMORTISSEMENT_TRAVAUX = 15
        DUREE_AMORTISSEMENT_MEUBLES = 7

        # Bases amortissables initiales
        valeur_totale = asset.get('valeur', 0)
        valeur_foncier = asset.get('part_amortissable_foncier', 0)
        valeur_travaux = asset.get('part_travaux', 0)
        valeur_meubles = asset.get('part_meubles', 0)
        
        base_immeuble = max(0, valeur_totale - valeur_foncier - valeur_travaux - valeur_meubles)
        
        stock_amortissement_restant['immeuble'] = base_immeuble
        stock_amortissement_restant['travaux'] = valeur_travaux
        stock_amortissement_restant['meubles'] = valeur_meubles

        # Calcul des dotations annuelles
        amortissement_annuel['immeuble'] = base_immeuble / DUREE_AMORTISSEMENT_IMMEUBLE if DUREE_AMORTISSEMENT_IMMEUBLE > 0 else 0
        amortissement_annuel['travaux'] = valeur_travaux / DUREE_AMORTISSEMENT_TRAVAUX if DUREE_AMORTISSEMENT_TRAVAUX > 0 else 0
        amortissement_annuel['meubles'] = valeur_meubles / DUREE_AMORTISSEMENT_MEUBLES if DUREE_AMORTISSEMENT_MEUBLES > 0 else 0

    for year in range(start_year, start_year + projection_duration + 1):
        # --- Calculs communs ---
        capital_rembourse_annuel = sum(calculate_loan_annual_breakdown(l, year=year).get('capital', 0) for l in loans)
        amortissement_utilise_annee = 0

        # --- Logique spécifique à la location meublée (LMNP) ---
        if is_lmnp:
            # 1. Calculer l'amortissement potentiel de l'année en consommant les stocks
            amortissement_potentiel_annee = 0
            for comp in ['immeuble', 'travaux', 'meubles']:
                if stock_amortissement_restant[comp] > 0:
                    dotation = min(stock_amortissement_restant[comp], amortissement_annuel[comp])
                    amortissement_potentiel_annee += dotation
                    stock_amortissement_restant[comp] -= dotation
            
            amortissement_disponible = amortissement_potentiel_annee + reserve_amortissement_reportee

            # 2. Calculer le revenu avant amortissement pour déterminer le plafond
            loyers_annuels = asset.get('loyers_mensuels', 0) * 12
            charges_annuelles = asset.get('charges', 0) * 12
            taxe_fonciere = asset.get('taxe_fonciere', 0)
            interets_emprunt = sum(calculate_loan_annual_breakdown(l, year=year).get('interest', 0) for l in loans)
            revenu_avant_amortissement = max(0, loyers_annuels - charges_annuelles - taxe_fonciere - interets_emprunt)

            # 3. Déterminer l'amortissement réellement utilisé et la nouvelle réserve
            amortissement_utilise_annee = min(amortissement_disponible, revenu_avant_amortissement)
            reserve_amortissement_reportee = amortissement_disponible - amortissement_utilise_annee

        # --- Calcul de l'impôt pour l'année (tenant compte de l'amortissement utilisé) ---
        tax_info = calculate_property_tax(
            asset, loans, tmi_pct, social_tax_pct, year=year, 
            amortissement_annuel_utilise=amortissement_utilise_annee
        )

        # --- Calcul du cash-flow pour l'année ---
        cash_flow_mensuel = calculate_savings_effort(asset, loans, tax_info['total'], year=year)
        cash_flow_annuel = cash_flow_mensuel * 12

        # --- Calcul de l'effet de levier ---
        effort_epargne_annuel = -cash_flow_annuel
        leverage = np.nan # Par défaut, pas de levier calculable
        if effort_epargne_annuel > 0 and capital_rembourse_annuel > 0:
            leverage = capital_rembourse_annuel / effort_epargne_annuel
        
        # Ajout du stock d'amortissement restant pour le graphique
        total_stock_restant = sum(stock_amortissement_restant.values()) if is_lmnp else 0

        projection_data.append({
            'Année': year,
            'Amortissement Utilisé': amortissement_utilise_annee,
            'Réserve d\'Amortissement': reserve_amortissement_reportee,
            'Stock d\'Amortissement Potentiel': total_stock_restant,
            'Cash-flow Annuel': cash_flow_annuel,
            'Effet de Levier': leverage,
            'Capital Remboursé': capital_rembourse_annuel,
            'Effort d\'Épargne': effort_epargne_annuel
        })

    return pd.DataFrame(projection_data)

def create_cash_flow_projection_fig(df_projection):
    """Crée la figure du graphique de projection du cash-flow."""
    df_projection['Couleur Cash-flow'] = np.where(df_projection['Cash-flow Annuel'] < 0, 'Négatif', 'Positif')
    fig = px.bar(
        df_projection, x='Année', y='Cash-flow Annuel',
        color='Couleur Cash-flow', color_discrete_map={'Négatif': '#FF5733', 'Positif': '#33C7FF'},
        labels={'Cash-flow Annuel': 'Cash-flow Annuel (€)'},
        hover_data={'Effort d\'Épargne': ':,.2f €'},
        title="Évolution du Cash-flow Annuel"
    )
    fig.update_layout(showlegend=False, yaxis_title="Montant (€)")
    return fig

def create_leverage_projection_fig(df_projection):
    """Crée la figure du graphique de projection de l'effet de levier."""
    df_plot_leverage = df_projection.dropna(subset=['Effet de Levier'])
    fig = px.line(
        df_plot_leverage, x='Année', y='Effet de Levier', markers=True,
        labels={'Effet de Levier': 'Ratio de Levier'},
        hover_data={'Capital Remboursé': ':,.2f €', 'Effort d\'Épargne': ':,.2f €'},
        title="Évolution de l'Effet de Levier"
    )
    fig.update_traces(connectgaps=False)

    if not df_plot_leverage.empty:
        max_leverage = df_plot_leverage['Effet de Levier'].max()
        y_axis_max = max(max_leverage * 1.2, 2)
    else:
        y_axis_max = 5

    fig.update_layout(yaxis_title="Ratio (Capital créé / Effort d'épargne)", yaxis=dict(range=[0, y_axis_max]))
    return fig

def create_amortissement_projection_fig(df_projection):
    """Crée la figure du graphique de projection de l'amortissement."""
    # Création d'une figure avec un axe Y secondaire
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # --- Axe Y Primaire (gauche) : Utilisation de l'amortissement ---
    # Zone pour l'amortissement utilisé
    fig.add_trace(go.Scatter(
        x=df_projection['Année'], 
        y=df_projection['Amortissement Utilisé'],
        hovertemplate='Amortissement Utilisé: %{y:,.0f}€<extra></extra>',
        mode='lines',
        line=dict(width=0.5),
        stackgroup='one',
        name='Amortissement Utilisé'
    ), secondary_y=False)
    # Zone pour la réserve d'amortissement (reportable)
    fig.add_trace(go.Scatter(
        x=df_projection['Année'], 
        y=df_projection['Réserve d\'Amortissement'],
        hovertemplate='Réserve d\'Amortissement: %{y:,.0f}€<extra></extra>',
        mode='lines',
        line=dict(width=0.5),
        stackgroup='one',
        name='Réserve d\'Amortissement'
    ), secondary_y=False)

    # --- Axe Y Secondaire (droite) : Stock d'amortissement potentiel ---
    fig.add_trace(go.Scatter(
        x=df_projection['Année'],
        y=df_projection['Stock d\'Amortissement Potentiel'],
        name="Stock Amortissable Restant",
        mode='lines+markers',
        line=dict(color='black', dash='dot'),
        hovertemplate='Stock Restant: %{y:,.0f}€<extra></extra>'
    ), secondary_y=True)

    # Mise en forme du graphique
    fig.update_layout(
        title_text="Évolution de l'Amortissement et du Stock Amortissable",
        legend_title_text='Composants'
    )
    fig.update_xaxes(title_text="Année")
    fig.update_yaxes(title_text="<b>Utilisation Annuelle</b> (€)", secondary_y=False)
    fig.update_yaxes(title_text="<b>Stock Amortissable</b> (€)", secondary_y=True)
    return fig

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
