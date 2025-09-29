"""
Module d'intégration du Simulateur d'Investissement Financier

Ce module permet d'intégrer facilement le simulateur dans une autre application Streamlit.
"""

# Import des principales fonctions pour faciliter l'utilisation
from .simulation_financiere import maximiser_solde_final_avec_contrainte, calculer_simulation_mensuelle
from .config import initialiser_session_state, preparer_parametres_optimisation
from .ui_components import (
    afficher_sidebar_parametres,
    afficher_metriques_principales,
    afficher_graphique_waterfall,
    afficher_tableau_resultats_actifs
)

__version__ = "2.0.0"
__author__ = "Simulateur d'Investissement Financier"

# Facilite l'import : from simulateur_integration import *
__all__ = [
    'maximiser_solde_final_avec_contrainte',
    'calculer_simulation_mensuelle', 
    'initialiser_session_state',
    'preparer_parametres_optimisation',
    'afficher_sidebar_parametres',
    'afficher_metriques_principales',
    'afficher_graphique_waterfall',
    'afficher_tableau_resultats_actifs'
]