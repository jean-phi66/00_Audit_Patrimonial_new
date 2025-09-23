import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Import des modules d'optimisation
try:
    from ref.optim_patrimoine.optimization import setup_and_run_optimization
    from ref.optim_patrimoine.simulation import run_unified_simulation, calculate_monthly_payment
except ImportError:
    st.error("Les modules d'optimisation ne sont pas disponibles. Vérifiez l'installation.")
    st.stop()

st.title("📊 Optimisation Patrimoniale")
st.markdown("---")

# Sidebar pour les paramètres
st.sidebar.header("⚙️ Paramètres d'optimisation")

# Paramètres de base
st.sidebar.subheader("💰 Capital et investissement")
initial_capital = st.sidebar.number_input(
    "Capital initial (€)", 
    min_value=0, 
    value=100000, 
    step=1000,
    format="%d"
)

monthly_investment = st.sidebar.number_input(
    "Investissement mensuel (€)", 
    min_value=0, 
    value=1000, 
    step=100,
    format="%d"
)

investment_horizon = st.sidebar.slider(
    "Horizon d'investissement (années)", 
    min_value=1, 
    max_value=50, 
    value=20
)

# Paramètres fiscaux
st.sidebar.subheader("🏛️ Fiscalité")
marginal_tax_rate = st.sidebar.slider(
    "Taux marginal d'imposition (%)", 
    min_value=0.0, 
    max_value=50.0, 
    value=30.0,
    step=0.5
)

per_deduction_limit = st.sidebar.number_input(
    "Plafond déduction PER (€)", 
    min_value=0, 
    value=35000, 
    step=1000,
    format="%d"
)

# Options financières
st.subheader("🏦 Options d'investissement financier")

# Création du DataFrame des options financières
default_options = {
    'Actif': [True, True],
    'Rendement Annuel (%)': [3.5, 4.0],
    'Frais Entrée (%)': [1.0, 2.0],
    'Fiscalité': ['AV', 'PER']
}

df_options = pd.DataFrame(
    default_options,
    index=["Assurance-Vie", "PER"]
)

st.markdown("**Configurez vos options d'investissement :**")
df_options_edited = st.data_editor(
    df_options,
    column_config={
        "Actif": st.column_config.CheckboxColumn("Actif"),
        "Rendement Annuel (%)": st.column_config.NumberColumn("Rendement annuel", format="%.1%"),
        "Frais Entrée (%)": st.column_config.NumberColumn("Frais d'entrée", format="%.1%"),
        "Fiscalité": st.column_config.SelectboxColumn(
            "Fiscalité",
            options=["PFU", "IR", "PER", "AV"]
        )
    },
    hide_index=False,
    use_container_width=True
)

