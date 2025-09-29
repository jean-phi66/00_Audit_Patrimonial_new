"""
Module de calculs financiers pour le simulateur d'investissement
Version adaptée pour l'intégration dans l'application d'audit patrimonial
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Any


def calculer_mensualite_credit_scpi(montant: float, taux: float, duree: float, assurance: float) -> float:
    """
    Calcule la mensualité d'un crédit SCPI (capital + intérêts + assurance).
    
    Args:
        montant: Montant emprunté
        taux: Taux d'intérêt annuel du crédit
        duree: Durée du crédit en années
        assurance: Taux d'assurance annuel
        
    Returns:
        Mensualité totale du crédit
    """
    if montant <= 0 or duree <= 0:
        return 0.0
    
    taux_mensuel_credit = (taux + assurance) / 12
    nb_mois_credit = int(duree * 12)
    
    if taux_mensuel_credit > 0:
        mensualite = montant * (taux_mensuel_credit * (1 + taux_mensuel_credit)**nb_mois_credit) / ((1 + taux_mensuel_credit)**nb_mois_credit - 1)
    else:
        mensualite = montant / nb_mois_credit
        
    return mensualite


def calculer_revenus_scpi(montant: float, taux_distribution: float, scpi_europeenne_ratio: float, tmi: float) -> Tuple[float, float, float]:
    """
    Calcule les revenus SCPI bruts, imposables et nets.
    
    Args:
        montant: Montant investi en SCPI
        taux_distribution: Taux de distribution annuel
        scpi_europeenne_ratio: Ratio de SCPI européennes (non soumises aux prélèvements sociaux)
        tmi: Taux marginal d'imposition
        
    Returns:
        Tuple (revenus_bruts_mensuels, impots_mensuels, revenus_nets_mensuels)
    """
    if montant <= 0:
        return 0.0, 0.0, 0.0
    
    revenus_bruts_mensuels = montant * taux_distribution / 12
    # Calcul du taux d'imposition SCPI en tenant compte du ratio européen
    taux_imposition_scpi = tmi + (1 - scpi_europeenne_ratio) * 0.172  # 17.2% de prélèvements sociaux
    impots_mensuels = revenus_bruts_mensuels * taux_imposition_scpi
    revenus_nets_mensuels = revenus_bruts_mensuels - impots_mensuels
    
    return revenus_bruts_mensuels, impots_mensuels, revenus_nets_mensuels


def calculer_economie_impots_per(versements_mensuels: float, tmi: float) -> float:
    """
    Calcule l'économie d'impôts mensuelle liée aux versements PER.
    
    Args:
        versements_mensuels: Montant des versements mensuels PER
        tmi: Taux marginal d'imposition
        
    Returns:
        Économie d'impôts mensuelle (valeur positive)
    """
    if versements_mensuels <= 0:
        return 0.0
    
    return versements_mensuels * tmi


def calculer_effort_epargne_scpi(mensualite_credit: float, loyers_nets: float, versements: float) -> float:
    """
    Calcule l'effort d'épargne mensuel pour la SCPI.
    
    Args:
        mensualite_credit: Mensualité du crédit SCPI
        loyers_nets: Loyers nets mensuels perçus
        versements: Versements mensuels complémentaires
        
    Returns:
        Effort d'épargne mensuel net
    """
    return mensualite_credit - loyers_nets + versements


def calculer_donnees_tableau_actifs(resultat_optimisation: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcule les données nécessaires pour le tableau des résultats par actif.
    
    Args:
        resultat_optimisation: Résultats de l'optimisation
        params: Paramètres de simulation
        
    Returns:
        Dictionnaire avec toutes les données calculées
    """
    # Extraction des valeurs optimales
    capital_av = resultat_optimisation.get('capital_av_opt', 0)
    capital_per = resultat_optimisation.get('capital_per_opt', 0)
    capital_scpi = resultat_optimisation.get('capital_scpi_opt', 0)
    versement_av = resultat_optimisation.get('versement_av_opt', 0)
    versement_per = resultat_optimisation.get('versement_per_opt', 0)
    versement_scpi = resultat_optimisation.get('versement_scpi_opt', 0)
    credit_scpi_montant = resultat_optimisation.get('credit_scpi_montant_opt', 0)
    
    # Calcul de la mensualité crédit SCPI
    mensualite_credit_scpi = 0
    if credit_scpi_montant > 0:
        mensualite_credit_scpi = calculer_mensualite_credit_scpi(
            credit_scpi_montant,
            params.get('credit_scpi_taux', 0.04),
            params.get('credit_scpi_duree', 15),
            params.get('credit_scpi_assurance', 0.003)
        )
    
    # Calcul des revenus SCPI
    capital_scpi_total = capital_scpi + credit_scpi_montant
    revenus_scpi_bruts, impots_scpi, revenus_scpi_nets = calculer_revenus_scpi(
        capital_scpi_total,
        params.get('taux_distribution_scpi', 0.05),
        params.get('scpi_europeenne_ratio', 0.0),
        params.get('tmi', 0.30)
    )
    
    # Calcul de l'économie d'impôts PER
    economie_impots_per = calculer_economie_impots_per(versement_per, params.get('tmi', 0.30))
    
    # Calculs des impacts fiscaux mensuels
    impact_fiscal_av = 0  # AV neutre fiscalement en phase d'accumulation
    impact_fiscal_per = -economie_impots_per  # Négatif = économie
    impact_fiscal_scpi = impots_scpi  # Positif = impôts à payer
    
    # Calculs des efforts d'épargne mensuels
    effort_epargne_av = versement_av
    effort_epargne_per = versement_per - economie_impots_per
    effort_epargne_scpi = versement_scpi + mensualite_credit_scpi - revenus_scpi_bruts + impots_scpi
    
    # Loyers mensuels nets (pour cohérence avec l'affichage)
    loyer_av = 0  # Pas de loyer pour AV
    loyer_per = 0  # Pas de loyer pour PER
    loyer_scpi = revenus_scpi_nets
    
    # Impact fiscal total
    impact_fiscal_total = impact_fiscal_av + impact_fiscal_per + impact_fiscal_scpi
    
    return {
        # Capitaux initiaux
        'capital_av': capital_av,
        'capital_per': capital_per,
        'capital_scpi': capital_scpi,
        'credit_scpi_montant': credit_scpi_montant,
        
        # Versements mensuels
        'versement_av': versement_av,
        'versement_per': versement_per,
        'versement_scpi': versement_scpi,
        
        # Données crédit SCPI
        'mensualite_credit_scpi': mensualite_credit_scpi,
        
        # Revenus SCPI
        'revenus_scpi_bruts': revenus_scpi_bruts,
        'impots_scpi': impots_scpi,
        'revenus_scpi_nets': revenus_scpi_nets,
        
        # Économie d'impôts PER
        'economie_impots_per': economie_impots_per,
        
        # Loyers mensuels nets
        'loyer_av': loyer_av,
        'loyer_per': loyer_per,
        'loyer_scpi': loyer_scpi,
        
        # Impacts fiscaux mensuels
        'impact_fiscal_av': impact_fiscal_av,
        'impact_fiscal_per': impact_fiscal_per,
        'impact_fiscal_scpi': impact_fiscal_scpi,
        'impact_fiscal_total': impact_fiscal_total,
        
        # Efforts d'épargne mensuels
        'effort_epargne_av': effort_epargne_av,
        'effort_epargne_per': effort_epargne_per,
        'effort_epargne_scpi': effort_epargne_scpi
    }


