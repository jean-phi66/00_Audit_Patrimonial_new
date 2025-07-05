import streamlit as st

# Configuration de la page principale
st.set_page_config(
    page_title="Audit Patrimonial",
    page_icon="🏠",
    layout="wide"
)

# Initialisation du st.session_state pour stocker les données
# C'est essentiel pour une application multipage afin de conserver les informations
# d'une page à l'autre.

# --- Initialisation pour la famille ---
if 'parents' not in st.session_state:
    # On initialise avec 1 dictionnaire pour le premier parent. Le second est optionnel.
    st.session_state.parents = [
        {'prenom': '', 'date_naissance': None}
    ]
if 'enfants' not in st.session_state:
    # On initialise avec une liste vide pour les enfants
    st.session_state.enfants = []

# --- Initialisation pour le patrimoine ---
if 'actifs' not in st.session_state:
    st.session_state.actifs = []
if 'passifs' not in st.session_state:
    st.session_state.passifs = []

# --- Initialisation pour les flux ---
if 'revenus' not in st.session_state:
    st.session_state.revenus = []
if 'depenses' not in st.session_state:
    st.session_state.depenses = []


# Page d'accueil
st.title("Outil d'Audit Patrimonial 💰")

st.markdown("""
Bienvenue dans votre assistant d'audit patrimonial.

Cette application vous permettra de :
1.  **Définir la composition de votre foyer** (parents et enfants).
2.  **Détailler votre patrimoine** (actifs et passifs).
3.  (Prochainement) **Projeter vos flux financiers** et anticiper les événements clés de votre vie.

**👈 Utilisez le menu de navigation sur la gauche pour commencer.**

---
*Cette application utilisera à terme [OpenFisca-France](https://github.com/openfisca/openfisca-france) pour des calculs de fiscalité précis.*
""")

# Afficher les données actuelles (utile pour le débogage)
with st.expander("Voir les données en cours (pour le développement)"):
    st.write("### Données du Foyer :")
    st.json(st.session_state.parents)
    st.json(st.session_state.enfants)
    st.write("### Données du Patrimoine :")
    st.json(st.session_state.actifs)
    st.json(st.session_state.passifs)
