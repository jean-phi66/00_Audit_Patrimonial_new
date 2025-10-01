"""
Patch pour ajouter la fonctionnalité TRI aux métriques d'optimisation
"""

import streamlit as st
import pandas as pd
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


def afficher_tableau_flux_recapitulatif(resultat_optimisation: Dict[str, Any]):
    """
    Affiche un tableau récapitulatif des flux mensuels et annuels avec radio button.
    
    Args:
        resultat_optimisation: Résultats de l'optimisation
    """
    if not resultat_optimisation or not resultat_optimisation.get('success'):
        st.warning("⚠️ Aucun résultat d'optimisation disponible pour afficher les flux")
        return
    
    st.subheader("💰 Tableau récapitulatif des flux")
    
    # Radio button pour choisir la vue
    vue_flux = st.radio(
        "Type d'affichage :",
        ["📅 Flux mensuels", "🗓️ Flux annuels"],
        horizontal=True,
        key="radio_flux_recap"
    )
    
    # Récupération des données
    try:
        df_res = resultat_optimisation.get('df_res_optimal')
        if df_res is None or df_res.empty:
            st.error("❌ Aucune simulation détaillée disponible")
            return
        
        if vue_flux == "📅 Flux mensuels":
            _afficher_flux_mensuels(df_res, resultat_optimisation)
        else:
            _afficher_flux_annuels(df_res, resultat_optimisation)
            
    except Exception as e:
        st.error(f"❌ Erreur lors de l'affichage des flux : {str(e)}")


