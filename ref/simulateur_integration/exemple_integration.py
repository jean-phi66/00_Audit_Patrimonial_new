"""
Exemple d'intégration du simulateur dans une autre application Streamlit
"""

import streamlit as st
import sys
import os

# Ajouter le chemin du simulateur à sys.path
# Adaptez ce chemin selon votre structure de projet
simulateur_path = os.path.join(os.path.dirname(__file__), 'simulateur_integration')
sys.path.insert(0, simulateur_path)

# Import des modules du simulateur
from config import initialiser_session_state
from ui_components import (
    afficher_sidebar_parametres,
    afficher_metriques_principales,
    afficher_graphique_waterfall,
    afficher_tableau_resultats_actifs
)
from simulation_financiere import maximiser_solde_final_avec_contrainte

def page_simulateur():
    """Page complète du simulateur intégrée dans votre app"""
    
    st.header("🏦 Simulateur d'Investissement Financier")
    st.markdown("---")
    
    # Initialisation du session state (obligatoire)
    initialiser_session_state()
    
    # Affichage de la sidebar et récupération des paramètres
    parametres = afficher_sidebar_parametres()
    
    # Bouton d'optimisation
    col1, col2 = st.columns([1, 4])
    
    with col1:
        if st.button("🚀 Optimiser", type="primary", use_container_width=True):
            st.session_state['optimisation_demandee'] = True
    
    with col2:
        if st.button("🔄 Réinitialiser", use_container_width=True):
            # Reset des valeurs
            for key in st.session_state:
                if key.startswith(('patrimoine_', 'revenus_', 'charges_')):
                    del st.session_state[key]
            st.rerun()
    
    # Traitement de l'optimisation
    if st.session_state.get('optimisation_demandee', False):
        with st.spinner("Optimisation en cours..."):
            try:
                # Lancement de l'optimisation
                resultat = maximiser_solde_final_avec_contrainte(
                    patrimoine_initial=parametres['patrimoine_initial'],
                    revenus_mensuels_nets=parametres['revenus_mensuels_nets'],
                    charges_mensuelles=parametres['charges_mensuelles'],
                    duree_simulation=parametres['duree_simulation'],
                    taux_rendement_annuel=parametres['taux_rendement_annuel'],
                    inflation_annuelle=parametres['inflation_annuelle'],
                    contrainte_cash_minimum=parametres.get('contrainte_cash_minimum', 10000),
                    options_avancees=parametres.get('options_avancees', {})
                )
                
                # Affichage des résultats
                if resultat.get('success', False):
                    st.success("✅ Optimisation réussie !")
                    
                    # Métriques principales
                    afficher_metriques_principales(resultat)
                    
                    # Graphique waterfall
                    st.markdown("### 📊 Évolution du patrimoine")
                    afficher_graphique_waterfall(resultat)
                    
                    # Tableau détaillé
                    st.markdown("### 📋 Répartition par type d'actif")
                    afficher_tableau_resultats_actifs(resultat)
                    
                else:
                    st.error(f"❌ Échec de l'optimisation : {resultat.get('message', 'Erreur inconnue')}")
                    
            except Exception as e:
                st.error(f"❌ Erreur lors de l'optimisation : {str(e)}")
            
            finally:
                # Reset du flag d'optimisation
                st.session_state['optimisation_demandee'] = False

def main():
    """Application principale - Exemple d'intégration"""
    
    st.set_page_config(
        page_title="Mon App avec Simulateur",
        page_icon="💼",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Menu de navigation de votre app principale
    pages = {
        "🏠 Accueil": page_accueil,
        "🏦 Simulateur": page_simulateur,
        "📊 Autres fonctionnalités": page_autres
    }
    
    # Sidebar pour navigation
    with st.sidebar:
        st.title("Navigation")
        page_selectionnee = st.selectbox("Choisir une page", list(pages.keys()))
    
    # Affichage de la page sélectionnée
    pages[page_selectionnee]()

def page_accueil():
    """Page d'accueil de votre application"""
    st.title("🏠 Bienvenue dans mon application")
    st.write("Cette application intègre le simulateur d'investissement financier.")
    st.write("Utilisez le menu de navigation pour accéder aux différentes fonctionnalités.")

def page_autres():
    """Autres fonctionnalités de votre application"""
    st.title("📊 Autres fonctionnalités")
    st.write("Ici vous pouvez ajouter d'autres fonctionnalités de votre application.")

if __name__ == "__main__":
    main()