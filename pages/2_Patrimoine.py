import streamlit as st
import uuid
from datetime import date
import pandas as pd
import plotly.express as px
from core.patrimoine_logic import calculate_monthly_payment, calculate_crd, get_patrimoine_df, add_item, remove_item

st.title("🏡 Description du Patrimoine")
st.markdown("Listez ici vos actifs (ce que vous possédez) et vos passifs (ce que vous devez).")

# --- Initialisation du Session State ---
# Indispensable sur chaque page pour que l'application fonctionne de manière autonome.
if 'actifs' not in st.session_state:
    st.session_state.actifs = []
if 'passifs' not in st.session_state:
    st.session_state.passifs = []

# --- Data Migration ---
# S'assure que tous les actifs existants ont un UUID.
# Cela gère les données des sessions plus anciennes où le champ 'id' n'existait pas.
for actif in st.session_state.actifs:
    if 'id' not in actif:
        actif['id'] = str(uuid.uuid4())

# --- Data Migration for Passifs ---
# Renomme 'valeur' en 'montant_initial' et ajoute les nouveaux champs de prêt.
for passif in st.session_state.passifs:
    if 'valeur' in passif and 'montant_initial' not in passif:
        passif['montant_initial'] = passif.pop('valeur')
    if 'taux_annuel' not in passif:
        passif['taux_annuel'] = 1.5
    if 'duree_annees' not in passif:
        passif['duree_annees'] = 20
    if 'date_debut' not in passif:
        passif['date_debut'] = date(2020, 1, 1)

# --- Types de catégories ---
types_actifs = ["Immobilier de jouissance", "Immobilier productif", "Actifs financiers", "Autres actifs"]


# Utilisation de colonnes pour séparer Actifs et Passifs
col1, col2 = st.columns(2)

# --- COLONNE 1 : ACTIFS ---
with col1:
    st.header("🟢 Actifs")
    if st.button("➕ Ajouter un actif", use_container_width=True):
        add_item('actifs')

    if not st.session_state.actifs:
        st.info("Cliquez sur 'Ajouter un actif' pour commencer.")
        
    for i, actif in enumerate(st.session_state.actifs):
        libelle_actif = actif.get('libelle', '')
        with st.expander(f"🟢 Actif {i + 1} : {libelle_actif or 'À compléter'}", expanded=False):
            field_col, button_col = st.columns([4, 1])
            with field_col:
                actif['libelle'] = st.text_input("Libellé", value=actif['libelle'], key=f"actif_libelle_{i}", placeholder="Ex: Résidence principale, Livret A...")
                actif['type'] = st.selectbox("Type d'actif", options=types_actifs, index=types_actifs.index(actif['type']) if actif['type'] in types_actifs else 0, key=f"actif_type_{i}")
                actif['valeur'] = st.number_input("Valeur (€)", value=actif['valeur'], min_value=0.0, step=1000.0, format="%.2f", key=f"actif_valeur_{i}")
            with button_col:
                st.write("") # Espaceur
                st.write("") # Espaceur
                if st.button("🗑️", key=f"del_actif_{i}", help="Supprimer cet actif"):
                    remove_item('actifs', i)
                    # Le rerun est dans la fonction remove_item

