import streamlit as st
import uuid
import plotly.graph_objects as go
from datetime import date
from core.patrimoine_logic import (
    calculate_monthly_payment, calculate_crd, get_patrimoine_df, add_item, remove_item
)
from core.charts import (
    create_patrimoine_brut_treemap, create_patrimoine_net_treemap,
    create_patrimoine_net_donut, create_patrimoine_ideal_donut
)
from core.flux_logic import calculate_consumption_units, calculate_age

# --- Constantes INSEE pour le patrimoine ---
# Patrimoine net des ménages par décile (INSEE, enquête 2021, en euros)
# Source : https://www.insee.fr/fr/statistiques/7627978
INSEE_PATRIMOINE_DECILES_2021 = {
    "D1 (10%)": 4400, "D2 (20%)": 13400, "D3 (30%)": 33200,
    "D4 (40%)": 106200, "D5 (Médiane)": 177200, "D6 (60%)": 246100,
    "D7 (70%)": 328400, "D8 (80%)": 447500, "D9 (90%)": 716300,
    "D95 (9(%)": 1034600, "D99 (99%)": 2239200
}

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
                    actif['mode_exploitation'] = st.radio(
                        "Mode d'exploitation",
                        options=["Location nue", "Location Meublée"],
                        index=1 if actif.get('mode_exploitation') == 'Location Meublée' else 0,
                        key=f"actif_mode_expl_{i}",
                        horizontal=True
                    )

                    if actif['mode_exploitation'] == "Location Meublée":
                        # Si on passe en meublé, on s'assure que le dispositif fiscal est remis à "Aucun"
                        if actif.get('dispositif_fiscal') != 'Aucun':
                            actif['dispositif_fiscal'] = 'Aucun'
                        
                        st.write("**Détails pour l'amortissement (LMNP/LMP)**")
                        # Correction: Suppression des colonnes imbriquées pour éviter une erreur Streamlit.
                        actif['part_amortissable_foncier'] = st.number_input(
                            "Valeur du Foncier (€)",
                            value=actif.get('part_amortissable_foncier', 0.0),
                            min_value=0.0, step=1000.0, format="%.2f",
                            key=f"actif_foncier_{i}",
                            help="Part non amortissable correspondant au terrain (ex: 15-20% de la valeur totale)."
                        )
                        actif['part_travaux'] = st.number_input(
                            "Valeur des Travaux (€)",
                            value=actif.get('part_travaux', 0.0),
                            min_value=0.0, step=1000.0, format="%.2f",
                            key=f"actif_travaux_{i}",
                            help="Montant des travaux réalisés, qui sont amortissables."
                        )
                        actif['part_meubles'] = st.number_input(
                            "Valeur des Meubles (€)",
                            value=actif.get('part_meubles', 0.0),
                            min_value=0.0, step=500.0, format="%.2f",
                            key=f"actif_meubles_{i}",
                            help="Valeur du mobilier, qui est amortissable."
                        )

                    elif actif['mode_exploitation'] == "Location nue":
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
                    actif['charges'] = st.number_input(
                        "Charges mensuelles (€)",
                        value=actif.get('charges', 0.0),
                        min_value=0.0, step=10.0, format="%.2f",
                        key=f"actif_charges_{i}",
                        help="Charges de copropriété, assurance habitation, etc."
                    )
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

