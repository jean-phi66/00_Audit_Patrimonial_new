# Fichier: ui_components.py (version mise à jour pour être contextuelle)
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy_financial as npf # Gardez cet import s'il est utilisé directement dans ce fichier
from .simulation import run_unified_simulation, calculate_monthly_payment # MODIFIÉ: Import relatif

# <<< MODIFIÉ : La fonction accepte maintenant un argument pour savoir sur quelle page on est
def setup_sidebar(page_name="optimisation"): 
    """
    Configure et affiche la barre latérale de l'application Streamlit.
    """
    st.sidebar.title("👨‍💼 Vos Paramètres")
    st.sidebar.header("Situation Initiale")
    initial_capital = st.sidebar.number_input("Capital de départ (€)", 0, value=20000, step=1000)
    monthly_investment = st.sidebar.number_input("Épargne mensuelle (€)", 0, value=500, step=50)
    investment_horizon = st.sidebar.slider("Horizon de temps (années)", 5, 40, 20, 1)

    st.sidebar.header("Fiscalité")
    marginal_tax_rate = st.sidebar.selectbox("Taux Marginal d'Imposition (TMI) (%)", options=[0, 11, 30, 41, 45], index=2)
    per_deduction_limit = st.sidebar.number_input("Plafond Annuel PER (€)", 0, value=4399, step=100)

    st.sidebar.header("Sélection des Investissements")
    df_options_financiers = pd.DataFrame(
        {'Actif': [True, True],
         'Rendement Annuel (%)': [3.5, 4.0],
         'Frais Entrée (%)': [1.0, 2.0],
         'Frais Gestion Annuels (%)': [0.6, 0.8]},
        index=["Assurance-Vie", "PER"]
    ) 
    # Filtrer les actifs financiers actifs
    df_options_financiers_edited = st.sidebar.data_editor(
        df_options_financiers,
        column_config={"Actif": st.column_config.CheckboxColumn("Activer ?", default=True)}
    )
    active_financial_assets = df_options_financiers_edited[df_options_financiers_edited['Actif']].index.tolist()

    # Ajout de débogage pour vérifier les actifs financiers actifs
    st.write("Débogage : Actifs financiers actifs")
    st.write(f"Actifs sélectionnés : {active_financial_assets}")

    # Initialisation des allocations manuelles pour éviter les erreurs de clé manquante
    manual_allocations_initial = {asset: 0 for asset in df_options_financiers_edited.index}
    manual_allocations_monthly = {asset: 0 for asset in df_options_financiers_edited.index}

    include_immo = False

    return {

        "initial_capital": initial_capital,
        "monthly_investment": monthly_investment,
        "investment_horizon": investment_horizon,
        "marginal_tax_rate": marginal_tax_rate,
        "per_deduction_limit": per_deduction_limit,
        "df_options_financiers_edited": df_options_financiers_edited,
        "include_immo": include_immo,
        "manual_allocations_initial": manual_allocations_initial,  # Ajout des allocations initiales
        "manual_allocations_monthly": manual_allocations_monthly  # Ajout des allocations mensuelles
    }


# Le reste du fichier (display_results, etc.) ne change pas.
def display_results(opt_result, simulation_args):
    st.subheader("📊 Résultat de la Stratégie")
    with st.expander("Voir le journal de l'optimiseur", expanded=not opt_result.success):
        st.text(f"Message de l'optimiseur : {opt_result.message}")
        st.text(f"Convergence réussie : {opt_result.success}")
    if not opt_result.success:
        st.error("L'optimisation n'a pas pu converger.")
        if simulation_args[5] is not None and 'x' in opt_result and len(opt_result.x) > 0:
             st.subheader("🕵️ Diagnostic de l'Échec")
             last_immo_price = opt_result.x[-1]
             loan_amount = last_immo_price
             loan_params = simulation_args[6]
             calculated_payment = calculate_monthly_payment(loan_amount, loan_params['rate'], loan_params['duration'])
             st.warning(f"La mensualité calculée ({calculated_payment:,.0f} €) pour le dernier bien testé à {last_immo_price:,.0f} € dépasse probablement votre maximum autorisé de {loan_params['mensualite_max']:,.0f} €.")
        return
    optimal_vars = opt_result.x
    _, final_patrimoine, final_crd, historique, event_logs, kpis, _ = run_unified_simulation(optimal_vars, *simulation_args)
    final_net_worth = historique['Total Net'].iloc[-1]
    st.success(f"**Patrimoine Net Final Estimé : {final_net_worth:,.0f} €**")
    display_kpis(historique, final_net_worth, kpis, simulation_args[1], simulation_args[2])
    display_allocations_and_charts(final_patrimoine, final_crd, historique, event_logs, kpis, optimal_vars, simulation_args)

