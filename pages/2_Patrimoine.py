import streamlit as st
import uuid
from datetime import date
import pandas as pd
import plotly.express as px

import sys
import os
# Add project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.patrimoine_logic import calculate_monthly_payment, calculate_crd, get_patrimoine_df, add_item, remove_item

# --- Constantes et Configuration ---

# Palette de couleurs unifiée pour tous les graphiques de la page
# Utilisation de la palette "Vivid" pour des couleurs vives et contrastées.
ASSET_TYPE_COLOR_MAP = {
    'Immobilier de jouissance': px.colors.qualitative.Vivid[0],
    'Immobilier productif': px.colors.qualitative.Vivid[1],
    'Actifs financiers': px.colors.qualitative.Vivid[2],
    'Autres actifs': px.colors.qualitative.Vivid[4],
    'Placements financiers': px.colors.qualitative.Vivid[2], # Pour le graphique "cible"
}
# --- Fonctions de configuration et de migration ---

def initialize_session_state():
    """Initialise les listes d'actifs et de passifs dans le session state si elles n'existent pas."""
    if 'actifs' not in st.session_state:
        st.session_state.actifs = []
    if 'passifs' not in st.session_state:
        st.session_state.passifs = []

def run_data_migrations():
    """
    Exécute des migrations de données pour assurer la compatibilité avec les nouvelles versions
    de la structure de données (ex: ajout d'ID, renommage de champs).
    """
    # Migration pour les UUID des actifs
    for actif in st.session_state.actifs:
        if 'id' not in actif:
            actif['id'] = str(uuid.uuid4())

    # Migration pour les champs des passifs
    for passif in st.session_state.passifs:
        if 'valeur' in passif and 'montant_initial' not in passif:
            passif['montant_initial'] = passif.pop('valeur')
        if 'duree_annees' in passif: # Migration de années vers mois
            passif['duree_mois'] = passif.pop('duree_annees') * 12
        if 'taux_annuel' not in passif:
            passif['taux_annuel'] = 1.5
        if 'duree_mois' not in passif:
            passif['duree_mois'] = 240
        if 'date_debut' not in passif:
            passif['date_debut'] = date(2020, 1, 1)

# --- Fonctions d'interface utilisateur (UI) ---

