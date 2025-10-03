"""
Module pour l'affichage des fonctions de capacité d'endettement.

Ce module contient toutes les fonctions d'interface utilisateur (UI) pour la page
Capacité d'Endettement, utilisant Streamlit pour l'affichage des résultats et
des graphiques.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from core.endettement_charts import (
    calculate_endettement_metrics,
    create_debt_gauge_chart,
    create_debt_breakdown_chart,
    RENTAL_INCOME_WEIGHT
)
from core.patrimoine_logic import calculate_loan_principal

def display_results(weighted_income, current_debt, max_debt_ratio_pct):
    """
    Affiche les résultats du calcul de capacité d'endettement.
    
    Args:
        weighted_income (float): Revenus pondérés mensuels
        current_debt (float): Charges de prêts actuelles mensuelles
        max_debt_ratio_pct (float): Taux d'endettement maximum autorisé (%)
        
    Returns:
        float: Capacité d'emprunt restante mensuelle
    """
    st.subheader("📊 Résultats")
    
    if weighted_income == 0:
        st.warning("Les revenus pondérés sont de 0. Impossible de calculer le taux d'endettement.")
        return

    # Calculs
    max_debt_service = weighted_income * (max_debt_ratio_pct / 100)
    current_debt_ratio_pct = (current_debt / weighted_income) * 100 if weighted_income > 0 else 0
    remaining_capacity = max(0, max_debt_service - current_debt)

    # Affichage en deux colonnes principales
    results_col1, results_col2 = st.columns([1, 1])

    with results_col1:
        st.markdown("##### 📈 Indicateurs Clés")
        # KPI en 2x2 + 1
        kpi_col1, kpi_col2 = st.columns(2)
        kpi_col1.metric("Revenus Pondérés", f"{weighted_income:,.0f} €/mois")
        kpi_col2.metric("Mensualité Maximum", f"{max_debt_service:,.0f} €/mois")

        kpi_col3, kpi_col4 = st.columns(2)
        kpi_col3.metric("Charges de Prêts", f"{current_debt:,.0f} €/mois")
        kpi_col4.metric(
            "Taux d'Endettement Actuel",
            f"{current_debt_ratio_pct:.2f} %",
            delta=f"{current_debt_ratio_pct - max_debt_ratio_pct:.2f} % pts",
            delta_color="inverse"
        )
        
        # KPI capacité restante sur toute la largeur
        st.metric("Capacité d'Emprunt Restante", f"{remaining_capacity:,.0f} €/mois")

    with results_col2:
        # Jauge de visualisation (sans titre supplémentaire)
        metrics_data = calculate_endettement_metrics([], [], max_debt_ratio_pct)
        metrics_data.update({
            'weighted_income': weighted_income,
            'current_debt': current_debt,
            'current_debt_ratio_pct': current_debt_ratio_pct,
            'max_debt_ratio_pct': max_debt_ratio_pct
        })
        fig = create_debt_gauge_chart(metrics_data)
        # Supprimer le titre du graphique pour éviter la superposition
        fig.update_layout(
            title="",  # Supprime le titre du graphique
            height=350, 
            margin=dict(t=20, b=20, l=20, r=20)
        )
        st.plotly_chart(fig, use_container_width=True)

    return remaining_capacity

def display_debt_ratio_breakdown_chart(debt_details, weighted_income, max_debt_ratio_pct):
    """
    Affiche un graphique de la répartition du taux d'endettement par prêt.
    
    Args:
        debt_details (list): Liste des détails des prêts
        weighted_income (float): Revenus pondérés mensuels
        max_debt_ratio_pct (float): Taux d'endettement maximum autorisé (%)
    """
    st.subheader("Répartition du Taux d'Endettement par Prêt")
    
    if not debt_details:
        st.info("Aucun prêt en cours à afficher.")
        return
    
    if weighted_income == 0:
        st.warning("Revenus pondérés nuls, impossible de calculer la répartition.")
        return

    # Utiliser la fonction centralisée
    metrics_data = {
        'debt_details': debt_details,
        'weighted_income': weighted_income,
        'max_debt_ratio_pct': max_debt_ratio_pct
    }
    fig = create_debt_breakdown_chart(metrics_data)
    fig.update_layout(height=300)  # Ajuster la hauteur pour l'interface GUI
    st.plotly_chart(fig, use_container_width=True)

def display_loan_simulator(remaining_capacity):
    """
    Affiche un simulateur de prêt basé sur la capacité restante.
    
    Args:
        remaining_capacity (float): Capacité d'emprunt restante mensuelle
    """
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

def display_weighted_income_details(weighted_income_data):
    """
    Affiche le détail des revenus pris en compte pour le calcul.
    
    Args:
        weighted_income_data (dict): Données détaillées des revenus pondérés
    """
    with st.expander("Détail des revenus pris en compte", expanded=False):
        st.markdown(f"""
        - **Salaires totaux :** `{weighted_income_data["salaires"]:,.2f} €` (pris à 100%)
        - **Loyers bruts totaux :** `{weighted_income_data["loyers_bruts"]:,.2f} €`
        - **Loyers pondérés ({RENTAL_INCOME_WEIGHT:.0%}) :** `{weighted_income_data["loyers_ponderes"]:,.2f} €`
        - **Total des revenus pondérés :** `{weighted_income_data["total"]:,.2f} €`
        
        *Les "Autres revenus" ne sont pas pris en compte dans ce calcul.*
        """)