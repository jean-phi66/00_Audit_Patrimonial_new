import streamlit as st
import plotly.graph_objects as go
from core.patrimoine_logic import (
    calculate_gross_yield,
    calculate_net_yield_charges,
    calculate_property_tax,
    calculate_net_yield_tax,
    calculate_savings_effort,
    find_associated_loan,
    calculate_loan_annual_breakdown
)

def calculate_property_metrics(asset, passifs, tmi, social_tax):
    """Calcule toutes les métriques de performance pour un bien immobilier."""
    metrics = {}
    
    # 1. Trouver le prêt associé
    loan = find_associated_loan(asset.get('id'), passifs)
    metrics['loan_found'] = loan is not None

    # 2. Calculer les différentes rentabilités
    metrics['gross_yield'] = calculate_gross_yield(asset)
    metrics['net_yield_charges'] = calculate_net_yield_charges(asset)
    
    # 3. Calculer l'impôt et la rentabilité nette de fiscalité
    tax_info = calculate_property_tax(asset, loan, tmi, social_tax)
    metrics['tax_info'] = tax_info
    metrics['net_yield_after_tax'] = calculate_net_yield_tax(asset, tax_info['total'])

    # 4. Calculer l'effort d'épargne mensuel (cash-flow)
    savings_effort = calculate_savings_effort(asset, loan, tax_info['total'])
    metrics['savings_effort'] = savings_effort
    metrics['cash_flow_annuel'] = savings_effort * 12

    # 5. Calculs pour le graphique en cascade et les indicateurs clés
    loan_breakdown = calculate_loan_annual_breakdown(loan)
    metrics['capital_rembourse_annuel'] = loan_breakdown.get('capital', 0)
    metrics['interets_annuels'] = loan_breakdown.get('interest', 0)

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

def display_property_analysis(asset, metrics):
    """Affiche les métriques de rentabilité pré-calculées pour un bien immobilier."""
    
    with st.expander(f"Analyse de : {asset.get('libelle', 'Sans nom')}", expanded=True):
        # --- Affichage des métriques principales ---
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Rentabilité Brute",
                value=f"{metrics['gross_yield']:.2f} %",
                help="Loyers annuels / Prix d'achat"
            )
        with col2:
            st.metric(
                label="Rentabilité Nette de charges",
                value=f"{metrics['net_yield_charges']:.2f} %",
                help="(Loyers - Charges - Taxe Foncière) / Prix d'achat"
            )
        with col3:
            st.metric(
                label="Rentabilité Nette de fiscalité",
                value=f"{metrics['net_yield_after_tax']:.2f} %",
                help="Rentabilité nette après déduction de l'impôt sur les revenus fonciers et des prélèvements sociaux."
            )
        with col4:
            st.metric(
                label="Effort d'épargne mensuel",
                value=f"{metrics['savings_effort']:,.2f} €",
                delta=f"{metrics['savings_effort']:,.2f}",
                delta_color="inverse",
                help="Flux de trésorerie mensuel après paiement des charges, de la taxe foncière, du crédit et des impôts. Un nombre négatif représente l'effort d'épargne à réaliser."
            )
        
        # --- Graphique en cascade ---
        st.markdown("---")
        
        fig = go.Figure(go.Waterfall(
            name = "Cash-flow", 
            orientation = "v",
            measure = [
                "absolute", "relative", "relative", "total", # -> Loyers Nets de Charges
                "relative", "total",                         # -> Revenus Fonciers Nets
                "relative", "relative", "relative", "total", # -> Résultat Net (avant capital)
                "relative", "total"                          # -> Cash-flow Net Annuel
            ],
            x = [
                "Loyers Bruts", "Charges", "Taxe Foncière", 
                "Loyers Nets de Charges",
                "Intérêts d'emprunt",
                "Revenus Fonciers Nets",
                "Impôt (IR)", "Prélèv. Sociaux",
                "Réduction d'impôt (Pinel)",
                "Résultat Net (avant capital)",
                "Capital Remboursé",
                "Cash-flow Net Annuel"
            ],
            textposition = "outside",
            text = [
                f"{metrics['loyers_annuels']:,.0f} €", f"{-metrics['charges_annuelles']:,.0f} €", f"{-metrics['taxe_fonciere']:,.0f} €",
                f"{metrics['loyers_nets_de_charges']:,.0f}",
                f"{-metrics['interets_annuels']:,.0f} €",
                f"{metrics['revenus_fonciers_nets']:,.0f}",
                f"{-metrics['tax_info']['ir']:,.0f} €", f"{-metrics['tax_info']['ps']:,.0f} €",
                f"+{metrics['reduction_pinel']:,.0f} €" if metrics['reduction_pinel'] > 0 else "0 €",
                f"{metrics['resultat_avant_remboursement_capital']:,.0f}",
                f"{-metrics['capital_rembourse_annuel']:,.0f} €",
                f"{metrics['cash_flow_annuel']:,.0f}"
            ],
            y = [
                metrics['loyers_annuels'], -metrics['charges_annuelles'], -metrics['taxe_fonciere'], 
                None, # Total: Loyers Nets de Charges
                -metrics['interets_annuels'],
                None, # Total: Revenus Fonciers Nets
                -metrics['tax_info']['ir'], -metrics['tax_info']['ps'], metrics['reduction_pinel'],
                None, # Total: Résultat Net (avant capital)
                -metrics['capital_rembourse_annuel'],
                None # Total final
            ],
            connector = {"line":{"color":"rgb(63, 63, 63)"}},
        ))

        fig.update_layout(
                title="Décomposition du Cash-flow Annuel",
                showlegend=False,
                yaxis_title="Montant (€)"
        )
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

def main():
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
        st.stop()

    # --- Paramètres de simulation ---
    st.sidebar.header("Hypothèses de calcul")
    tmi = st.sidebar.select_slider(
        "Votre Taux Marginal d'Imposition (TMI)",
        options=[0, 11, 30, 41, 45],
        value=30,
        help="Le TMI est le taux d'imposition qui s'applique à la dernière tranche de vos revenus. Il est essentiel pour calculer l'impôt sur les revenus fonciers."
    )
    social_tax = 17.2 # Taux des prélèvements sociaux
    st.sidebar.info(f"Les prélèvements sociaux sont fixés à **{social_tax}%**.")

    st.markdown("---")

    # --- Affichage par bien ---
    passifs = st.session_state.get('passifs', [])
    for asset in productive_assets:
        # Vérifier que les données nécessaires sont présentes
        if asset.get('loyers_mensuels') is not None:
            metrics = calculate_property_metrics(asset, passifs, tmi, social_tax)
            display_property_analysis(asset, metrics)
        else:
            st.warning(f"Les données de loyers pour **{asset.get('libelle')}** ne sont pas renseignées dans la page Patrimoine.")

if __name__ == "__main__":
    main()