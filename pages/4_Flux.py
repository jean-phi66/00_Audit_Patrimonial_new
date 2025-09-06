import streamlit as st
import pandas as pd

from core.flux_logic import sync_all_flux_data
from core.flux_display import (
    display_revenus_ui,
    display_depenses_ui,
    display_summary
)

# --- Exécution Principale ---

st.title("🌊 Flux Mensuels (Revenus & Dépenses)")
st.markdown("Renseignez ici vos revenus et vos dépenses mensuelles pour calculer votre capacité d'épargne.")

# --- Options dans la sidebar ---
st.sidebar.header("⚙️ Options")
if 'auto_ir_enabled' not in st.session_state:
    st.session_state.auto_ir_enabled = True

auto_ir_enabled = st.sidebar.checkbox(
    "🏛️ Calcul automatique de l'impôt sur le revenu", 
    value=st.session_state.auto_ir_enabled,
    help="Si activé, l'impôt sur le revenu est calculé automatiquement en fonction des salaires et revenus fonciers."
)
st.session_state.auto_ir_enabled = auto_ir_enabled

if not auto_ir_enabled:
    st.sidebar.info("💡 Le calcul automatique de l'IR est désactivé. Vous pouvez l'ajouter manuellement dans les dépenses.")

if 'parents' not in st.session_state or not st.session_state.parents or not st.session_state.parents[0].get('prenom'):
    st.warning("⚠️ Veuillez d'abord renseigner les informations du foyer dans la page **1_Famille**.")
    st.stop()

sync_all_flux_data()

col1, col2 = st.columns(2)
with col1:
    display_revenus_ui()
with col2:
    display_depenses_ui()

display_summary()

# --- Table détaillée des flux ---
st.markdown("---")
st.subheader("📊 Détail des Flux Mensuels")

# Création des données pour la table
revenus_data = []
depenses_data = []

# Récupération des données de revenus depuis session_state (liste d'objets)
if 'revenus' in st.session_state and isinstance(st.session_state.revenus, list):
    for revenu in st.session_state.revenus:
        montant = revenu.get('montant', 0)
        if montant > 0:
            # Déterminer le type et la personne
            type_revenu = revenu.get('type', 'Autre')
            libelle = revenu.get('libelle', 'N/A')
            
            if type_revenu == 'Salaire':
                # Extraire le prénom du libellé "Salaire Prénom"
                personne = libelle.replace('Salaire ', '') if 'Salaire ' in libelle else 'N/A'
                revenus_data.append({'Type': 'Salaire', 'Personne': personne, 'Montant': montant})
            elif type_revenu == 'Patrimoine':
                revenus_data.append({'Type': 'Patrimoine', 'Personne': 'Foyer', 'Montant': montant, 'Détail': libelle})
            else:
                revenus_data.append({'Type': type_revenu, 'Personne': 'Foyer', 'Montant': montant, 'Détail': libelle})

# Récupération des données de dépenses depuis session_state (liste d'objets)
if 'depenses' in st.session_state and isinstance(st.session_state.depenses, list):
    for depense in st.session_state.depenses:
        montant = depense.get('montant', 0)
        if montant > 0:
            categorie = depense.get('categorie', 'Autres')
            libelle = depense.get('libelle', 'N/A')
            
            depenses_data.append({'Catégorie': categorie, 'Montant': montant, 'Détail': libelle})

# Debug - Afficher la structure des données si nécessaire
if st.checkbox("🔍 Debug - Afficher la structure des données"):
    st.write("**Structure de revenus:**", type(st.session_state.get('revenus')))
    if 'revenus' in st.session_state:
        st.write(st.session_state.revenus)
    st.write("**Structure de dépenses:**", type(st.session_state.get('depenses')))
    if 'depenses' in st.session_state:
        st.write(st.session_state.depenses)

# Affichage des tables
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 💰 Revenus")
    if revenus_data:
        df_revenus = pd.DataFrame(revenus_data)
        # Calcul du total avant formatage
        total_revenus = df_revenus['Montant'].sum()
        # Formatage pour affichage
        df_revenus['Montant'] = df_revenus['Montant'].apply(lambda x: f"{x:,.0f} €".replace(',', ' '))
        st.dataframe(df_revenus, use_container_width=True, hide_index=True)
        st.markdown(f"**Total revenus : {total_revenus:,.0f} €**".replace(',', ' '))
    else:
        st.info("Aucun revenu renseigné")

with col2:
    st.markdown("### 💸 Charges")
    if depenses_data:
        df_charges = pd.DataFrame(depenses_data)
        # Calcul du total avant formatage
        total_charges = df_charges['Montant'].sum()
        # Formatage pour affichage
        df_charges['Montant'] = df_charges['Montant'].apply(lambda x: f"{x:,.0f} €".replace(',', ' '))
        st.dataframe(df_charges, use_container_width=True, hide_index=True)
        st.markdown(f"**Total charges : {total_charges:,.0f} €**".replace(',', ' '))
    else:
        st.info("Aucune charge renseignée")

# Calcul et affichage de la capacité d'épargne
if revenus_data and depenses_data:
    # Recalcul des totaux avec les valeurs numériques originales
    total_revenus_num = sum([item['Montant'] for item in revenus_data])
    total_charges_num = sum([item['Montant'] for item in depenses_data])
    capacite_epargne = total_revenus_num - total_charges_num
    
    st.markdown("---")
    if capacite_epargne > 0:
        st.success(f"💰 **Capacité d'épargne mensuelle : {capacite_epargne:,.0f} €**".replace(',', ' '))
    elif capacite_epargne < 0:
        st.error(f"⚠️ **Déficit mensuel : {abs(capacite_epargne):,.0f} €**".replace(',', ' '))
    else:
        st.info("**Équilibre parfait : 0 €**")