def _afficher_flux_mensuels(df_res: pd.DataFrame, resultat_optimisation: Dict[str, Any]):
    """Affiche les flux mensuels avec pagination"""
    
    # Préparation des données mensuelles
    df_flux = df_res.copy()
    
    # Sélection des colonnes pertinentes pour les flux
    colonnes_flux = {
        'mois': 'Mois',
        'versement_av_mensuel': 'Versement AV (€)',
        'versement_per_mensuel': 'Versement PER (€)',
        'versement_scpi_mensuel': 'Versement SCPI (€)',
        'mensualite_credit_scpi_mensuel': 'Mensualité Crédit SCPI (€)',
        'revenu_scpi_brut_mensuel': 'Loyers SCPI (€)',
        'economie_impot_per_mensuelle': 'Économie PER (€)',
        'impot_scpi_mensuel': 'Impôt SCPI (€)',
        'effort_epargne_mensuel': 'Effort Total (€)'
    }
    
    # Vérification des colonnes disponibles
    colonnes_disponibles = {k: v for k, v in colonnes_flux.items() if k in df_flux.columns}
    
    if not colonnes_disponibles:
        st.error("❌ Colonnes de flux non trouvées dans les données")
        return
    
    # Création du DataFrame d'affichage
    df_affichage = df_flux[list(colonnes_disponibles.keys())].copy()
    
    # Formatage des colonnes monétaires
    for col in df_affichage.columns:
        if col != 'mois':
            df_affichage[col] = df_affichage[col].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "0")
    
    # Renommage des colonnes
    df_affichage = df_affichage.rename(columns=colonnes_disponibles)
    
    # Contrôles de pagination
    col_pagination1, col_pagination2, col_pagination3 = st.columns([1, 2, 1])
    
    with col_pagination2:
        # Sélection de la plage de mois
        max_mois = len(df_affichage)
        
        if max_mois > 12:
            annee_debut = st.selectbox(
                "Année de début :",
                options=list(range(1, max_mois // 12 + 2)),
                index=0,
                key="annee_debut_flux"
            )
            
            mois_debut = (annee_debut - 1) * 12
            mois_fin = min(mois_debut + 12, max_mois)
            
            st.write(f"**Année {annee_debut}** (mois {mois_debut + 1} à {mois_fin})")
            df_affichage_page = df_affichage.iloc[mois_debut:mois_fin]
        else:
            df_affichage_page = df_affichage
    
    # Affichage du tableau
    st.dataframe(
        df_affichage_page, 
        use_container_width=True, 
        hide_index=True,
        height=400
    )
    
    # Résumé de la période affichée
    if len(df_affichage_page) > 0:
        with st.expander("📊 Résumé de la période affichée"):
            col1, col2, col3, col4, col5 = st.columns(5)
            
            # Calculs sur la période affichée (en remettant les valeurs numériques)
            df_calcul = df_res.iloc[mois_debut:mois_fin] if 'mois_debut' in locals() else df_res
            
            with col1:
                effort_total_periode = df_calcul['effort_epargne_mensuel'].sum() if 'effort_epargne_mensuel' in df_calcul else 0
                st.metric("Total effort épargne", f"{effort_total_periode:,.0f} €")
            
            with col2:
                mensualites_credit_periode = df_calcul['mensualite_credit_scpi_mensuel'].sum() if 'mensualite_credit_scpi_mensuel' in df_calcul else 0
                st.metric("Total mensualités crédit", f"{mensualites_credit_periode:,.0f} €")
            
            with col3:
                loyers_scpi_periode = df_calcul['revenu_scpi_brut_mensuel'].sum() if 'revenu_scpi_brut_mensuel' in df_calcul else 0
                st.metric("Total loyers SCPI", f"{loyers_scpi_periode:,.0f} €")
            
            with col4:
                economie_per_periode = df_calcul['economie_impot_per_mensuelle'].sum() if 'economie_impot_per_mensuelle' in df_calcul else 0
                st.metric("Total économie PER", f"{economie_per_periode:,.0f} €")
            
            with col5:
                impots_scpi_periode = df_calcul['impot_scpi_mensuel'].sum() if 'impot_scpi_mensuel' in df_calcul else 0
                st.metric("Total impôts SCPI", f"{impots_scpi_periode:,.0f} €")


def _afficher_flux_annuels(df_res: pd.DataFrame, resultat_optimisation: Dict[str, Any]):
    """Affiche les flux agrégés par année"""
    
    # Création de la colonne année
    df_annuel = df_res.copy()
    df_annuel['annee'] = ((df_annuel['mois'] - 1) // 12) + 1
    
    # Agrégation par année
    colonnes_a_sommer = [
        'versement_av_mensuel', 'versement_per_mensuel', 'versement_scpi_mensuel',
        'mensualite_credit_scpi_mensuel', 'revenu_scpi_brut_mensuel',
        'effort_epargne_mensuel', 'economie_impot_per_mensuelle', 'impot_scpi_mensuel'
    ]
    
    # Vérification des colonnes disponibles
    colonnes_somme_dispo = [col for col in colonnes_a_sommer if col in df_annuel.columns]
    
    # Agrégation
    agg_dict = {}
    for col in colonnes_somme_dispo:
        agg_dict[col] = 'sum'
    
    if not agg_dict:
        st.error("❌ Aucune colonne de données trouvée pour l'agrégation")
        return
    
    df_flux_annuel = df_annuel.groupby('annee').agg(agg_dict).reset_index()
    
    # Renommage des colonnes pour l'affichage
    colonnes_affichage = {
        'annee': 'Année',
        'versement_av_mensuel': 'Versements AV (€)',
        'versement_per_mensuel': 'Versements PER (€)', 
        'versement_scpi_mensuel': 'Versements SCPI (€)',
        'mensualite_credit_scpi_mensuel': 'Mensualités Crédit SCPI (€)',
        'revenu_scpi_brut_mensuel': 'Loyers SCPI (€)',
        'economie_impot_per_mensuelle': 'Économie PER (€)',
        'impot_scpi_mensuel': 'Impôts SCPI (€)',
        'effort_epargne_mensuel': 'Effort Total (€)'
    }
    
    # Formatage des données
    df_affichage_annuel = df_flux_annuel.copy()
    
    # Formatage monétaire (sauf pour l'année)
    for col in df_affichage_annuel.columns:
        if col != 'annee' and col in df_affichage_annuel.columns:
            df_affichage_annuel[col] = df_affichage_annuel[col].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "0")
    
    # Renommage des colonnes disponibles
    colonnes_rename = {k: v for k, v in colonnes_affichage.items() if k in df_affichage_annuel.columns}
    df_affichage_annuel = df_affichage_annuel.rename(columns=colonnes_rename)
    
    # Affichage du tableau annuel
    st.dataframe(
        df_affichage_annuel, 
        use_container_width=True, 
        hide_index=True,
        height=400
    )
    
    # Résumé sur toute la période
    with st.expander("📊 Résumé sur toute la période"):
        col1, col2, col3, col4, col5 = st.columns(5)
        
        # Calculs de synthèse (en utilisant les données numériques originales)
        with col1:
            effort_total = df_res['effort_epargne_mensuel'].sum() if 'effort_epargne_mensuel' in df_res else 0
            st.metric("Effort total", f"{effort_total:,.0f} €")
        
        with col2:
            mensualites_credit_total = df_res['mensualite_credit_scpi_mensuel'].sum() if 'mensualite_credit_scpi_mensuel' in df_res else 0
            st.metric("Mensualités crédit totales", f"{mensualites_credit_total:,.0f} €")
        
        with col3:
            loyers_scpi_total = df_res['revenu_scpi_brut_mensuel'].sum() if 'revenu_scpi_brut_mensuel' in df_res else 0
            st.metric("Loyers SCPI totaux", f"{loyers_scpi_total:,.0f} €")
        
        with col4:
            economie_per_total = df_res['economie_impot_per_mensuelle'].sum() if 'economie_impot_per_mensuelle' in df_res else 0
            st.metric("Économie PER totale", f"{economie_per_total:,.0f} €")
        
        with col5:
            impots_scpi_total = df_res['impot_scpi_mensuel'].sum() if 'impot_scpi_mensuel' in df_res else 0
            st.metric("Impôts SCPI totaux", f"{impots_scpi_total:,.0f} €")