def display_patrimoine_comparison_ui():
    """Affiche la comparaison du patrimoine du foyer avec les données nationales INSEE."""
    st.markdown("---")
    st.header("📊 Positionnement Patrimonial")
    st.markdown("Cette section compare le **patrimoine net** de votre foyer à la moyenne nationale française, sur la base des données de l'INSEE (2021).")

    # 1. Calcul du patrimoine net du foyer
    total_actifs = sum(a.get('valeur', 0.0) for a in st.session_state.actifs)
    total_passifs = sum(p.get('crd_calcule', 0.0) for p in st.session_state.passifs)
    patrimoine_net_foyer = total_actifs - total_passifs

    # 2. Affichage de la métrique
    st.metric("Patrimoine Net du Foyer", f"{patrimoine_net_foyer:,.0f} €")

    # 3. Création du graphique de comparaison
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=['Votre Foyer'], x=[patrimoine_net_foyer], name='Votre Patrimoine Net', orientation='h',
        marker=dict(color='rgba(34, 139, 34, 0.8)', line=dict(color='rgba(34, 139, 34, 1.0)', width=1)),
        text=f"<b>{patrimoine_net_foyer:,.0f} €</b>", textposition='inside', insidetextanchor='middle'
    ))

    # Ajouter les lignes des déciles
    for label, value in INSEE_PATRIMOINE_DECILES_2021.items():
        fig.add_vline(
            x=value, line_width=1, line_dash="dash", line_color="grey",
            annotation_text=f"<b>{label.split(' ')[0]}</b><br>{value:,.0f}€",
            annotation_position="top", annotation_font_size=10
        )

    # Déterminer le décile atteint
    decile_atteint = None
    for label, value in sorted(INSEE_PATRIMOINE_DECILES_2021.items(), key=lambda item: item[1], reverse=True):
        if patrimoine_net_foyer >= value:
            decile_atteint = label
            break

    if decile_atteint:
        st.success(f"Votre patrimoine net vous place au-dessus du **{decile_atteint}** des foyers français.")
    else:
        st.info("Votre patrimoine net se situe dans le premier décile des foyers français.")

    # Configuration du graphique
    max_range = max(patrimoine_net_foyer * 1.2, 200000)  # Au minimum 200k€ pour la lisibilité
    fig.update_layout(
        title_text="Positionnement de votre patrimoine net par rapport aux déciles français (INSEE 2021)",
        xaxis_title="Patrimoine net du foyer (€)", 
        yaxis_title="",
        showlegend=False, 
        height=300, 
        margin=dict(l=20, r=20, t=80, b=20), 
        bargap=0.5,
        xaxis_range=[0, max_range]
    )
    st.plotly_chart(fig, use_container_width=True)

    # Informations complémentaires
    if patrimoine_net_foyer < 0:
        st.warning("⚠️ Votre patrimoine net est négatif. Cela signifie que vos dettes dépassent la valeur de vos actifs.")
    elif patrimoine_net_foyer == 0:
        st.info("💡 Votre patrimoine net est nul. C'est le point de départ pour commencer à constituer un patrimoine.")
    else:
        st.info("💡 Les données INSEE incluent tous les types de patrimoine : immobilier, financier, professionnel, etc.")

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
        fig_brut = create_patrimoine_brut_treemap(df_patrimoine)
        if fig_brut:
            st.plotly_chart(fig_brut, use_container_width=True)
        else:
            st.info("Aucun actif avec une valeur brute positive à afficher.")

    with chart_col2:
        st.subheader("Répartition du Patrimoine Net")
        fig_net = create_patrimoine_net_treemap(df_patrimoine)
        if fig_net:
            st.plotly_chart(fig_net, use_container_width=True)
        else:
            st.info("Aucun actif avec une valeur nette positive à afficher.")

    st.markdown("---")
    st.header("Analyse de la Répartition")

    donut_col1, donut_col2 = st.columns(2)

    with donut_col1:
        st.subheader("Répartition Actuelle (Nette)")
        fig_donut_actual = create_patrimoine_net_donut(df_patrimoine)
        if fig_donut_actual:
            st.plotly_chart(fig_donut_actual, use_container_width=True)
        else:
            st.info("Aucun actif avec une valeur nette positive à afficher.")

    with donut_col2:
        st.subheader("Répartition Cible Théorique")
        fig_donut_ideal = create_patrimoine_ideal_donut()
        st.plotly_chart(fig_donut_ideal, use_container_width=True)

    # Ajout de la section de comparaison patrimoniale
    if not df_patrimoine.empty:
        display_patrimoine_comparison_ui()

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
