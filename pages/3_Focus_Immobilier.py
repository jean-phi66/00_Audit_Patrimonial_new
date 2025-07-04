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

def display_property_analysis(asset, passifs, tmi, social_tax):
    """Affiche les métriques de rentabilité pour un bien immobilier productif."""
    
    with st.expander(f"Analyse de : {asset.get('libelle', 'Sans nom')}", expanded=True):
        # --- Calculs ---
        # 1. Trouver le prêt associé
        loan = find_associated_loan(asset.get('id'), passifs)

        # 2. Calculer les différentes rentabilités
        gross_yield = calculate_gross_yield(asset)
        net_yield_charges = calculate_net_yield_charges(asset)
        
        # 3. Calculer l'impôt et la rentabilité nette de fiscalité
        # On suppose un régime au réel car on a le détail des charges
        tax_info = calculate_property_tax(asset, loan, tmi, social_tax)
        net_yield_after_tax = calculate_net_yield_tax(asset, tax_info['total'])

        # 4. Calculer l'effort d'épargne mensuel (cash-flow)
        savings_effort = calculate_savings_effort(asset, loan, tax_info['total'])

        # --- Affichage ---
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Rentabilité Brute",
                value=f"{gross_yield:.2f} %",
                help="Loyers annuels / Prix d'achat"
            )
        with col2:
            st.metric(
                label="Rentabilité Nette de charges",
                value=f"{net_yield_charges:.2f} %",
                help="(Loyers - Charges - Taxe Foncière) / Prix d'achat"
            )
        with col3:
            st.metric(
                label="Rentabilité Nette de fiscalité",
                value=f"{net_yield_after_tax:.2f} %",
                help="Rentabilité nette après déduction de l'impôt sur les revenus fonciers et des prélèvements sociaux."
            )
        with col4:
            st.metric(
                label="Effort d'épargne mensuel",
                value=f"{savings_effort:,.2f} €",
                delta=f"{savings_effort:,.2f}",
                delta_color="inverse",
                help="Flux de trésorerie mensuel après paiement des charges, de la taxe foncière, du crédit et des impôts. Un nombre négatif représente l'effort d'épargne à réaliser."
            )
        
        # --- Graphique en cascade ---
        st.markdown("---")
        
        # Nouveaux calculs pour le graphique
        loan_breakdown = calculate_loan_annual_breakdown(loan) # Utilise l'année en cours par défaut
        capital_rembourse_annuel = loan_breakdown['capital']
        interets_annuels = loan_breakdown['interest']

        loyers_annuels = asset.get('loyers_mensuels', 0) * 12
        charges_annuelles = asset.get('charges', 0) * 12
        taxe_fonciere = asset.get('taxe_fonciere', 0)
        loyers_nets_de_charges = loyers_annuels - charges_annuelles - taxe_fonciere
        revenus_fonciers_nets = loyers_nets_de_charges - interets_annuels
        # Nouveau total intermédiaire qui représente le résultat avant le remboursement du capital
        resultat_avant_remboursement_capital = revenus_fonciers_nets - tax_info['ir'] - tax_info['ps']
        cash_flow_annuel = savings_effort * 12

        fig = go.Figure(go.Waterfall(
            name = "Cash-flow", 
            orientation = "v",
            measure = [
                "absolute", "relative", "relative", "total", # -> Loyers Nets de Charges
                "relative", "total",                         # -> Revenus Fonciers Nets
                "relative", "relative", "total",             # -> Résultat Net (avant capital)
                "relative", "total"                          # -> Cash-flow Net Annuel
            ],
            x = [
                "Loyers Bruts", "Charges", "Taxe Foncière", 
                "Loyers Nets de Charges",
                "Intérêts d'emprunt",
                "Revenus Fonciers Nets",
                "Impôt (IR)", "Prélèv. Sociaux", 
                "Résultat Net (avant capital)",
                "Capital Remboursé",
                "Cash-flow Net Annuel"
            ],
            textposition = "outside",
            text = [
                f"{loyers_annuels:,.0f} €", f"{-charges_annuelles:,.0f} €", f"{-taxe_fonciere:,.0f} €",
                f"{loyers_nets_de_charges:,.0f}",
                f"{-interets_annuels:,.0f} €",
                f"{revenus_fonciers_nets:,.0f}",
                f"{-tax_info['ir']:,.0f} €", f"{-tax_info['ps']:,.0f} €",
                f"{resultat_avant_remboursement_capital:,.0f}",
                f"{-capital_rembourse_annuel:,.0f} €",
                f"{cash_flow_annuel:,.0f}"
            ],
            y = [
                loyers_annuels, -charges_annuelles, -taxe_fonciere, 
                None, # Total: Loyers Nets de Charges
                -interets_annuels,
                None, # Total: Revenus Fonciers Nets
                -tax_info['ir'], -tax_info['ps'],
                None, # Total: Résultat Net (avant capital)
                -capital_rembourse_annuel,
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
            display_property_analysis(asset, passifs, tmi, social_tax)
        else:
            st.warning(f"Les données de loyers pour **{asset.get('libelle')}** ne sont pas renseignées dans la page Patrimoine.")

if __name__ == "__main__":
    main()