def display_kpis(historique, final_net_worth, kpis, initial_capital, monthly_investment):
    st.subheader("Indicateurs Clés de Performance (KPIs)")
    flow_cols = [col for col in historique.columns if 'Flux' in col]
    total_flux_invested = historique[flow_cols].sum().sum()
    total_invested = initial_capital + total_flux_invested
    if kpis.get('leaked_cash', 0) > 0:
        st.warning(f"**Flux non investi :** {kpis['leaked_cash']:,.0f} € n'ont pas pu être investis.")
    investment_horizon = len(historique) - 1
    cash_flows = [-initial_capital] + [-monthly_investment * 12] * investment_horizon
    cash_flows[-1] += final_net_worth
    irr = npf.irr(cash_flows) if total_invested > 0 else 0
    col1, col2, col3 = st.columns(3)
    col1.metric("Plus-Value Nette Totale", f"{final_net_worth - total_invested:,.0f} €")
    col2.metric("Total des Versements", f"{total_invested:,.0f} €")
    col3.metric("Rendement Annuel Moyen (TRI)", f"{irr:.2%}")

# Définition d'une palette de couleurs pour les actifs dans ce module
# pour assurer la cohérence avec le reste de l'application.
COULEURS_ACTIFS_OPTIM = {
    # Pour le Pie Chart (df_final_comp.index)
    "Assurance-Vie": "#ff9933",  # Variation d'orange (Financier)
    "PER": "#ffad5c",          # Variation d'orange (Financier)
    "SCPI": "#ffc085",         # Variation d'orange (Financier)
    "Immobilier (Patrimoine Net)": "#636EFA", # Couleur pour l'immobilier productif/simulé
    "Immobilier (Bien)": "#636EFA", # Couleur pour l'immobilier productif/simulé (nom original)

    # Pour l'Area Chart (colonnes de df_plot, ex: 'Asset_Net')
    "Assurance-Vie_Net": "#ff9933",
    "PER_Net": "#ffad5c",
    "SCPI_Net": "#ffc085",
    "Immobilier (Bien)_Net": "#636EFA",

    # Fallbacks génériques (moins susceptibles d'être utilisés si les noms spécifiques sont présents)
    "Financier": "#ff7f0e",
    "Immobilier Productif": "#636EFA",
    "Immobilier de Jouissance": "#1f77b4", # Moins pertinent pour l'optimisation, mais pour la complétude
}

