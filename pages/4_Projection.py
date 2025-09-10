import streamlit as st
from datetime import date

from core.projection_logic import (
    generate_gantt_data,
    generate_financial_projection,
    OPENFISCA_UTILITY_AVAILABLE
)
from core.projection_display import (
    display_settings_ui,
    display_gantt_chart,
    display_loan_crd_chart,
    display_projection_table,
    display_projection_chart,
    display_annual_tax_chart,
    display_cumulative_tax_at_retirement,
    display_retirement_transition_analysis
)

# --- Exécution Principale ---

st.title("🗓️ Projection des grandes étapes de vie")
st.markdown("Définissez les âges clés pour chaque membre du foyer afin de visualiser une frise chronologique de leurs activités.")

if 'parents' not in st.session_state or not st.session_state.parents or not st.session_state.parents[0].get('prenom'):
    st.warning("⚠️ Veuillez d'abord renseigner les informations du foyer dans la page **1_Famille**.")
    st.stop()

if 'projection_settings' not in st.session_state:
    st.session_state.projection_settings = {}

# Initialiser l'état du calcul de projection
if 'projection_calculated' not in st.session_state:
    st.session_state.projection_calculated = False

parents = st.session_state.parents
enfants = st.session_state.enfants

# Barre latérale avec bouton de calcul
with st.sidebar:
    st.header("🚀 Actions")
    
    # Paramètre de durée de projection
    duree_projection = st.number_input(
        "Durée de la projection (années)",
        min_value=1, max_value=50, value=25, step=1,
        help="Nombre d'années à projeter après le départ à la retraite des parents."
    )
    
    st.markdown("---")
    
    # Bouton pour lancer le calcul de projection
    if st.button("🔄 Calculer la Projection", type="primary", use_container_width=True):
        st.session_state.projection_calculated = True
        st.rerun()
    
    # Bouton pour réinitialiser
    if st.button("🗑️ Réinitialiser", use_container_width=True):
        st.session_state.projection_calculated = False
        st.rerun()
    
    if(False):    
        st.markdown("---")
        st.markdown("### 📋 Instructions")
        st.markdown("""
        1. **Ajustez** la durée de projection
        2. **Configurez** les paramètres ci-dessous
        3. **Cliquez** sur "Calculer la Projection"
        4. **Analysez** les résultats obtenus
        """)

settings = display_settings_ui(parents, enfants)

gantt_data = generate_gantt_data(parents, enfants, settings, duree_projection)
display_gantt_chart(gantt_data, duree_projection, parents, enfants)

# Affichage conditionnel de la projection financière
if st.session_state.projection_calculated:
    passifs = st.session_state.get('passifs', [])
    
    # Créer une clé de cache basée sur les paramètres
    import json
    cache_key = json.dumps({
        'duree_projection': duree_projection,
        'settings': settings,
        'passifs_count': len(passifs),
        'parents_count': len(parents),
        'enfants_count': len(enfants)
    }, sort_keys=True)
    
    # Vérifier si les données de projection sont déjà en cache
    if ('projection_cache_key' not in st.session_state or 
        st.session_state.projection_cache_key != cache_key or
        'df_projection' not in st.session_state):
        
        # Recalculer seulement si nécessaire
        with st.spinner("🔄 Calcul de la projection financière en cours..."):
            df_projection = generate_financial_projection(parents, enfants, passifs, settings, duree_projection)
            st.session_state.df_projection = df_projection
            st.session_state.projection_cache_key = cache_key
    else:
        # Utiliser les données en cache
        df_projection = st.session_state.df_projection

    st.header("📈 Projection Financière Annuelle")
    if not OPENFISCA_UTILITY_AVAILABLE:
        error_msg = st.session_state.get('openfisca_import_error', "Erreur inconnue.")
        st.warning(
            "**Le module OpenFisca n'a pas pu être chargé.** Les calculs d'impôts seront des estimations simplifiées (taux forfaitaire de 15%).\n\n"
            f"**Erreur technique :** `{error_msg}`\n\n"
            "Pour un calcul précis, assurez-vous que le package `openfisca-france` est bien installé dans votre environnement."
        )

    if df_projection.empty:
        st.info("Aucune donnée de projection financière à afficher.")
    else:
        with st.expander("Détails de la projection financière"):
            display_projection_table(df_projection)
        display_projection_chart(df_projection)

        # Nouveaux graphiques et métriques pour la fiscalité
        st.markdown("---")
        st.header("🔎 Focus Fiscalité")
        display_annual_tax_chart(df_projection)
        display_cumulative_tax_at_retirement(df_projection, parents, settings)
        
        # Analyse de la transition vers la retraite
        st.markdown("---")
        st.header("🎯 Analyse de la Transition vers la Retraite")
        display_retirement_transition_analysis(df_projection, parents, settings)
        
        st.markdown("---")
        st.header("🔎 Focus Emprunts")
        display_loan_crd_chart(df_projection, passifs)

else:
    st.info("👈 Cliquez sur le bouton **'Calculer la Projection'** dans la barre latérale pour afficher la projection financière.")
    
    # Afficher un aperçu des paramètres configurés
    st.subheader("📋 Résumé des paramètres configurés")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**👨‍👩‍👧 Parents :**")
        for parent in parents:
            prenom = parent.get('prenom')
            if prenom and prenom in st.session_state.projection_settings:
                settings_parent = st.session_state.projection_settings[prenom]
                age_retraite = settings_parent.get('retraite', 64)
                pension = settings_parent.get('pension_annuelle', 25000)
                st.markdown(f"- **{prenom}** : Retraite à {age_retraite} ans, Pension {pension:,.0f}€/an")
    
    with col2:
        st.markdown("**👶 Enfants :**")
        if not enfants:
            st.markdown("- Aucun enfant renseigné")
        else:
            for enfant in enfants:
                prenom = enfant.get('prenom')
                if prenom and prenom in st.session_state.projection_settings:
                    settings_enfant = st.session_state.projection_settings[prenom]
                    fin_etudes = settings_enfant.get('fin_etudes', 25)
                    st.markdown(f"- **{prenom}** : Fin d'études à {fin_etudes} ans")