def display_assets_ui():
    """Affiche l'interface pour la gestion des actifs."""
    st.header("🟢 Actifs")
    if st.button("➕ Ajouter un actif", use_container_width=True):
        add_item('actifs')

    if not st.session_state.actifs:
        st.info("Cliquez sur 'Ajouter un actif' pour commencer.")
    
    types_actifs = ["Immobilier de jouissance", "Immobilier productif", "Actifs financiers", "Autres actifs"]
    for i, actif in enumerate(st.session_state.actifs):
        libelle_actif = actif.get('libelle', '')
        with st.expander(f"🟢 Actif {i + 1} : {libelle_actif or 'À compléter'}", expanded=False):
            field_col, button_col = st.columns([4, 1])
            with field_col:
                actif['libelle'] = st.text_input("Libellé", value=actif['libelle'], key=f"actif_libelle_{i}", placeholder="Ex: Résidence principale, Livret A...")
                actif['type'] = st.selectbox("Type d'actif", options=types_actifs, index=types_actifs.index(actif['type']) if actif['type'] in types_actifs else 0, key=f"actif_type_{i}")
                actif['valeur'] = st.number_input("Valeur (€)", value=actif.get('valeur', 0.0), min_value=0.0, step=1000.0, format="%.2f", key=f"actif_valeur_{i}")

                # Ajout des champs spécifiques à l'immobilier
                if actif['type'] == "Immobilier productif":
                    st.markdown("---")
                    actif['loyers_mensuels'] = st.number_input(
                        "Loyers mensuels (€)",
                        value=actif.get('loyers_mensuels', 0.0),
                        min_value=0.0, step=50.0, format="%.2f",
                        key=f"actif_loyers_{i}"
                    )
                    actif['charges'] = st.number_input(
                        "Charges mensuelles (€)",
                        value=actif.get('charges', 0.0),
                        min_value=0.0, step=10.0, format="%.2f",
                        key=f"actif_charges_{i}",
                        help="Charges de copropriété, assurance PNO, etc."
                    )
                    actif['taxe_fonciere'] = st.number_input(
                        "Taxe foncière (€/an)",
                        value=actif.get('taxe_fonciere', 0.0),
                        min_value=0.0, step=50.0, format="%.2f",
                        key=f"actif_taxe_{i}"
                    )
                    
                    st.markdown("---")
                    st.write("**Dispositif Fiscal**")
                    actif['dispositif_fiscal'] = st.selectbox(
                        "Dispositif applicable",
                        options=["Aucun", "Pinel"],
                        index=1 if actif.get('dispositif_fiscal') == 'Pinel' else 0,
                        key=f"actif_dispositif_{i}"
                    )

                    if actif.get('dispositif_fiscal') == 'Pinel':
                        actif['duree_dispositif'] = st.selectbox(
                            "Durée d'engagement Pinel", options=[6, 9, 12],
                            index=[6, 9, 12].index(actif.get('duree_dispositif', 9)),
                            key=f"pinel_duree_{i}"
                        )
                        actif['annee_debut_dispositif'] = st.number_input("Année de début", min_value=2014, max_value=date.today().year, value=actif.get('annee_debut_dispositif', date.today().year - 1), key=f"pinel_annee_{i}")

                elif actif['type'] == "Immobilier de jouissance":
                    st.markdown("---")
                    actif['taxe_fonciere'] = st.number_input(
                        "Taxe foncière (€/an)",
                        value=actif.get('taxe_fonciere', 0.0),
                        min_value=0.0, step=50.0, format="%.2f",
                        key=f"actif_taxe_{i}"
                    )

            with button_col:
                st.write("") # Espaceur
                st.write("") # Espaceur
                if st.button("🗑️", key=f"del_actif_{i}", help="Supprimer cet actif"):
                    remove_item('actifs', i)

def display_liabilities_ui():
    """Affiche l'interface pour la gestion des passifs."""
    st.header("🔴 Passifs")
    if st.button("➕ Ajouter un passif", use_container_width=True):
        add_item('passifs')

    if not st.session_state.passifs:
        st.info("Cliquez sur 'Ajouter un passif' pour commencer.")

    asset_choices = {a['id']: a.get('libelle', 'Actif sans nom') for a in st.session_state.actifs if a.get('libelle')}
    asset_options = [None] + list(asset_choices.keys())

    def format_asset_choice(asset_id):
        if asset_id is None: return "— Aucun —"
        return asset_choices.get(asset_id, "⚠️ Actif supprimé")

    for i, passif in enumerate(st.session_state.passifs):
        libelle_passif = passif.get('libelle', '')
        with st.expander(f"🔴 Passif {i + 1} : {libelle_passif or 'À compléter'}", expanded=False):
            r1c1, r1c2 = st.columns([4, 1])
            with r1c1:
                passif['libelle'] = st.text_input("Libellé du prêt", value=passif.get('libelle', ''), key=f"passif_libelle_{i}", placeholder="Ex: Crédit maison, Prêt auto...")
            with r1c2:
                st.write("\n\n")
                if st.button("🗑️", key=f"del_passif_{i}", help="Supprimer ce passif"):
                    remove_item('passifs', i)
            
            p_c1, p_c2, p_c3 = st.columns(3)
            passif['montant_initial'] = p_c1.number_input("Montant initial (€)", value=passif.get('montant_initial', 0.0), min_value=0.0, step=1000.0, format="%.2f", key=f"passif_montant_{i}")
            passif['taux_annuel'] = p_c2.number_input("Taux annuel (%)", value=passif.get('taux_annuel', 1.5), min_value=0.0, max_value=100.0, step=0.1, format="%.2f", key=f"passif_taux_{i}")
            passif['duree_mois'] = p_c3.number_input("Durée (mois)", value=passif.get('duree_mois', 240), min_value=0, step=12, key=f"passif_duree_{i}")
            
            passif['date_debut'] = st.date_input("Date de début du prêt", value=passif.get('date_debut', date.today()), min_value=date(1980, 1, 1), max_value=date.today(), key=f"passif_date_{i}")
            
            current_assoc_id = passif.get('actif_associe_id')
            if current_assoc_id and current_assoc_id not in asset_options:
                current_assoc_id = passif['actif_associe_id'] = None
            current_index = asset_options.index(current_assoc_id) if current_assoc_id in asset_options else 0
            passif['actif_associe_id'] = st.selectbox("Actif associé", options=asset_options, index=current_index, format_func=format_asset_choice, key=f"passif_assoc_{i}")

            mensualite = calculate_monthly_payment(passif['montant_initial'], passif['taux_annuel'], passif['duree_mois'])
            crd = calculate_crd(passif['montant_initial'], passif['taux_annuel'], passif['duree_mois'], passif['date_debut'])
            passif['crd_calcule'] = crd
            st.markdown("---")
            m1, m2 = st.columns(2)
            m1.metric("Mensualité estimée", f"{mensualite:,.2f} €/mois")
            m2.metric("Capital Restant Dû", f"{crd:,.2f} €")

