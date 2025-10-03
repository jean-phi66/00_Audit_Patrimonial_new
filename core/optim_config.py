"""
Module de configuration pour le simulateur d'investissement
Gère l'initialisation des paramètres et du session state
"""

import streamlit as st
from core.optim_simulation_financiere import creer_parametres_defaut
from typing import Dict, Any


def initialiser_session_state():
    """
    Initialise les paramètres par défaut dans le session state s'ils n'existent pas déjà.
    """
    if 'optim_params_initialized' not in st.session_state:
        st.session_state.optim_params_initialized = True
        st.session_state.optim_params = creer_parametres_defaut()
        
        # Valeurs par défaut pour les variables d'optimisation
        st.session_state.optim_default_values = {
            'capital_av': 0.0,
            'capital_per': 0.0,
            'capital_scpi': 10000.0,
            'versement_av': 0.0,
            'versement_per': 100.0,
            'versement_scpi': 0.0,
            'credit_scpi_montant': 175000.0
        }
        
        # Valeurs courantes (conservent les dernières valeurs optimisées ou saisies)
        st.session_state.optim_current_values = {
            'capital_av': 0.0,
            'capital_per': 0.0,
            'capital_scpi': 10000.0,
            'versement_av': 0.0,
            'versement_per': 100.0,
            'versement_scpi': 0.0,
            'credit_scpi_montant': 175000.0
        }
        
        # État d'activation des variables d'optimisation
        st.session_state.optim_activer_vars = {
            'capital_av': True,
            'capital_per': False,
            'capital_scpi': True,
            'versement_av': True,
            'versement_per': True,
            'versement_scpi': False,
            'credit_scpi_montant': True
        }
        
        # Paramètres persistants de la sidebar
        st.session_state.optim_sidebar_params = {
            'effort_max': 1000.0,
            'mensualite_max': 600.0,
            'capital_initial_max': 50000.0,
            'plafond_per_annuel': 27840.0  # Valeur par défaut
        }
        
        # Résultats de la dernière optimisation
        st.session_state.optim_dernier_resultat = None


def mettre_a_jour_parametres_sidebar(parametres_sidebar: Dict[str, Any]):
    """
    Met à jour les paramètres de la simulation avec les valeurs de la sidebar.
    
    Args:
        parametres_sidebar: Dictionnaire des paramètres saisis dans la sidebar
    """
    # Mise à jour du plafond PER dans les paramètres d'optimisation
    if parametres_sidebar['plafond_per_annuel'] != st.session_state.optim_params['plafond_per_annuel']:
        st.session_state.optim_params['plafond_per_annuel'] = parametres_sidebar['plafond_per_annuel']
    
    # Synchronisation avec le session_state persistant (déjà fait dans afficher_sidebar_parametres)
    # Cette fonction garde sa logique actuelle pour la compatibilité


def mettre_a_jour_variables_optimisation(variables_info: Dict[str, Dict[str, Any]]):
    """
    Met à jour l'état des variables d'optimisation et leurs valeurs.
    
    Args:
        variables_info: Dictionnaire avec l'état des variables d'optimisation
    """
    for var_name, info in variables_info.items():
        # Mise à jour de l'état d'activation
        st.session_state.optim_activer_vars[var_name] = info['activer']
        
        # Mise à jour de la valeur courante
        st.session_state.optim_current_values[var_name] = info['valeur']


