import streamlit as st
from datetime import date

import sys
import os
# Add project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


try:
    # Tentative d'import de la fonction à tester
    from utils.openfisca_utils import calculer_impot_openfisca
    OPENFISCA_UTILITY_AVAILABLE = True
except ImportError as e:
    OPENFISCA_UTILITY_AVAILABLE = False
    # Store the specific error for more informative messages
    st.session_state.openfisca_import_error = str(e)
    
st.set_page_config(layout="wide")

st.title("🐛 Debug - Session State")

st.markdown(
    """
    Cette page affiche le contenu complet de `st.session_state` à des fins de débogage.
    Cela vous permet de voir toutes les données qui sont actuellement stockées et partagées entre les pages de l'application.
    """
)

st.write("---")

if not st.session_state:
    st.info("Le `session_state` est actuellement vide.")
else:
    st.header("Contenu actuel du `session_state` :")
    st.json(st.session_state)

st.write("---")

# --- Section de test pour la fonction de calcul d'impôt ---
st.header("🧪 Test du calcul d'impôt (OpenFisca)")

if not OPENFISCA_UTILITY_AVAILABLE:
    error_msg = st.session_state.get('openfisca_import_error', "Erreur inconnue.")
    st.error(
        "**La fonction `calculer_impot_openfisca` n'a pas pu être importée.**\n\n"
        f"**Erreur technique :** `{error_msg}`\n\n"
        "Cela est souvent dû à une dépendance manquante. Assurez-vous d'avoir installé `openfisca-france`:\n"
        "`pip install openfisca-france`"
    )
elif 'parents' not in st.session_state or not st.session_state.parents:
    st.warning("Veuillez d'abord renseigner les informations du foyer dans la page **1_Famille** pour pouvoir tester le calcul d'impôt.")
else:
    st.markdown("Utilisez ce formulaire pour tester la fonction `calculer_impot_openfisca` avec les données du foyer.")
    
    with st.form("test_openfisca_form"):
        test_annee = st.number_input("Année de simulation", min_value=2000, max_value=date.today().year + 10, value=date.today().year)
        
        test_revenus = {}
        st.subheader("Revenus annuels pour le test")
        for parent in st.session_state.parents:
            prenom = parent.get('prenom')
            if prenom:
                test_revenus[prenom] = st.number_input(f"Revenu de {prenom}", min_value=0, value=50000, step=1000, key=f"debug_rev_{prenom}")

        st.subheader("Revenus fonciers pour le test")
        test_revenu_foncier_net = st.number_input("Revenu foncier net imposable", min_value=0, value=9000, step=500)

        test_parent_isole = st.checkbox("Le foyer est-il monoparental (coche la case T) ?")

        submitted = st.form_submit_button("Lancer le calcul d'impôt de test")

    if submitted:
        with st.spinner("Calcul en cours..."):
            parents_data = st.session_state.get('parents', [])
            enfants_data = st.session_state.get('enfants', [])

            impot_calcule = calculer_impot_openfisca(
                annee=test_annee,
                parents=parents_data,
                enfants=enfants_data,
                revenus_annuels=test_revenus,
                revenu_foncier_net=test_revenu_foncier_net,
                est_parent_isole=test_parent_isole
            )

            st.success(f"**Impôt net calculé pour {test_annee} : {impot_calcule:,.2f} €**")

            with st.expander("Voir les données envoyées à la fonction `calculer_impot_openfisca`"):
                st.json({
                    "annee": test_annee,
                    "parents": parents_data,
                    "enfants": enfants_data,
                    "revenus_annuels": test_revenus,
                    "revenu_foncier_net": test_revenu_foncier_net,
                    "est_parent_isole": test_parent_isole
                })