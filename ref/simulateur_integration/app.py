"""
Interface Streamlit pour le simulateur d'investissement financier
Version 2.0 - Interface refactorisée avec modules séparés
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Import des modules locaux
from simulation_financiere import maximiser_solde_final_avec_contrainte
from config import (
    initialiser_session_state, 
    mettre_a_jour_parametres_sidebar,
    mettre_a_jour_variables_optimisation,
    preparer_parametres_optimisation,
    sauvegarder_resultat_optimisation,
    mettre_a_jour_valeurs_courantes_avec_resultat,
    valider_coherence_parametres
)
from ui_components import (
    afficher_sidebar_parametres,
    afficher_variables_optimisation,
    afficher_parametres_avances,
    afficher_metriques_principales,
    afficher_messages_contraintes,
    afficher_tableau_resultats_actifs,
    afficher_details_complementaires,
    afficher_graphique_waterfall,
    afficher_detail_complet_parametres,
    afficher_simulation_detaillee
)

# Configuration de la page
st.set_page_config(
    page_title="Simulateur d'Investissement Financier",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Titre principal
st.title("💰 Simulateur d'Investissement Financier")
st.markdown("---")

# Initialisation du session state
initialiser_session_state()

# Affichage de la sidebar et récupération des paramètres
parametres_sidebar = afficher_sidebar_parametres()
mettre_a_jour_parametres_sidebar(parametres_sidebar)

# Interface principale - Variables d'optimisation
variables_info = afficher_variables_optimisation()
mettre_a_jour_variables_optimisation(variables_info)

# Paramètres avancés
afficher_parametres_avances()

# Validation des paramètres
st.markdown("---")
parametres_valides, erreurs = valider_coherence_parametres()

if not parametres_valides:
    st.error("⚠️ **Erreurs de configuration détectées :**")
    for erreur in erreurs:
        st.write(f"• {erreur}")
    st.stop()

# Bouton d'optimisation
st.markdown("---")
col_bouton, col_info = st.columns([1, 2])

with col_bouton:
    if st.button("🚀 Lancer l'optimisation", type="primary"):
        # Préparation des paramètres d'optimisation
        params_optim = preparer_parametres_optimisation(parametres_sidebar)
        
        if not any(params_optim['activer_vars']):
            st.error("❌ Aucune variable sélectionnée pour l'optimisation")
        else:
            # Lancement de l'optimisation
            with st.spinner("Optimisation en cours..."):
                try:
                    resultat_optimisation = maximiser_solde_final_avec_contrainte(
                        params_optim['params'],
                        params_optim['effort_max'],
                        mensualite_max=params_optim['mensualite_max'],
                        capital_initial_max=params_optim['capital_initial_max'],
                        activer_vars=params_optim['activer_vars'],
                        valeurs_defaut=params_optim['valeurs_defaut']
                    )
                    
                    # Sauvegarde du résultat
                    sauvegarder_resultat_optimisation(resultat_optimisation)
                    
                    # Mise à jour des valeurs courantes avec les résultats d'optimisation
                    mettre_a_jour_valeurs_courantes_avec_resultat(resultat_optimisation)
                    
                    st.success("✅ Optimisation terminée avec succès!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Erreur lors de l'optimisation : {str(e)}")

with col_info:
    if st.session_state.dernier_resultat is None:
        st.info("👆 Configurez les paramètres et cliquez sur 'Lancer l'optimisation' pour voir les résultats.")

# Affichage des résultats
if st.session_state.dernier_resultat is not None:
    st.markdown("---")
    st.header("📊 Résultats d'optimisation")
    
    # Métriques principales
    afficher_metriques_principales(st.session_state.dernier_resultat)
    
    # Messages de contraintes
    afficher_messages_contraintes(st.session_state.dernier_resultat)
    
    # Tableau des résultats par actif
    donnees_actifs = afficher_tableau_resultats_actifs(
        st.session_state.dernier_resultat, 
        st.session_state.params
    )
    
    # Détails complémentaires
    afficher_details_complementaires(donnees_actifs, st.session_state.params)
    
    # Simulation détaillée avec paramètres optimaux
    afficher_simulation_detaillee(st.session_state.dernier_resultat)
    
    # Détail complet des paramètres
    afficher_detail_complet_parametres(st.session_state.dernier_resultat)
    
    # Graphique waterfall
    afficher_graphique_waterfall(st.session_state.dernier_resultat)