def preparer_parametres_optimisation(parametres_sidebar: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prépare les paramètres pour l'optimisation.
    
    Args:
        parametres_sidebar: Paramètres de la sidebar
        
    Returns:
        Dictionnaire des paramètres d'optimisation
    """
    # Variables disponibles dans l'ordre attendu par maximiser_solde_final_avec_contrainte
    variables_ordre = ['capital_av', 'capital_per', 'capital_scpi', 'versement_av', 
                      'versement_per', 'versement_scpi', 'credit_scpi_montant']
    
    # Variables à optimiser (liste de booléens)
    activer_vars = []
    valeurs_defaut = []
    
    for var_name in variables_ordre:
        is_active = st.session_state.optim_activer_vars.get(var_name, False)
        activer_vars.append(is_active)
        valeurs_defaut.append(st.session_state.optim_current_values.get(var_name, 0.0))
    
    # Valeurs fixées (non optimisées) - pour information
    valeurs_fixes = {}
    for var_name in variables_ordre:
        if not st.session_state.optim_activer_vars.get(var_name, False):
            valeurs_fixes[var_name] = st.session_state.optim_current_values.get(var_name, 0.0)
    
    return {
        'effort_max': parametres_sidebar['effort_max'],
        'mensualite_max': parametres_sidebar['mensualite_max'],
        'capital_initial_max': parametres_sidebar['capital_initial_max'],
        'activer_vars': activer_vars,  # Liste de 7 booléens
        'valeurs_defaut': valeurs_defaut,  # Liste de 7 valeurs
        'valeurs_fixes': valeurs_fixes,
        'params': st.session_state.optim_params.copy()
    }


def sauvegarder_resultat_optimisation(resultat: Dict[str, Any]):
    """
    Sauvegarde les résultats de l'optimisation dans le session state.
    
    Args:
        resultat: Résultats de l'optimisation
    """
    st.session_state.optim_dernier_resultat = resultat


def mettre_a_jour_valeurs_courantes_avec_resultat(resultat: Dict[str, Any]):
    """
    Met à jour les valeurs courantes avec les résultats d'optimisation.
    
    Args:
        resultat: Résultats de l'optimisation
    """
    # Mapping des clés de résultat vers les clés du session state
    mapping_cles = {
        'capital_av_opt': 'capital_av',
        'capital_per_opt': 'capital_per',
        'capital_scpi_opt': 'capital_scpi',
        'versement_av_opt': 'versement_av',
        'versement_per_opt': 'versement_per',
        'versement_scpi_opt': 'versement_scpi',
        'credit_scpi_montant_opt': 'credit_scpi_montant'
    }
    
    for cle_resultat, cle_session in mapping_cles.items():
        if cle_resultat in resultat:
            st.session_state.optim_current_values[cle_session] = resultat[cle_resultat]


def obtenir_parametres_interface() -> Dict[str, Any]:
    """
    Retourne les paramètres actuels de l'interface.
    
    Returns:
        Dictionnaire avec tous les paramètres de l'interface
    """
    return {
        'params': st.session_state.optim_params,
        'current_values': st.session_state.optim_current_values,
        'activer_vars': st.session_state.optim_activer_vars,
        'dernier_resultat': st.session_state.optim_dernier_resultat
    }


def reinitialiser_valeurs_defaut():
    """
    Remet les valeurs courantes aux valeurs par défaut.
    """
    st.session_state.optim_current_values = st.session_state.optim_default_values.copy()


def valider_coherence_parametres() -> tuple[bool, list[str]]:
    """
    Valide la cohérence des paramètres saisis.
    
    Returns:
        Tuple (est_valide, liste_erreurs)
    """
    erreurs = []
    
    # Vérification que au moins une variable est activée pour l'optimisation
    au_moins_une_variable = any(st.session_state.optim_activer_vars.values())
    if not au_moins_une_variable:
        erreurs.append("Au moins une variable doit être activée pour l'optimisation")
    
    # Vérification des plafonds PER
    versement_per_annuel = st.session_state.optim_current_values['versement_per'] * 12
    if versement_per_annuel > st.session_state.optim_params['plafond_per_annuel']:
        erreurs.append(f"Les versements PER annuels ({versement_per_annuel:,.0f} €) dépassent le plafond autorisé ({st.session_state.optim_params['plafond_per_annuel']:,.0f} €)")
    
    # Vérification des valeurs négatives
    for key, value in st.session_state.optim_current_values.items():
        if value < 0:
            erreurs.append(f"La valeur de {key} ne peut pas être négative")
    
    return len(erreurs) == 0, erreurs


def obtenir_resume_configuration() -> Dict[str, Any]:
    """
    Retourne un résumé de la configuration actuelle.
    
    Returns:
        Dictionnaire avec le résumé de la configuration
    """
    variables_activees = [k for k, v in st.session_state.optim_activer_vars.items() if v]
    variables_fixees = [k for k, v in st.session_state.optim_activer_vars.items() if not v]
    
    return {
        'variables_activees': variables_activees,
        'variables_fixees': variables_fixees,
        'nb_variables_activees': len(variables_activees),
        'nb_variables_fixees': len(variables_fixees),
        'plafond_per_annuel': st.session_state.optim_params['plafond_per_annuel'],
        'duree_simulation': st.session_state.optim_params['duree_annees']
    }


def valider_coherence_parametres() -> tuple[bool, list[str]]:
    """
    Valide la cohérence des paramètres saisis exactement comme l'original.
    
    Returns:
        Tuple (est_valide, liste_erreurs)
    """
    erreurs = []
    
    # Vérification que au moins une variable est activée pour l'optimisation
    au_moins_une_variable = any(st.session_state.optim_activer_vars.values())
    if not au_moins_une_variable:
        erreurs.append("Au moins une variable doit être activée pour l'optimisation")
    
    # Vérification des plafonds PER
    versement_per_annuel = st.session_state.optim_current_values['versement_per'] * 12
    if versement_per_annuel > st.session_state.optim_params['plafond_per_annuel']:
        erreurs.append(f"Les versements PER annuels ({versement_per_annuel:,.0f} €) dépassent le plafond autorisé ({st.session_state.optim_params['plafond_per_annuel']:,.0f} €)")
    
    # Vérification des valeurs négatives
    for key, value in st.session_state.optim_current_values.items():
        if value < 0:
            erreurs.append(f"La valeur de {key} ne peut pas être négative")
    
    return len(erreurs) == 0, erreurs