# --- COLONNE 2 : PASSIFS ---
with col2:
    st.header("🔴 Passifs")
    if st.button("➕ Ajouter un passif", use_container_width=True):
        add_item('passifs')

    if not st.session_state.passifs:
        st.info("Cliquez sur 'Ajouter un passif' pour commencer.")

    # Prépare les options pour le sélecteur d'actifs associés
    # C'est fait en dehors de la boucle pour de meilleures performances
    asset_choices = {a['id']: a.get('libelle', 'Actif sans nom') for a in st.session_state.actifs if a.get('libelle')}
    asset_options = [None] + list(asset_choices.keys())

    def format_asset_choice(asset_id):
        """Affiche le libellé de l'actif dans le sélecteur au lieu de son ID."""
        if asset_id is None:
            return "— Aucun —"
        return asset_choices.get(asset_id, "⚠️ Actif supprimé")

    for i, passif in enumerate(st.session_state.passifs):
        libelle_passif = passif.get('libelle', '')
        with st.expander(f"🔴 Passif {i + 1} : {libelle_passif or 'À compléter'}", expanded=False):
            # Ligne 1: Libellé et bouton de suppression
            r1c1, r1c2 = st.columns([4, 1])
            with r1c1:
                passif['libelle'] = st.text_input("Libellé du prêt", value=passif.get('libelle', ''), key=f"passif_libelle_{i}", placeholder="Ex: Crédit maison, Prêt auto...")
            with r1c2:
                st.write("") # Espaceur
                st.write("") # Espaceur
                if st.button("🗑️", key=f"del_passif_{i}", help="Supprimer ce passif"):
                    remove_item('passifs', i)
                    # Le rerun est dans la fonction remove_item
            
            # Ligne 2: Détails du prêt
            p_c1, p_c2, p_c3 = st.columns(3)
            passif['montant_initial'] = p_c1.number_input("Montant initial (€)", value=passif.get('montant_initial', 0.0), min_value=0.0, step=1000.0, format="%.2f", key=f"passif_montant_{i}")
            passif['taux_annuel'] = p_c2.number_input("Taux annuel (%)", value=passif.get('taux_annuel', 1.5), min_value=0.0, max_value=100.0, step=0.1, format="%.2f", key=f"passif_taux_{i}")
            passif['duree_annees'] = p_c3.number_input("Durée (années)", value=passif.get('duree_annees', 20), min_value=0, step=1, key=f"passif_duree_{i}")
            
            # Ligne 3: Autres champs
            passif['date_debut'] = st.date_input("Date de début du prêt", value=passif.get('date_debut', date.today()), min_value=date(1980, 1, 1), max_value=date.today(), key=f"passif_date_{i}")
            
            current_assoc_id = passif.get('actif_associe_id')
            if current_assoc_id and current_assoc_id not in asset_options:
                passif['actif_associe_id'] = None
                current_assoc_id = None
            current_index = asset_options.index(current_assoc_id) if current_assoc_id in asset_options else 0
            selected_asset_id = st.selectbox("Actif associé", options=asset_options, index=current_index, format_func=format_asset_choice, key=f"passif_assoc_{i}")
            passif['actif_associe_id'] = selected_asset_id

            # Ligne 4: Métriques
            mensualite = calculate_monthly_payment(passif['montant_initial'], passif['taux_annuel'], passif['duree_annees'])
            crd = calculate_crd(passif['montant_initial'], passif['taux_annuel'], passif['duree_annees'], passif['date_debut'])
            passif['crd_calcule'] = crd
            st.markdown("---")
            m1, m2 = st.columns(2)
            m1.metric("Mensualité estimée", f"{mensualite:,.2f} €/mois")
            m2.metric("Capital Restant Dû", f"{crd:,.2f} €")

# --- Calcul et affichage du patrimoine net ---
total_actifs = sum(a.get('valeur', 0.0) for a in st.session_state.actifs)
total_passifs = sum(p.get('crd_calcule', 0.0) for p in st.session_state.passifs)
patrimoine_net = total_actifs - total_passifs

st.markdown("---")
st.header("Bilan Patrimonial")

metric_col1, metric_col2, metric_col3 = st.columns(3)
metric_col1.metric("Total Actifs", f"{total_actifs:,.2f} €")
metric_col2.metric("Total Passifs", f"{total_passifs:,.2f} €")
metric_col3.metric("Patrimoine Net", f"{patrimoine_net:,.2f} €")


# --- Visualisation du Patrimoine ---
st.markdown("---")
st.header("Visualisation du Patrimoine")

df_patrimoine = get_patrimoine_df(st.session_state.actifs, st.session_state.passifs)

if not df_patrimoine.empty:
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("Répartition du Patrimoine Brut")
        df_brut = df_patrimoine[df_patrimoine['Valeur Brute'] > 0]
        if not df_brut.empty:
            fig_brut = px.treemap(
                df_brut,
                path=[px.Constant("Total"), 'Type', 'Libellé'],
                values='Valeur Brute',
                color='Type',
                hover_data={'Valeur Brute': ':,.2f €'}
            )
            fig_brut.update_traces(textinfo='label+percent root', textfont_size=14)
            fig_brut.update_layout(margin = dict(t=30, l=10, r=10, b=10))
            st.plotly_chart(fig_brut, use_container_width=True)
        else:
            st.info("Aucun actif avec une valeur brute positive à afficher.")

    with chart_col2:
        st.subheader("Répartition du Patrimoine Net")
        df_net = df_patrimoine[df_patrimoine['Valeur Nette'] > 0]
        if not df_net.empty:
            fig_net = px.treemap(
                df_net,
                path=[px.Constant("Total"), 'Type', 'Libellé'],
                values='Valeur Nette',
                color='Type',
                hover_data={'Valeur Nette': ':,.2f €'}
            )
            fig_net.update_traces(textinfo='label+percent root', textfont_size=14)
            fig_net.update_layout(margin = dict(t=30, l=10, r=10, b=10))
            st.plotly_chart(fig_net, use_container_width=True)
        else:
            st.info("Aucun actif avec une valeur nette positive à afficher.")
else:
    st.info("Ajoutez des actifs pour visualiser la répartition de votre patrimoine.")