def display_summary_and_charts():
    """Calcule et affiche le bilan patrimonial et les graphiques de répartition."""
    total_actifs = sum(a.get('valeur', 0.0) for a in st.session_state.actifs)
    total_passifs = sum(p.get('crd_calcule', 0.0) for p in st.session_state.passifs)
    patrimoine_net = total_actifs - total_passifs

    st.markdown("---")
    st.header("Bilan Patrimonial")
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("Total Actifs", f"{total_actifs:,.2f} €")
    metric_col2.metric("Total Passifs", f"{total_passifs:,.2f} €")
    metric_col3.metric("Patrimoine Net", f"{patrimoine_net:,.2f} €")

    #st.markdown("---")
    #st.header("Visualisation du Patrimoine")
    df_patrimoine = get_patrimoine_df(st.session_state.actifs, st.session_state.passifs)

    if df_patrimoine.empty:
        st.info("Ajoutez des actifs pour visualiser la répartition de votre patrimoine.")
        return

    st.subheader("Tableau Récapitulatif")
    df_display = df_patrimoine.copy()
    # S'assurer que les colonnes existent avant de les réordonner pour l'affichage
    cols_to_display = ['Libellé', 'Type', 'Valeur Brute', 'Passif', 'Valeur Nette']
    existing_cols = [col for col in cols_to_display if col in df_display.columns]
    st.dataframe(
        df_display[existing_cols].style.format({
            'Valeur Brute': '{:,.2f} €',
            'Passif': '{:,.2f} €',
            'Valeur Nette': '{:,.2f} €'
        }),
        use_container_width=True,
        hide_index=True
    )

    chart_col1, chart_col2 = st.columns(2, gap="medium")
    with chart_col1:
        st.subheader("Répartition du Patrimoine Brut")
        fig_brut = create_patrimoine_brut_treemap(df_patrimoine, ASSET_TYPE_COLOR_MAP)
        if fig_brut:
            st.plotly_chart(fig_brut, use_container_width=True)
        else:
            st.info("Aucun actif avec une valeur brute positive à afficher.")

    with chart_col2:
        st.subheader("Répartition du Patrimoine Net")
        fig_net = create_patrimoine_net_treemap(df_patrimoine, ASSET_TYPE_COLOR_MAP)
        if fig_net:
            st.plotly_chart(fig_net, use_container_width=True)
        else:
            st.info("Aucun actif avec une valeur nette positive à afficher.")

    st.markdown("---")
    st.header("Analyse de la Répartition")

    donut_col1, donut_col2 = st.columns(2)

    with donut_col1:
        st.subheader("Répartition Actuelle (Nette)")
        fig_donut_actual = create_patrimoine_net_donut(df_patrimoine, ASSET_TYPE_COLOR_MAP)
        if fig_donut_actual:
            st.plotly_chart(fig_donut_actual, use_container_width=True)
        else:
            st.info("Aucun actif avec une valeur nette positive à afficher.")

    with donut_col2:
        st.subheader("Répartition Cible Théorique")
        fig_donut_ideal = create_patrimoine_ideal_donut(ASSET_TYPE_COLOR_MAP)
        st.plotly_chart(fig_donut_ideal, use_container_width=True)

