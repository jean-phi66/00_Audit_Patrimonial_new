import streamlit as st
import uuid
from datetime import date
import pandas as pd
import plotly.express as px
from core.patrimoine_logic import calculate_monthly_payment, calculate_crd, get_patrimoine_df, add_item, remove_item

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

                # Ajout des champs spécifiques à l'immobilier productif
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

    st.markdown("---")
    st.header("Visualisation du Patrimoine")
    df_patrimoine = get_patrimoine_df(st.session_state.actifs, st.session_state.passifs)

    if df_patrimoine.empty:
        st.info("Ajoutez des actifs pour visualiser la répartition de votre patrimoine.")
        return

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.subheader("Répartition du Patrimoine Brut")
        df_brut = df_patrimoine[df_patrimoine['Valeur Brute'] > 0]
        if not df_brut.empty:
            fig = px.treemap(df_brut, path=[px.Constant("Total"), 'Type', 'Libellé'], values='Valeur Brute', color='Type', hover_data={'Valeur Brute': ':,.2f €'})
            fig.update_traces(textinfo='label+percent root', textfont_size=14)
            fig.update_layout(margin=dict(t=30, l=10, r=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucun actif avec une valeur brute positive à afficher.")

    with chart_col2:
        st.subheader("Répartition du Patrimoine Net")
        df_net = df_patrimoine[df_patrimoine['Valeur Nette'] > 0]
        if not df_net.empty:
            fig = px.treemap(df_net, path=[px.Constant("Total"), 'Type', 'Libellé'], values='Valeur Nette', color='Type', hover_data={'Valeur Nette': ':,.2f €'})
            fig.update_traces(textinfo='label+percent root', textfont_size=14)
            fig.update_layout(margin=dict(t=30, l=10, r=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucun actif avec une valeur nette positive à afficher.")

# --- Exécution Principale ---

def main():
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

if __name__ == "__main__":
    main()