def display_allocations_and_charts(final_patrimoine, final_crd, historique, event_logs, kpis, optimal_vars, simulation_args):
    """Affiche les détails de l'allocation, les bilans et les graphiques."""
    asset_names, initial_capital, monthly_investment, _, _, include_immo, loan_params, _, _ = simulation_args

    # Vérification adaptée pour la différenciation entre allocations initiales et mensuelles
    num_assets = len(asset_names)
    if len(optimal_vars) != num_assets * 2 and len(optimal_vars) != num_assets * 2 + 1:
        st.error("Erreur : Le nombre d'actifs financiers actifs ne correspond pas aux allocations définies (initiales et mensuelles).")
        st.stop()

    # Séparation des allocations initiales et mensuelles
    alloc_initial = optimal_vars[:num_assets]
    alloc_monthly = optimal_vars[num_assets:num_assets * 2]

    # Vérification des allocations initiales et mensuelles
    if len(alloc_initial) != num_assets or len(alloc_monthly) != num_assets:
        st.error("Erreur : Les allocations initiales ou mensuelles ne correspondent pas au nombre d'actifs financiers actifs.")
        st.stop()

    st.subheader("Détails de la Stratégie Optimale")
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if len(alloc_initial) > 0:
            # Allocation initiale
            df_alloc_initial = pd.DataFrame({'Poids': alloc_initial}, index=asset_names)
            df_alloc_initial['Montant'] = df_alloc_initial['Poids'] * initial_capital
            st.write("**Répartition du Capital de Départ**")
            st.dataframe(df_alloc_initial[df_alloc_initial['Poids'] > 0.001].sort_values('Poids', ascending=False).style.format({'Poids': '{:.1%}', 'Montant': '{:,.0f} €'}))
            
            # Allocation mensuelle
            df_alloc_monthly = pd.DataFrame({'Poids': alloc_monthly}, index=asset_names)
            df_alloc_monthly['Montant Mensuel'] = df_alloc_monthly['Poids'] * monthly_investment
            st.write("**Allocation de l'Épargne Mensuelle**")
            st.dataframe(df_alloc_monthly[df_alloc_monthly['Poids'] > 0.001].sort_values('Poids', ascending=False).style.format({'Poids': '{:.1%}', 'Montant Mensuel': '{:,.0f} €'}))
        else:
            st.write("**Allocation d'actifs financiers**")
            st.info("Aucun actif financier sélectionné.")

    # Vérification explicite que loan_params n'est pas None
    if include_immo and loan_params:
        with col2:
            st.write("**Bilan du Projet Immobilier**")
            optimal_immo_price = optimal_vars[-1]
            final_mensualite = calculate_monthly_payment(optimal_immo_price, loan_params['rate'], loan_params['duration'])
            st.metric(label="Prix d'achat du bien visé", value=f"{optimal_immo_price:,.0f} €", help=f"Mensualité de prêt associée : {final_mensualite:,.0f} €/mois")
            st.text(f"Total Loyers Perçus : {kpis.get('total_rent_received', 0):,.0f} €")
            st.text(f"Total Intérêts Payés : {kpis.get('total_interest_paid', 0):,.0f} €")
            st.text(f"Total Impôts Locatifs : {kpis.get('total_rental_tax', 0):,.0f} €")
    
    if kpis.get('total_tax_saving_per', 0) > 0:
        st.info(f"💰 **Gain fiscal total grâce au PER : {kpis['total_tax_saving_per']:,.0f} €** (réinvesti)")
    
    if event_logs:
        st.write("**Journal des Événements Clés**")
        for log in event_logs:
            st.info(f"{log}")

    st.subheader("Analyse Visuelle de la Stratégie")
    net_assets = {k: v for k, v in final_patrimoine.items() if v > 1}
    if 'Immobilier (Bien)' in net_assets and net_assets['Immobilier (Bien)'] > 0:
        net_assets['Immobilier (Patrimoine Net)'] = net_assets.pop('Immobilier (Bien)') - final_crd
    
    df_final_comp = pd.DataFrame(net_assets.values(), index=net_assets.keys(), columns=['Valeur'])
    if not df_final_comp.empty:
        fig_pie = px.pie(df_final_comp, 
                         values='Valeur', 
                         names=df_final_comp.index, 
                         title="Composition du Patrimoine Net Final", 
                         hole=0.3,
                         color=df_final_comp.index, # S'assurer que Plotly utilise les noms pour mapper les couleurs
                         color_discrete_map=COULEURS_ACTIFS_OPTIM)
        st.plotly_chart(fig_pie, use_container_width=True)
    
    df_plot = historique.drop(columns=[col for col in historique.columns if 'Flux' in col or 'Dette' in col or 'Total' in col or 'Soutien' in col])
    df_plot = df_plot.loc[:, (df_plot.abs().sum() > 0)]
    if not df_plot.empty:
        fig_area = px.area(
            df_plot,
            x=df_plot.index,
            y=df_plot.columns,
            title="Évolution de la Composition du Patrimoine Brut",
            labels={'index': 'Année', 'value': 'Valeur (€)', 'variable': 'Actif'},
            color_discrete_map=COULEURS_ACTIFS_OPTIM
        )
        st.plotly_chart(fig_area, use_container_width=True)

    st.subheader("Tableau de Bord Annuel")
    st.dataframe(
        historique.style.format(
            formatter="{:,.0f} €",
            subset=pd.IndexSlice[:, [col for col in historique.columns if 'Flux' not in col and 'Soutien' not in col]]
        )
    )

    # Déplacement des affichages de débogage dans un expander
    with st.expander("🔍 Débogage : Détails des Données", expanded=False):
        st.write("Débogage : Vérification des données d'entrée")
        st.write(f"Actifs financiers actifs : {asset_names}")
        st.write(f"Variables d'optimisation : {optimal_vars}")
        st.write(f"Inclusion d'un projet immobilier : {include_immo}")
        st.write("Débogage : Allocations séparées")
        st.write(f"Allocations initiales : {alloc_initial}")
        st.write(f"Allocations mensuelles : {alloc_monthly}")