def create_patrimoine_brut_treemap(df_patrimoine, color_map):
    """Crée le treemap de répartition du patrimoine brut."""
    df_brut = df_patrimoine[df_patrimoine['Valeur Brute'] > 0]
    if not df_brut.empty:
        fig = px.treemap(
            df_brut, 
            path=['Type', 'Libellé'], 
            values='Valeur Brute', 
            color='Type', 
            color_discrete_map=color_map,
            hover_data={'Valeur Brute': ':,.2f €'}
        )
        fig.update_traces(textinfo='label+percent root', textfont_size=14)
        fig.update_layout(margin=dict(t=10, l=10, r=10, b=10))
        return fig
    else:
        return None

def create_patrimoine_net_treemap(df_patrimoine, color_map):
    """Crée le treemap de répartition du patrimoine net."""
    df_net = df_patrimoine[df_patrimoine['Valeur Nette'] > 0]
    if not df_net.empty:
        fig = px.treemap(
            df_net, 
            path=['Type', 'Libellé'], 
            values='Valeur Nette', 
            color='Type', 
            color_discrete_map=color_map,
            hover_data={'Valeur Nette': ':,.2f €'}
        )
        fig.update_traces(textinfo='label+percent root', textfont_size=14)
        fig.update_layout(margin=dict(t=10, l=10, r=10, b=10))
        return fig
    else:
        return None

def create_patrimoine_net_donut(df_patrimoine, color_map):
    """Crée le donut chart de répartition du patrimoine net par type d'actif."""
    df_net_by_type = df_patrimoine[df_patrimoine['Valeur Nette'] > 0].groupby('Type')['Valeur Nette'].sum().reset_index()
    if not df_net_by_type.empty:
        fig = px.pie(
            df_net_by_type,
            names='Type',
            values='Valeur Nette',
            hole=0.4,
            color='Type',
            color_discrete_map=color_map
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(showlegend=True, legend_title_text='Type d\'Actif', margin=dict(t=50, l=10, r=10, b=10))
        return fig
    else:
        return None

def create_patrimoine_ideal_donut(color_map):
    """Crée le donut chart de répartition cible idéale du patrimoine."""
    ideal_data = {
        'Catégorie': ['Immobilier de jouissance', 'Immobilier productif', 'Placements financiers'],
        'Pourcentage': [33.33, 33.33, 33.34]
    }
    df_ideal = pd.DataFrame(ideal_data)
    fig = px.pie(
        df_ideal,
        names='Catégorie',
        values='Pourcentage',
        hole=0.4,
        color='Catégorie',
        color_discrete_map=color_map
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(showlegend=True, legend_title_text='Catégorie', margin=dict(t=50, l=10, r=10, b=10))
    return fig
# --- Exécution Principale ---

#def main():
"""Fonction principale pour exécuter la page Patrimoine."""
st.title("🏡 Description du Patrimoine")
st.markdown("Listez ici vos actifs (ce que vous possédez) et vos passifs (ce que vous devez).")

initialize_session_state()
run_data_migrations()

col1, col2 = st.columns(2)
with col1:
    display_assets_ui()
with col2:
    display_liabilities_ui()

display_summary_and_charts()

#if __name__ == "__main__":
#    main()
