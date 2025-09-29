import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from typing import Dict, Any

try:
    # Import des modules du simulateur intégrés
    from core.optim_simulation_financiere import maximiser_solde_final_avec_contrainte
    from core.optim_config import (
        initialiser_session_state as init_sim_session,
        preparer_parametres_optimisation,
        mettre_a_jour_variables_optimisation,
        mettre_a_jour_parametres_sidebar,
        sauvegarder_resultat_optimisation,
        mettre_a_jour_valeurs_courantes_avec_resultat,
        valider_coherence_parametres
    )
    from core.optim_ui_components import (
        afficher_sidebar_parametres,
        afficher_variables_optimisation,
        afficher_messages_contraintes,
        afficher_tableau_resultats_actifs,
        afficher_graphique_waterfall,
        afficher_simulation_detaillee,
        afficher_parametres_avances,
        afficher_details_complementaires,
        afficher_detail_complet_parametres
    )
    from core.tri_patch import afficher_metriques_principales_avec_tri
    from core.optim_calculations import (
        calculer_donnees_tableau_actifs,
        calculer_statistiques_simulation
    )
    
    simulateur_available = True
except ImportError as e:
    st.error(f"❌ Erreur d'importation du simulateur : {e}")
    simulateur_available = False

# --- Configuration de la page ---
st.title("🎯 Optimisation Patrimoniale")
st.markdown("""
Cette page vous permet d'optimiser votre allocation d'investissement entre **Assurance-Vie**, **PER** et **SCPI** 
en utilisant un algorithme d'optimisation avancé.
""")

if not simulateur_available:
    st.error("⚠️ Le simulateur d'optimisation n'est pas disponible. Veuillez vérifier l'installation des modules.")
    st.stop()

# --- Vérification des prérequis ---
if 'parents' not in st.session_state or not st.session_state.parents or not st.session_state.parents[0].get('prenom'):
    st.warning("⚠️ Veuillez d'abord renseigner les informations du foyer dans la page **1_Famille**.")
    st.stop()

# --- Initialisation du simulateur ---
try:
    # Initialisation du simulateur avec préfixage des clés
    if 'optim_params_initialized' not in st.session_state:
        init_sim_session()
        
        # Récupération des données du foyer si disponibles
        if hasattr(st.session_state, 'parents') and st.session_state.parents:
            parent = st.session_state.parents[0]
            if 'tmi' in parent:
                st.session_state.optim_params['tmi'] = parent.get('tmi', 30) / 100  # Conversion en décimal
                
        st.success("✅ Simulateur d'optimisation initialisé avec succès")
    
except Exception as e:
    st.error(f"❌ Erreur lors de l'initialisation : {e}")
    st.stop()

# --- Interface principale exactement comme l'original ---

# Affichage de la sidebar et récupération des paramètres
parametres_sidebar = afficher_sidebar_parametres()
mettre_a_jour_parametres_sidebar(parametres_sidebar)

# Interface principale - Variables d'optimisation
variables_info = afficher_variables_optimisation()
mettre_a_jour_variables_optimisation(variables_info)

# Paramètres avancés
afficher_parametres_avances()

# Validation des paramètres
parametres_valides, erreurs = valider_coherence_parametres()

if not parametres_valides:
    st.error("⚠️ **Erreurs de configuration détectées :**")
    for erreur in erreurs:
        st.write(f"• {erreur}")
    st.stop()

# Bouton d'optimisation
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
    if st.session_state.optim_dernier_resultat is None:
        st.info("👆 Configurez les paramètres et cliquez sur 'Lancer l'optimisation' pour voir les résultats.")

# Affichage des résultats
if st.session_state.optim_dernier_resultat is not None:
    st.header("📊 Résultats d'optimisation")
    
    # Métriques principales
    afficher_metriques_principales_avec_tri(st.session_state.optim_dernier_resultat)
    
    # Messages de contraintes
    afficher_messages_contraintes(st.session_state.optim_dernier_resultat)
    
    # Tableau des résultats par actif
    donnees_actifs = afficher_tableau_resultats_actifs(
        st.session_state.optim_dernier_resultat, 
        st.session_state.optim_params
    )
    
    # Détails complémentaires
    afficher_details_complementaires(donnees_actifs, st.session_state.optim_params)
    
    # Simulation détaillée avec paramètres optimaux
    afficher_simulation_detaillee(st.session_state.optim_dernier_resultat)
    
    # Détail complet des paramètres
    afficher_detail_complet_parametres(st.session_state.optim_dernier_resultat)
    
    # Graphique waterfall
    afficher_graphique_waterfall(st.session_state.optim_dernier_resultat)

# --- Informations complémentaires ---
with st.expander("ℹ️ À propos de l'optimisation"):
    st.markdown("""
    ### Comment fonctionne l'optimisation ?
    
    L'algorithme d'optimisation utilise des méthodes numériques avancées pour :
    - **Maximiser** votre patrimoine final sur la période choisie
    - **Respecter** vos contraintes d'épargne et d'endettement
    - **Optimiser** la répartition fiscale entre AV, PER et SCPI
    - **Intégrer** les effets du crédit SCPI et des avantages fiscaux
    
    ### Variables optimisables :
    - **Capitaux initiaux** : AV, PER, SCPI
    - **Versements mensuels** : AV, PER, SCPI  
    - **Montant du crédit SCPI**
    
    ### Contraintes prises en compte :
    - Effort d'épargne maximal mensuel
    - Mensualité crédit SCPI maximale
    - Capital initial maximal disponible
    - Plafond annuel PER
    - Tranche marginale d'imposition (TMI)
    """)

# --- Debug et informations techniques ---
if st.checkbox("🔧 Mode développeur"):
    st.markdown("### État du session state (simulateur)")
    debug_keys = [k for k in st.session_state.keys() if any(x in k.lower() for x in ['optim_', 'dernier_', 'activer_'])]
    for key in debug_keys:
        st.write(f"**{key}:** {st.session_state.get(key)}")