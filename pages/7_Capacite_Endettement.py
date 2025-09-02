import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

import sys
import os
# Add project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.patrimoine_logic import calculate_monthly_payment

# --- Constantes de calcul ---
RENTAL_INCOME_WEIGHT = 0.70 # Pondération des revenus locatifs par les banques

# --- Fonctions de calcul ---

def calculate_weighted_income(revenus):
    """
    Calcule les revenus mensuels pondérés pour le calcul de la capacité d'endettement.
    - Salaires: 100%
    - Revenus locatifs (Patrimoine): 70%
    - Autres revenus: 0% (non pris en compte)
    """
    total_weighted_income = 0
    salaire_total = 0
    loyers_bruts = 0
    loyers_ponderes = 0

    for revenu in revenus:
        montant = revenu.get('montant', 0.0)
        if revenu.get('type') == 'Salaire':
            total_weighted_income += montant
            salaire_total += montant
        elif revenu.get('type') == 'Patrimoine':
            loyers_bruts += montant
            weighted_amount = montant * RENTAL_INCOME_WEIGHT
            total_weighted_income += weighted_amount
            loyers_ponderes += weighted_amount
    
    return {
        "total": total_weighted_income,
        "salaires": salaire_total,
        "loyers_bruts": loyers_bruts,
        "loyers_ponderes": loyers_ponderes
    }

def calculate_current_debt_service(passifs):
    """
    Calcule le total des mensualités de prêts en cours et fournit le détail.
    """
    total_debt_service = 0
    debt_details = []
    for passif in passifs:
        mensualite = calculate_monthly_payment(
            passif.get('montant_initial', 0),
            passif.get('taux_annuel', 0),
            passif.get('duree_mois', 0)
        )
        if mensualite > 0:
            debt_details.append({
                'libelle': passif.get('libelle', 'Prêt non identifié'),
                'mensualite': mensualite
            })
            total_debt_service += mensualite
    return {"total": total_debt_service, "details": debt_details}

def calculate_loan_principal(monthly_payment, annual_rate_pct, duration_months):
    """
    Calcule le capital d'un prêt à partir de la mensualité, du taux et de la durée.
    Inverse de `calculate_monthly_payment`.
    """
    if duration_months <= 0 or annual_rate_pct is None or monthly_payment <= 0:
        return 0.0

    monthly_rate = (annual_rate_pct / 100) / 12

    if monthly_rate == 0:
        return monthly_payment * duration_months

    principal = monthly_payment * (1 - (1 + monthly_rate)**-duration_months) / monthly_rate
    return principal

# --- Fonctions d'UI ---

def display_results(weighted_income, current_debt, max_debt_ratio_pct):
    """Affiche les résultats du calcul."""
    
    st.subheader("📊 Résultats")
    
    if weighted_income == 0:
        st.warning("Les revenus pondérés sont de 0. Impossible de calculer le taux d'endettement.")
        return

    # Calculs
    max_debt_service = weighted_income * (max_debt_ratio_pct / 100)
    current_debt_ratio_pct = (current_debt / weighted_income) * 100 if weighted_income > 0 else 0
    remaining_capacity = max(0, max_debt_service - current_debt)

    # Affichage des métriques
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Revenus Pondérés", f"{weighted_income:,.0f} €/mois")
    col2.metric("Charges de Prêts", f"{current_debt:,.0f} €/mois")
    col3.metric(
        "Taux d'Endettement Actuel",
        f"{current_debt_ratio_pct:.2f} %",
        delta=f"{current_debt_ratio_pct - max_debt_ratio_pct:.2f} % pts",
        delta_color="inverse"
    )
    col4.metric("Capacité d'Emprunt Restante", f"{remaining_capacity:,.0f} €/mois")

    # Jauge de visualisation
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = current_debt_ratio_pct,
        number = {'suffix': ' %'},
        title = {'text': f"Taux d'endettement (Cible: {max_debt_ratio_pct}%)"},
        delta = {'reference': max_debt_ratio_pct, 'increasing': {'color': "red"}, 'decreasing': {'color': "green"}},
        gauge = {
            'axis': {'range': [None, 50], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "darkblue"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps' : [
                {'range': [0, max_debt_ratio_pct], 'color': 'lightgreen'},
                {'range': [max_debt_ratio_pct, 50], 'color': 'lightcoral'}
            ],
            'threshold' : {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': max_debt_ratio_pct}
        }))
    fig.update_layout(height=300, margin=dict(t=50, b=50, l=50, r=50))
    st.plotly_chart(fig, use_container_width=True)

    return remaining_capacity

