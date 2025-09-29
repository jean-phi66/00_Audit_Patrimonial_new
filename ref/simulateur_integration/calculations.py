"""
Module de calculs financiers pour le simulateur d'investissement
Contient toutes les fonctions de calcul des mensualités, loyers, impacts fiscaux, etc.
"""

import pandas as pd
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
    revenus_imposables_mensuels = revenus_bruts_mensuels * (1 - scpi_europeenne_ratio)
    impots_mensuels = revenus_imposables_mensuels * tmi
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


def calculer_impacts_fiscaux_actifs(resultat_optimisation: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, float]:
    """
    Calcule les impacts fiscaux pour tous les actifs.
    
    Args:
        resultat_optimisation: Résultats de l'optimisation
        params: Paramètres de simulation
        
    Returns:
        Dictionnaire avec les impacts fiscaux par actif
    """
    # Récupération des valeurs optimales
    capital_av_opt = resultat_optimisation['capital_av_opt']
    capital_per_opt = resultat_optimisation['capital_per_opt']
    capital_scpi_opt = resultat_optimisation['capital_scpi_opt']
    
    versement_av_opt = resultat_optimisation['versement_av_opt']
    versement_per_opt = resultat_optimisation['versement_per_opt']
    versement_scpi_opt = resultat_optimisation['versement_scpi_opt']
    
    credit_scpi_montant_opt = resultat_optimisation['credit_scpi_montant_opt']
    
    # Calculs d'impact fiscal
    impact_fiscal_av = 0.0  # Pas d'impact fiscal immédiat pour l'AV
    
    # PER : économie d'impôts (valeur négative car c'est un avantage)
    economie_impots_per = calculer_economie_impots_per(versement_per_opt, params['tmi'])
    impact_fiscal_per = -economie_impots_per
    
    # SCPI : impôts sur les revenus (valeur positive car c'est une charge)
    if credit_scpi_montant_opt > 0:
        _, impots_scpi, _ = calculer_revenus_scpi(
            credit_scpi_montant_opt,
            params['taux_distribution_scpi'],
            params['scpi_europeenne_ratio'],
            params['tmi']
        )
        impact_fiscal_scpi = impots_scpi
    else:
        impact_fiscal_scpi = 0.0
    
    return {
        'av': impact_fiscal_av,
        'per': impact_fiscal_per,
        'scpi': impact_fiscal_scpi,
        'total': impact_fiscal_av + impact_fiscal_per + impact_fiscal_scpi
    }


def calculer_donnees_tableau_actifs(resultat_optimisation: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcule toutes les données nécessaires pour le tableau des résultats par actif.
    
    Args:
        resultat_optimisation: Résultats de l'optimisation
        params: Paramètres de simulation
        
    Returns:
        Dictionnaire avec toutes les données calculées
    """
    # Récupération des valeurs optimales
    capital_av_opt = resultat_optimisation['capital_av_opt']
    capital_per_opt = resultat_optimisation['capital_per_opt']
    capital_scpi_opt = resultat_optimisation['capital_scpi_opt']
    
    versement_av_opt = resultat_optimisation['versement_av_opt']
    versement_per_opt = resultat_optimisation['versement_per_opt']
    versement_scpi_opt = resultat_optimisation['versement_scpi_opt']
    
    credit_scpi_montant_opt = resultat_optimisation['credit_scpi_montant_opt']
    
    # Calculs pour la SCPI
    if credit_scpi_montant_opt > 0:
        # Mensualité de crédit
        mensualite_credit_scpi = calculer_mensualite_credit_scpi(
            credit_scpi_montant_opt,
            params['credit_scpi_taux'],
            params['credit_scpi_duree'],
            params['credit_scpi_assurance']
        )
        
        # Revenus SCPI
        revenus_bruts, impots_scpi, loyers_nets = calculer_revenus_scpi(
            credit_scpi_montant_opt,
            params['taux_distribution_scpi'],
            params['scpi_europeenne_ratio'],
            params['tmi']
        )
        
        # Effort d'épargne SCPI
        effort_epargne_scpi = calculer_effort_epargne_scpi(
            mensualite_credit_scpi,
            loyers_nets,
            versement_scpi_opt
        )
        
        impact_fiscal_scpi = impots_scpi
    else:
        mensualite_credit_scpi = 0.0
        revenus_bruts = 0.0
        loyers_nets = 0.0
        impots_scpi = 0.0
        effort_epargne_scpi = versement_scpi_opt
        impact_fiscal_scpi = 0.0
    
    # Calculs pour le PER
    economie_impots_per = calculer_economie_impots_per(versement_per_opt, params['tmi'])
    
    # Calculs des impacts fiscaux
    impacts_fiscaux = calculer_impacts_fiscaux_actifs(resultat_optimisation, params)
    
    return {
        # Capitaux initiaux
        'capital_av': capital_av_opt,
        'capital_per': capital_per_opt,
        'capital_scpi': capital_scpi_opt,
        
        # Versements mensuels
        'versement_av': versement_av_opt,
        'versement_per': versement_per_opt,
        'versement_scpi': versement_scpi_opt,
        
        # Mensualités de crédit
        'mensualite_credit_av': 0.0,
        'mensualite_credit_per': 0.0,
        'mensualite_credit_scpi': mensualite_credit_scpi,
        
        # Loyers
        'loyer_av': 0.0,
        'loyer_per': 0.0,
        'loyer_scpi': loyers_nets,
        
        # Impacts fiscaux
        'impact_fiscal_av': impacts_fiscaux['av'],
        'impact_fiscal_per': impacts_fiscaux['per'],
        'impact_fiscal_scpi': impacts_fiscaux['scpi'],
        'impact_fiscal_total': impacts_fiscaux['total'],
        
        # Efforts d'épargne
        'effort_epargne_av': versement_av_opt,
        'effort_epargne_per': versement_per_opt,
        'effort_epargne_scpi': effort_epargne_scpi,
        
        # Détails complémentaires
        'revenus_scpi_bruts': revenus_bruts,
        'impots_scpi': impots_scpi,
        'economie_impots_per': economie_impots_per,
        'credit_scpi_montant': credit_scpi_montant_opt
    }