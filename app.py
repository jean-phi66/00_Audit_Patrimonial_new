import streamlit as st
from collections import OrderedDict

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

# --- Configuration des pages et de leur ordre ---

page_config = OrderedDict({
    "Accueil": None,  # Page d'accueil, pas besoin de fichier dédié
    "👪 Foyer": {
        "1_Famille": "Composition du foyer",
    },
    "🏛️ Patrimoine": {
        "2_Patrimoine": "Détail du patrimoine",
    },
    "💸 Flux": {
        "4_Flux": "Flux mensuels (revenus & dépenses)",
    },
    "🔎 Analyse": {
        "7_Capacite_Endettement": "Capacité d'endettement",
        "4_Projection": "Projection des grandes étapes de vie",
        "3_Focus_Immobilier": "Focus immobilier locatif",
        "8_Focus_Fiscalite": "Focus fiscalité",
    },
    "📄 Rapport": {
        "6_Rapport": "Génération de rapport PDF",
    },
    "🛠️ Outils": {
        "5_Sauvegarde_et_Chargement": "Sauvegarde et chargement des données",
        "99_Debug": "Debug - Session State",
    },
})


accueil_page = st.Page("pages/0_Accueil.py", title="👋🏽 Accueil")#, icon=":material/home:")
load_save_page = st.Page("pages/5_Sauvegarde_et_Chargement.py", title="💾 Sauvegarde et chargement")#, icon=":material/save:")

famille_page = st.Page("pages/1_Famille.py", title="🧑‍🧑‍🧒‍🧒 Composition du foyer")#, icon=":material/group:")#, icon=":material/add_circle:")
patrimoine_page = st.Page("pages/2_Patrimoine.py", title="💰 Description du patrimoine")#, icon=":material/attach_money:")
flux_page = st.Page("pages/4_Flux.py", title="💸  Flux : revenus & dépenses")#, icon=":material/monetization_on:")

immobilier_page = st.Page("pages/3_Focus_Immobilier.py", title="🏘️ Focus Immobilier")#, icon=":material/house:")
fiscalite_page = st.Page("pages/8_Focus_Fiscalite.py", title="🧐Focus Fiscalité")#, icon=":material/monetization_on:")
projection_page = st.Page("pages/4_Projection.py", title="📈 Projection")#, icon=":material/calendar_today:")
#create_page = st.Page("pages/3_Flux.py", title="Delete entry", icon=":material/delete:")

pg = st.navigation({'Fichier':[accueil_page,  load_save_page],
                   'Informations du Foyer': [famille_page, patrimoine_page, flux_page],
                   'Analyse': [immobilier_page, fiscalite_page],
                   'Projection': [projection_page]})
#st.set_page_config(page_title="Data manager", page_icon=":material/edit:")
pg.run()
