"""
Guide de démarrage rapide pour l'intégration du simulateur

Ce fichier montre les différentes façons d'utiliser le simulateur dans votre app.
"""

import streamlit as st
import sys
import os

# Configuration du chemin d'import
def setup_simulateur_path():
    """Configure le chemin pour importer les modules du simulateur"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    simulateur_dir = os.path.join(current_dir, 'simulateur_integration')
    
    if simulateur_dir not in sys.path:
        sys.path.insert(0, simulateur_dir)

# Configuration à appeler une seule fois au début de votre app
setup_simulateur_path()

# ============================================================================
# METHODE 1 : Intégration complète (recommandée)
# ============================================================================

def integration_complete():
    """
    Intégration complète du simulateur avec tous ses composants.
    Idéal pour une page dédiée dans votre application.
    """
    from config import initialiser_session_state
    from ui_components import afficher_sidebar_parametres, afficher_metriques_principales
    from simulation_financiere import maximiser_solde_final_avec_contrainte
    
    st.header("🏦 Simulateur d'Investissement")
    
    # OBLIGATOIRE : Initialiser le session state
    initialiser_session_state()
    
    # Interface utilisateur automatique
    parametres = afficher_sidebar_parametres()
    
    # Bouton d'optimisation
    if st.button("Optimiser le portefeuille"):
        with st.spinner("Calcul en cours..."):
            resultat = maximiser_solde_final_avec_contrainte(**parametres)
            afficher_metriques_principales(resultat)

# ============================================================================
# METHODE 2 : Intégration modulaire (pour usage personnalisé)
# ============================================================================

def integration_modulaire():
    """
    Utilise seulement certains composants du simulateur.
    Permet de personnaliser l'interface selon vos besoins.
    """
    from simulation_financiere import maximiser_solde_final_avec_contrainte
    from ui_components import afficher_graphique_waterfall
    
    st.header("Mon Simulateur Personnalisé")
    
    # Vos propres composants d'interface
    col1, col2 = st.columns(2)
    
    with col1:
        patrimoine = st.number_input("Patrimoine initial (€)", value=50000)
        revenus = st.number_input("Revenus mensuels nets (€)", value=3000)
    
    with col2:
        charges = st.number_input("Charges mensuelles (€)", value=2000)
        duree = st.slider("Durée (années)", 1, 30, 10)
    
    if st.button("Calculer"):
        # Utilisation du moteur de calcul
        resultat = maximiser_solde_final_avec_contrainte(
            patrimoine_initial=patrimoine,
            revenus_mensuels_nets=revenus,
            charges_mensuelles=charges,
            duree_simulation=duree
        )
        
        # Affichage avec les composants du simulateur
        if resultat.get('success'):
            st.success(f"Patrimoine final optimisé : {resultat['patrimoine_final']:,.0f} €")
            afficher_graphique_waterfall(resultat)

# ============================================================================
# METHODE 3 : Utilisation des fonctions de calcul seulement
# ============================================================================

def calculs_seulement():
    """
    Utilise seulement le moteur de calcul sans interface.
    Idéal pour intégrer dans votre logique métier existante.
    """
    from simulation_financiere import maximiser_solde_final_avec_contrainte, calculer_simulation_mensuelle
    
    st.header("Calculs d'investissement")
    
    # Paramètres fixes ou calculés par votre logique
    parametres = {
        'patrimoine_initial': 100000,
        'revenus_mensuels_nets': 4000,
        'charges_mensuelles': 2500,
        'duree_simulation': 15,
        'taux_rendement_annuel': 0.07,
        'inflation_annuelle': 0.02
    }
    
    if st.button("Analyser"):
        # Optimisation
        resultat_opti = maximiser_solde_final_avec_contrainte(**parametres)
        
        # Simulation détaillée
        simulation = calculer_simulation_mensuelle(**parametres)
        
        # Affichage personnalisé
        st.metric("Patrimoine final", f"{resultat_opti.get('patrimoine_final', 0):,.0f} €")
        st.metric("Rendement annuel moyen", f"{resultat_opti.get('rendement_moyen', 0)*100:.1f}%")
        
        # Graphique simple avec vos données
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            y=[m['patrimoine_total'] for m in simulation[:120]],  # 10 ans
            name="Évolution patrimoine"
        ))
        st.plotly_chart(fig)

# ============================================================================
# EXEMPLE D'APPLICATION MULTI-PAGES
# ============================================================================

def app_exemple():
    """Exemple d'application complète avec navigation"""
    
    st.set_page_config(
        page_title="Mon App Financière",
        page_icon="💰",
        layout="wide"
    )
    
    # Navigation
    pages = {
        "🏠 Accueil": lambda: st.write("Bienvenue dans votre app !"),
        "🏦 Simulateur Complet": integration_complete,
        "⚙️ Calculateur Personnalisé": integration_modulaire,
        "📊 Analyses Rapides": calculs_seulement
    }
    
    with st.sidebar:
        st.title("Navigation")
        page = st.selectbox("Choisir une page", list(pages.keys()))
    
    # Affichage de la page
    pages[page]()

# ============================================================================
# LANCEMENT
# ============================================================================

if __name__ == "__main__":
    # Décommentez la méthode que vous voulez tester :
    
    # app_exemple()           # Application complète avec navigation
    # integration_complete()  # Page simulateur complète
    # integration_modulaire() # Interface personnalisée
    # calculs_seulement()     # Calculs seulement
    
    st.info("""
    ### 🚀 Guide de démarrage rapide
    
    1. **Installation** : `pip install -r requirements.txt`
    2. **Import** : Copiez la fonction `setup_simulateur_path()` dans votre app
    3. **Utilisation** : Choisissez une des 3 méthodes d'intégration ci-dessus
    
    **Méthodes disponibles :**
    - `integration_complete()` : Interface complète avec sidebar
    - `integration_modulaire()` : Composants personnalisables  
    - `calculs_seulement()` : Moteur de calcul uniquement
    
    Décommentez la méthode souhaitée dans la section LANCEMENT ci-dessus.
    """)