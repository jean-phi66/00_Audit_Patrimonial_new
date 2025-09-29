"""
Patch pour ajouter la fonctionnalité TRI aux métriques d'optimisation
"""

import streamlit as st
import numpy as np
from typing import Dict, Any


def calculer_tri_optimisation(resultat_optimisation: Dict[str, Any]) -> float:
    """
    Calcule le TRI (Taux de Rendement Interne) de la stratégie d'optimisation.
    
    Args:
        resultat_optimisation: Résultats de l'optimisation contenant les paramètres et résultats
        
    Returns:
        TRI annuel en pourcentage
    """
    try:
        if not resultat_optimisation or not resultat_optimisation.get('success'):
            return 0.0
            
        # Récupération des données nécessaires avec des valeurs par défaut prudentes
        capital_initial = resultat_optimisation.get('capital_initial', 0)
        effort_mensuel = resultat_optimisation.get('max_effort_opt', 0)
        duree_mois = resultat_optimisation.get('duree_mois', 240)  # par défaut 20 ans
        capital_final = resultat_optimisation.get('solde_final_opt', 0)
        
        if capital_initial <= 0 or effort_mensuel <= 0 or capital_final <= capital_initial:
            return 0.0
            
        # Méthode améliorée : calcul plus précis du TRI
        duree_annees = duree_mois / 12
        
        if duree_annees <= 0:
            return 0.0
        
        # Calcul par approximation itérative du TRI
        # On cherche le taux r tel que VAN = 0
        def van(r):
            """Calcul de la Valeur Actuelle Nette pour un taux r mensuel"""
            van_val = -capital_initial  # Investissement initial
            for mois in range(1, duree_mois + 1):
                van_val -= effort_mensuel / ((1 + r) ** mois)  # Flux mensuels actualisés
            van_val += capital_final / ((1 + r) ** duree_mois)  # Valeur finale actualisée
            return van_val
        
        # Recherche par dichotomie du taux mensuel
        r_min, r_max = -0.5, 0.5  # Bornes raisonnables pour le taux mensuel
        tolerance = 1e-6
        max_iterations = 100
        
        for _ in range(max_iterations):
            r_mid = (r_min + r_max) / 2
            van_mid = van(r_mid)
            
            if abs(van_mid) < tolerance:
                # Conversion en taux annuel
                tri_annuel = ((1 + r_mid) ** 12 - 1) * 100
                return max(0, min(50, tri_annuel))
            
            if van_mid > 0:
                r_min = r_mid
            else:
                r_max = r_mid
        
        # Si pas de convergence, calcul approché
        total_investi = capital_initial + (effort_mensuel * duree_mois)
        if total_investi > 0:
            tri_approx = ((capital_final / total_investi) ** (1 / duree_annees) - 1) * 100
            return max(0, min(50, tri_approx))
        else:
            return 0.0
                    
    except Exception as e:
        return 0.0


def afficher_metriques_principales_avec_tri(resultat_optimisation: Dict[str, Any]):
    """
    Affiche les métriques principales des résultats d'optimisation avec TRI.
    
    Args:
        resultat_optimisation: Résultats de l'optimisation
    """
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="💰 Solde final optimal",
            value=f"{resultat_optimisation['solde_final_opt']:,.2f} €"
        )
    
    with col2:
        st.metric(
            label="🎯 Effort d'épargne maximal",
            value=f"{resultat_optimisation['max_effort_opt']:.2f} €/mois"
        )
    
    with col3:
        # Calcul et affichage du TRI
        tri_percent = calculer_tri_optimisation(resultat_optimisation)
        
        st.metric(
            label="📈 TRI annuel",
            value=f"{tri_percent:.2f} %"
        )
    
    with col4:
        statut_color = "🟢" if resultat_optimisation['success'] else "🔴"
        contraintes_color = "🟢" if resultat_optimisation['contraintes_satisfaites'] else "🟠"
        st.write(f"**Statut:** {statut_color} {'Réussi' if resultat_optimisation['success'] else 'Échec'}")
        st.write(f"**Contraintes:** {contraintes_color} {'OK' if resultat_optimisation['contraintes_satisfaites'] else 'Attention'}")