# Bouton d'optimisation
st.markdown("---")
if st.button("🚀 Lancer l'optimisation", type="primary", use_container_width=True):
    
    # Préparation des paramètres
    params = {
        'df_options_financiers_edited': df_options_edited,
        'initial_capital': initial_capital,
        'monthly_investment': monthly_investment,
        'investment_horizon': investment_horizon,
        'marginal_tax_rate': marginal_tax_rate,
        'per_deduction_limit': per_deduction_limit,
        'include_immo': False  # L'immobilier est désactivé
    }
    
    # Lancement de l'optimisation
    with st.spinner("Optimisation en cours..."):
        try:
            # Débogage: afficher les paramètres avant l'optimisation
            st.write("DEBUG - Paramètres envoyés:")
            st.write(f"Active assets: {df_options_edited[df_options_edited['Actif']].index.tolist()}")
            
            opt_result, args = setup_and_run_optimization(params)
            
            if opt_result is not None and opt_result.success:
                st.success("✅ Optimisation réussie !")
                
                # Affichage des résultats
                st.subheader("📈 Résultats de l'optimisation")
                
                # Extraction des résultats optimaux
                optimal_vars = opt_result.x
                active_assets = df_options_edited[df_options_edited['Actif']].index.tolist()
                
                # DEBUG: Afficher les variables optimales
                st.write(f"DEBUG - Variables optimales: {optimal_vars}")
                st.write(f"DEBUG - Type: {type(optimal_vars)}")
                st.write(f"DEBUG - Longueur: {len(optimal_vars)}")
                st.write(f"DEBUG - Actifs actifs: {active_assets}")
                
                try:
                    # Simulation avec les paramètres optimaux
                    final_net_worth, _, _, _, _, kpis, _ = run_unified_simulation(optimal_vars, *args)
                    
                    total_income = kpis.get('total_rent_received', 0)
                    total_taxes = kpis.get('total_rental_tax', 0)
                    
                    # Métriques principales
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric(
                            "Patrimoine final", 
                            f"{float(final_net_worth):,.0f} €",
                            f"+{float(final_net_worth) - initial_capital:,.0f} €"
                        )
                    
                    with col2:
                        annual_return = (final_net_worth / initial_capital) ** (1/investment_horizon) - 1
                        st.metric("Rendement annuel moyen", f"{annual_return:.2%}")
                except Exception as e:
                    st.error(f"Erreur lors de la simulation finale : {str(e)}")
                    st.write(f"DEBUG - Erreur de simulation: {e}")
                    st.write(f"DEBUG - Types des variables:")
                    try:
                        final_net_worth, _, _, _, total_income, total_taxes, _ = run_unified_simulation(optimal_vars, *args)
                        st.write(f"final_net_worth: {type(final_net_worth)} = {final_net_worth}")
                        st.write(f"total_income: {type(total_income)} = {total_income}")
                        st.write(f"total_taxes: {type(total_taxes)} = {total_taxes}")
                    except:
                        pass
                    import traceback
                    st.code(traceback.format_exc())
                
                # Allocation optimale - version simplifiée pour éviter les erreurs
                st.subheader("🎯 Allocation optimale")
                
                # Affichage simple des variables optimales
                st.write("**Variables d'optimisation:**")
                for i, asset in enumerate(active_assets):
                    if i < len(optimal_vars):
                        percentage = optimal_vars[i] * 100
                        amount = optimal_vars[i] * initial_capital
                        st.write(f"- {asset}: {percentage:.1f}% ({amount:,.0f} €)")
                
            else:
                st.error("❌ L'optimisation a échoué. Vérifiez vos paramètres.")
                if opt_result is not None:
                    st.error(f"Message d'erreur : {opt_result.message}")
                    
        except Exception as e:
            st.error(f"❌ Erreur lors de l'optimisation : {str(e)}")
            st.write("**Détails de l'erreur:**")
            import traceback
            st.code(traceback.format_exc())

# Informations et aide
with st.expander("ℹ️ Aide et informations"):
    st.markdown("""
    ### Comment utiliser l'optimisateur patrimonial ?
    
    1. **Paramètres de base** : Définissez votre capital initial, investissement mensuel et horizon
    2. **Fiscalité** : Indiquez votre taux marginal d'imposition et plafond PER
    3. **Options financières** : Activez/désactivez les actifs et ajustez leurs caractéristiques
    4. **Immobilier** (optionnel) : Configurez les paramètres immobiliers et de crédit
    5. **Lancement** : Cliquez sur "Lancer l'optimisation" pour obtenir les résultats
    
    ### Types de fiscalité :
    - **PFU** : Prélèvement Forfaitaire Unique (30%)
    - **IR** : Impôt sur le Revenu (selon TMI)
    - **PER** : Plan d'Épargne Retraite (déductible)
    - **AV** : Assurance Vie (fiscalité spécifique)
    
    ### Contraintes d'optimisation :
    - Les allocations doivent sommer à 100%
    - Le cash-flow doit rester positif
    - Les mensualités immobilières ne doivent pas dépasser le maximum fixé
    """)