def calculer_statistiques_simulation(resultat_optimisation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcule des statistiques utiles sur la simulation.
    
    Args:
        resultat_optimisation: Résultats de l'optimisation
        
    Returns:
        Dictionnaire avec les statistiques calculées
    """
    if 'df_res_optimal' not in resultat_optimisation:
        return {}
    
    df_res = resultat_optimisation['df_res_optimal']
    
    statistiques = {
        'patrimoine_initial': (
            resultat_optimisation.get('capital_av_opt', 0) +
            resultat_optimisation.get('capital_per_opt', 0) +
            resultat_optimisation.get('capital_scpi_opt', 0)
        ),
        'patrimoine_final': resultat_optimisation.get('solde_final_opt', 0),
        'gain_total': resultat_optimisation.get('solde_final_opt', 0) - (
            resultat_optimisation.get('capital_av_opt', 0) +
            resultat_optimisation.get('capital_per_opt', 0) +
            resultat_optimisation.get('capital_scpi_opt', 0)
        ),
        'versements_totaux_mensuels': (
            resultat_optimisation.get('versement_av_opt', 0) +
            resultat_optimisation.get('versement_per_opt', 0) +
            resultat_optimisation.get('versement_scpi_opt', 0)
        ),
        'effort_epargne_moyen': df_res['effort_epargne_mensuel'].mean(),
        'effort_epargne_max': df_res['effort_epargne_mensuel'].max(),
        'economie_impots_totale': df_res['economie_impot_per_mensuelle'].sum(),
        'impots_scpi_totaux': df_res['impot_scpi_mensuel'].sum(),
        'credit_scpi_montant': resultat_optimisation.get('credit_scpi_montant_opt', 0)
    }
    
    # Calcul du rendement annualisé
    duree_annees = len(df_res) / 12
    if statistiques['patrimoine_initial'] > 0 and duree_annees > 0:
        rendement_annualise = (
            (statistiques['patrimoine_final'] / statistiques['patrimoine_initial']) ** (1 / duree_annees) - 1
        ) * 100
        statistiques['rendement_annualise'] = rendement_annualise
    else:
        statistiques['rendement_annualise'] = 0
    
    return statistiques


def analyser_repartition_finale(resultat_optimisation: Dict[str, Any]) -> Dict[str, float]:
    """
    Analyse la répartition du patrimoine final par support.
    
    Args:
        resultat_optimisation: Résultats de l'optimisation
        
    Returns:
        Dictionnaire avec les pourcentages de répartition
    """
    if 'df_res_optimal' not in resultat_optimisation:
        return {}
    
    df_res = resultat_optimisation['df_res_optimal']
    mois_final = df_res['mois'].max()
    
    solde_av = df_res.loc[df_res['mois'] == mois_final, 'solde_av_mensuel'].values[0]
    solde_per = df_res.loc[df_res['mois'] == mois_final, 'solde_per_mensuel'].values[0]
    solde_scpi = df_res.loc[df_res['mois'] == mois_final, 'solde_scpi_mensuel'].values[0]
    
    patrimoine_total = solde_av + solde_per + solde_scpi
    
    if patrimoine_total > 0:
        repartition = {
            'assurance_vie_pct': (solde_av / patrimoine_total) * 100,
            'per_pct': (solde_per / patrimoine_total) * 100,
            'scpi_pct': (solde_scpi / patrimoine_total) * 100
        }
    else:
        repartition = {
            'assurance_vie_pct': 0,
            'per_pct': 0,
            'scpi_pct': 0
        }
    
    return repartition


def valider_coherence_resultats(resultat_optimisation: Dict[str, Any], contraintes: Dict[str, float]) -> Tuple[bool, list]:
    """
    Valide la cohérence des résultats d'optimisation avec les contraintes.
    
    Args:
        resultat_optimisation: Résultats de l'optimisation
        contraintes: Dictionnaire des contraintes (effort_max, mensualite_max, etc.)
        
    Returns:
        Tuple (coherent, liste_erreurs)
    """
    erreurs = []
    
    # Vérification de l'effort d'épargne
    effort_max_calcule = resultat_optimisation.get('max_effort_opt', 0)
    effort_max_autorise = contraintes.get('effort_max', float('inf'))
    
    if effort_max_calcule > effort_max_autorise * 1.01:  # Tolérance de 1%
        erreurs.append(f"Effort d'épargne dépassé : {effort_max_calcule:.2f} > {effort_max_autorise:.2f}")
    
    # Vérification du capital initial total
    capital_total = (
        resultat_optimisation.get('capital_av_opt', 0) +
        resultat_optimisation.get('capital_per_opt', 0) +
        resultat_optimisation.get('capital_scpi_opt', 0)
    )
    capital_max_autorise = contraintes.get('capital_initial_max', float('inf'))
    
    if capital_total > capital_max_autorise * 1.01:  # Tolérance de 1%
        erreurs.append(f"Capital initial dépassé : {capital_total:.2f} > {capital_max_autorise:.2f}")
    
    # Vérification de la mensualité crédit SCPI
    if 'df_res_optimal' in resultat_optimisation:
        df_res = resultat_optimisation['df_res_optimal']
        mensualite_max_calculee = df_res['mensualite_credit_scpi_mensuel'].max()
        mensualite_max_autorisee = contraintes.get('mensualite_max', float('inf'))
        
        if mensualite_max_calculee > mensualite_max_autorisee * 1.01:  # Tolérance de 1%
            erreurs.append(f"Mensualité crédit dépassée : {mensualite_max_calculee:.2f} > {mensualite_max_autorisee:.2f}")
    
    return len(erreurs) == 0, erreurs