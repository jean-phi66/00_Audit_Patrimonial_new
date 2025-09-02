import streamlit as st
import os
import sys

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

pg = st.navigation(
    {
        "Fichier": [
            st.Page("pages/0_Accueil.py", title="Accueil", icon="🏠"),
            st.Page("pages/5_Sauvegarde_et_Chargement.py", title="Sauvegarde et chargement", icon="💾"),
            st.Page("pages/6_Rapport.py", title="Rapport PDF", icon="📄"),
        ],
        "Informations du Foyer": [
            st.Page("pages/1_Famille.py", title="Composition du foyer", icon="🧑‍🧑‍🧒‍🧒"),
            st.Page("pages/2_Patrimoine.py", title="Description du patrimoine", icon="💰"),
            st.Page("pages/4_Flux.py", title="Flux : revenus & dépenses", icon="💸"),
        ],
        "Analyse": [
            st.Page("pages/3_Focus_Immobilier.py", title="Focus Immobilier", icon="🏘️"),
            st.Page("pages/8_Focus_Fiscalite.py", title="Focus Fiscalité", icon="🧐"),
            st.Page("pages/7_Capacite_Endettement.py", title="Capacité d'endettement", icon="🏦"),
        ],
        "Projection": [
            st.Page("pages/4_Projection.py", title="Projection", icon="📈"),
        ],
        "Solutions": [
            st.Page("pages/9_Optimisation_PER.py", title="Optimisation PER", icon="🎯"),
            st.Page("pages/8_Simulation_Manuelle.py", title="Simulation Manuelle", icon="🕹️"),
            st.Page("pages/9_Optimisation_Patrimoniale.py", title="Optimisation Globale", icon="💫"),
        ],
        "Outils": [
            st.Page("pages/99_Debug.py", title="Debug - Session State", icon="🐛"),
        ]
    }, position='top'
)
pg.run()