def display_debt_ratio_breakdown_chart(debt_details, weighted_income, max_debt_ratio_pct):
    """Affiche un graphique de la répartition du taux d'endettement par prêt."""
    st.subheader("Répartition du Taux d'Endettement par Prêt")
    
    if not debt_details:
        st.info("Aucun prêt en cours à afficher.")
        return
    
    if weighted_income == 0:
        st.warning("Revenus pondérés nuls, impossible de calculer la répartition.")
        return

    # Préparer les données pour le graphique
    chart_data = []
    total_current_debt_pct = 0
    for loan in debt_details:
        percentage = (loan['mensualite'] / weighted_income) * 100
        chart_data.append({
            'y_axis': "Taux d'endettement",
            'percentage': percentage,
            'pret': loan['libelle'],
            'mensualite': loan['mensualite'] # Ajout de la mensualité pour l'affichage
        })
        total_current_debt_pct += percentage
    
    # Ajouter la capacité restante pour atteindre la limite
    remaining_capacity_pct = max_debt_ratio_pct - total_current_debt_pct
    if remaining_capacity_pct > 0:
        total_current_debt_amount = sum(l['mensualite'] for l in debt_details)
        remaining_capacity_amount = (weighted_income * (max_debt_ratio_pct / 100)) - total_current_debt_amount
        chart_data.append({
            'y_axis': "Taux d'endettement",
            'percentage': remaining_capacity_pct,
            'pret': 'Capacité restante',
            'mensualite': remaining_capacity_amount # Ajout du montant restant
        })
    
    df_chart = pd.DataFrame(chart_data)
    
    # Créer le graphique
    fig = px.bar(
        df_chart,
        x='percentage',
        y='y_axis',
        color='pret',
        orientation='h',
        title="Composition du Taux d'Endettement Actuel",
        labels={'percentage': "Taux d'endettement (%)", 'pret': 'Prêt'},
        text='percentage', # Le texte sera défini par le template ci-dessous
        custom_data=['mensualite'], # Fournir les données de mensualité au graphique
        color_discrete_map={
            "Capacité restante": "rgba(44, 160, 44, 0.5)" # Vert clair transparent
        }
    )

    fig.update_traces(
        # Afficher le % et le montant en € (sans décimales)
        texttemplate='%{x:.2f}%<br><b>%{customdata[0]:.0f} €</b>', 
        textposition='inside',
        insidetextanchor='middle',
        textfont_size=14 # Augmentation de la taille de la police
    )
    
    # Ajouter une ligne verticale pour la limite
    fig.add_vline(
        x=max_debt_ratio_pct, 
        line_width=2, 
        line_dash="dash", 
        line_color="red",
        annotation_text=f"Limite {max_debt_ratio_pct}%",
        annotation_position="bottom right"
    )

    fig.update_layout(
        barmode='stack',
        xaxis_title="Taux d'endettement (%)",
        yaxis_title="",
        yaxis=dict(showticklabels=False),
        height=300,
        margin=dict(l=10, r=10, t=50, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.5, xanchor="center", x=0.5)
    )
    st.plotly_chart(fig, use_container_width=True)

def display_loan_simulator(remaining_capacity):
    """Affiche un simulateur de prêt basé sur la capacité restante."""
    st.subheader("🏦 Simulation de nouveau prêt")
    if remaining_capacity <= 0:
        st.info("Votre capacité d'emprunt restante est nulle ou négative. Vous ne pouvez pas contracter de nouveau prêt selon ces critères.")
        return

    st.markdown(f"Avec une capacité de remboursement de **{remaining_capacity:,.2f} €/mois**, voici ce que vous pourriez emprunter :")
    
    sim_col1, sim_col2 = st.columns(2)
    with sim_col1:
        sim_duree_annees = st.slider("Durée du nouveau prêt (années)", min_value=5, max_value=30, value=25, step=1)
    with sim_col2:
        sim_taux_annuel = st.slider("Taux d'intérêt annuel (%)", min_value=0.5, max_value=8.0, value=3.5, step=0.1)

    sim_duree_mois = sim_duree_annees * 12
    
    montant_empruntable = calculate_loan_principal(remaining_capacity, sim_taux_annuel, sim_duree_mois)

    st.metric(
        label=f"Montant empruntable sur {sim_duree_annees} ans à {sim_taux_annuel}%",
        value=f"{montant_empruntable:,.0f} €"
    )

# --- Exécution Principale ---

#def main():
st.title("🏦 Capacité d'Endettement")
st.markdown("Cette page analyse votre capacité à contracter de nouveaux prêts en fonction de vos revenus et de vos charges de crédits existantes.")

# Vérification des données
if 'revenus' not in st.session_state or 'passifs' not in st.session_state:
    st.warning("⚠️ Veuillez d'abord renseigner vos revenus (page **4_Flux**) et vos passifs (page **2_Patrimoine**).")
    st.stop()

# --- Paramètres ---
st.sidebar.header("Paramètres de Calcul")
max_debt_ratio = st.sidebar.radio(
    "Taux d'endettement maximum",
    options=[35, 40],
    format_func=lambda x: f"{x} %",
    index=0,
    help="Le taux d'endettement maximum autorisé par les banques. La norme est de 35%."
)

# --- Calculs ---
revenus = st.session_state.get('revenus', [])
passifs = st.session_state.get('passifs', [])

weighted_income_data = calculate_weighted_income(revenus)
debt_data = calculate_current_debt_service(passifs)
total_weighted_income = weighted_income_data["total"]
total_current_debt = debt_data["total"]

# --- Affichage ---
with st.expander("Détail des revenus pris en compte", expanded=False):
    st.markdown(f"""
    - **Salaires totaux :** `{weighted_income_data["salaires"]:,.2f} €` (pris à 100%)
    - **Loyers bruts totaux :** `{weighted_income_data["loyers_bruts"]:,.2f} €`
    - **Loyers pondérés ({RENTAL_INCOME_WEIGHT:.0%}) :** `{weighted_income_data["loyers_ponderes"]:,.2f} €`
    - **Total des revenus pondérés :** `{total_weighted_income:,.2f} €`
    
    *Les "Autres revenus" ne sont pas pris en compte dans ce calcul.*
    """)

remaining_capacity = display_results(total_weighted_income, total_current_debt, max_debt_ratio)

if remaining_capacity is not None:
    st.markdown("---")
    display_debt_ratio_breakdown_chart(debt_data["details"], total_weighted_income, max_debt_ratio)

    st.markdown("---")
    display_loan_simulator(remaining_capacity)


#if __name__ == "__main__":
#    main()