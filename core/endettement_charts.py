"""
Module pour la génération des graphiques de capacité d'endettement.

Ce module centralise les fonctions de génération des graphiques de la page 
Focus Endettement, sans dépendances Streamlit pour permettre leur utilisation
aussi bien dans le GUI que dans le script de génération de graphiques.

Graphiques générés:
1. Jauge de taux d'endettement
2. Graphique en barres horizontales de répartition des prêts
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from core.patrimoine_logic import calculate_monthly_payment

# --- Constantes ---
RENTAL_INCOME_WEIGHT = 0.70  # Pondération des revenus locatifs par les banques

def calculate_weighted_income(revenus):
    """
    Calcule les revenus mensuels pondérés pour le calcul de la capacité d'endettement.
    - Salaires: 100%
    - Revenus locatifs (Patrimoine): 70%
    - Autres revenus: 0% (non pris en compte)
    
    Args:
        revenus (list): Liste des revenus
        
    Returns:
        dict: Dictionnaire avec total, salaires, loyers_bruts, loyers_ponderes
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
    
    Args:
        passifs (list): Liste des passifs/prêts
        
    Returns:
        dict: Dictionnaire avec total et details (liste des prêts)
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

def calculate_endettement_metrics(revenus, passifs, max_debt_ratio_pct=35):
    """
    Calcule toutes les métriques d'endettement nécessaires aux graphiques.
    
    Args:
        revenus (list): Liste des revenus
        passifs (list): Liste des passifs
        max_debt_ratio_pct (int): Taux d'endettement maximum autorisé
        
    Returns:
        dict: Métriques complètes d'endettement
    """
    weighted_income_data = calculate_weighted_income(revenus)
    debt_data = calculate_current_debt_service(passifs)
    
    total_weighted_income = weighted_income_data["total"]
    total_current_debt = debt_data["total"]
    
    # Calculs des métriques
    max_debt_service = total_weighted_income * (max_debt_ratio_pct / 100)
    current_debt_ratio_pct = (total_current_debt / total_weighted_income * 100) if total_weighted_income > 0 else 0
    remaining_capacity = max(0, max_debt_service - total_current_debt)
    
    return {
        'weighted_income': total_weighted_income,
        'current_debt': total_current_debt,
        'max_debt_service': max_debt_service,
        'current_debt_ratio_pct': current_debt_ratio_pct,
        'remaining_capacity': remaining_capacity,
        'max_debt_ratio_pct': max_debt_ratio_pct,
        'debt_details': debt_data["details"],
        'weighted_income_data': weighted_income_data
    }

def create_debt_gauge_chart(metrics):
    """
    Crée la jauge du taux d'endettement.
    
    Args:
        metrics (dict): Métriques d'endettement calculées
        
    Returns:
        plotly.graph_objects.Figure: Graphique en jauge
    """
    current_debt_ratio_pct = metrics['current_debt_ratio_pct']
    max_debt_ratio_pct = metrics['max_debt_ratio_pct']
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=current_debt_ratio_pct,
        number={'suffix': ' %'},
        title={'text': f"Taux d'endettement (Cible: {max_debt_ratio_pct}%)"},
        delta={'reference': max_debt_ratio_pct, 'increasing': {'color': "red"}, 'decreasing': {'color': "green"}},
        gauge={
            'axis': {'range': [None, 50], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "darkblue"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, max_debt_ratio_pct], 'color': 'lightgreen'},
                {'range': [max_debt_ratio_pct, 50], 'color': 'lightcoral'}
            ],
            'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': max_debt_ratio_pct}
        }
    ))
    
    fig.update_layout(
        height=400,
        margin=dict(t=50, b=50, l=50, r=50),
        title=dict(
            text="Jauge du Taux d'Endettement",
            x=0.5,
            xanchor='center'
        )
    )
    
    return fig

def create_debt_breakdown_chart(metrics):
    """
    Crée le graphique en barres horizontales de répartition du taux d'endettement par prêt.
    
    Args:
        metrics (dict): Métriques d'endettement calculées
        
    Returns:
        plotly.graph_objects.Figure: Graphique en barres horizontales
    """
    debt_details = metrics['debt_details']
    weighted_income = metrics['weighted_income']
    max_debt_ratio_pct = metrics['max_debt_ratio_pct']
    
    if not debt_details or weighted_income == 0:
        # Créer un graphique vide avec message
        fig = go.Figure()
        fig.add_annotation(
            text="Aucune donnée d'endettement à afficher",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font_size=16
        )
        fig.update_layout(
            title="Répartition du Taux d'Endettement par Prêt",
            height=150,
            margin=dict(t=50, b=50, l=50, r=50)
        )
        return fig
    
    # Préparer les données pour le graphique
    chart_data = []
    total_current_debt_pct = 0
    
    for loan in debt_details:
        percentage = (loan['mensualite'] / weighted_income) * 100
        chart_data.append({
            'y_axis': "Taux d'endettement",
            'percentage': percentage,
            'pret': loan['libelle'],
            'mensualite': loan['mensualite']
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
            'mensualite': remaining_capacity_amount
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
        text='percentage',
        custom_data=['mensualite'],
        color_discrete_map={
            "Capacité restante": "rgba(44, 160, 44, 0.5)"  # Vert clair transparent
        }
    )
    
    fig.update_traces(
        # Afficher le % et le montant en € (sans décimales)
        texttemplate='%{x:.2f}%<br><b>%{customdata[0]:.0f} €</b>',
        textposition='inside',
        insidetextanchor='middle',
        textfont_size=14
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
        height=75,
        margin=dict(l=10, r=10, t=50, b=50),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )
    
    return fig

def generate_endettement_charts(revenus, passifs, max_debt_ratio_pct=35):
    """
    Génère tous les graphiques d'endettement.
    
    Args:
        revenus (list): Liste des revenus
        passifs (list): Liste des passifs
        max_debt_ratio_pct (int): Taux d'endettement maximum
        
    Returns:
        dict: Dictionnaire contenant les figures et métadonnées
    """
    # Calcul des métriques
    metrics = calculate_endettement_metrics(revenus, passifs, max_debt_ratio_pct)
    
    # Génération des graphiques
    charts = {
        'gauge_chart': create_debt_gauge_chart(metrics),
        'breakdown_chart': create_debt_breakdown_chart(metrics),
        'metrics': metrics
    }
    
    return charts