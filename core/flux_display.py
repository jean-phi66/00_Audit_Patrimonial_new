import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from core.flux_logic import (
    add_flux_item, 
    remove_flux_item, 
    calculate_consumption_units, 
    find_decile,
    INSEE_DECILES_2021,
    INSEE_SAVINGS_RATE_2017
)
from core.charts import create_flux_treemap_mensuel, create_flux_treemap_annuel

def display_revenus_ui():
    """Affiche l'interface pour la gestion des revenus."""
    st.header("💰 Revenus Mensuels")

    # --- Salaires (obligatoires) ---
    for revenu in st.session_state.revenus:
        if revenu['type'] == 'Salaire':
            with st.container(border=True):
                st.subheader(revenu['libelle'])
                montant = st.number_input("Montant net mensuel (€)", value=float(revenu.get('montant', 0.0)), min_value=0.0, step=100.0, format="%.2f", key=f"revenu_montant_{revenu['id']}")
                revenu['montant'] = montant
                if montant == 0.0:
                    st.warning("Le salaire de ce parent est obligatoire et doit être renseigné.")
    
    # --- Revenus du patrimoine (automatiques) ---
    st.markdown("---")
    st.subheader("Revenus du patrimoine (auto)")
    patrimoine_revenus = [r for r in st.session_state.revenus if r.get('type') == 'Patrimoine']
    if not patrimoine_revenus:
        st.info("Aucun revenu locatif détecté depuis la page Patrimoine.")
    else:
        for revenu in patrimoine_revenus:
            r_c1, r_c2 = st.columns([3, 2])
            r_c1.text_input("Libellé (auto)", value=revenu['libelle'], key=f"revenu_libelle_auto_{revenu['id']}", disabled=True)
            r_c2.number_input("Montant mensuel (€) (auto)", value=float(revenu.get('montant', 0.0)), key=f"revenu_montant_auto_{revenu['id']}", disabled=True, format="%.2f")

    # --- Autres revenus (manuels) ---
    st.markdown("---")
    st.subheader("Autres revenus manuels")
    if st.button("➕ Ajouter un autre revenu manuel", use_container_width=True):
        add_flux_item('revenus')

    manual_revenus = [r for r in st.session_state.revenus if r.get('type') == 'Autre']
    if not manual_revenus:
        st.info("Cliquez sur 'Ajouter un autre revenu manuel' pour commencer.")

    for revenu in manual_revenus:
        if revenu.get('type') == 'Autre':
            r_c1, r_c2, r_c3 = st.columns([4, 2, 1])
            revenu['libelle'] = r_c1.text_input("Libellé", value=revenu['libelle'], key=f"revenu_libelle_{revenu['id']}", placeholder="Ex: Pension, Aide...")
            revenu['montant'] = r_c2.number_input("Montant mensuel (€)", value=float(revenu.get('montant', 0.0)), min_value=0.0, step=50.0, format="%.2f", key=f"revenu_montant_{revenu['id']}")
            with r_c3:
                st.write("")
                st.write("")
                if st.button("🗑️", key=f"del_revenu_{revenu['id']}", help="Supprimer ce revenu"):
                    remove_flux_item('revenus', revenu['id'])

def display_depenses_ui():
    """Affiche l'interface pour la gestion des dépenses."""
    st.header("💸 Dépenses Mensuelles")

    # --- Dépenses du patrimoine (automatiques) ---
    st.subheader("Dépenses du patrimoine (auto)")
    patrimoine_depenses = [d for d in st.session_state.depenses if 'source_id' in d and d.get('source_id') != 'fiscal_auto']
    if not patrimoine_depenses:
        st.info("Aucune dépense liée au patrimoine détectée (charges, taxes, prêts).")
    else:
        for depense in patrimoine_depenses:
            d_c1, d_c2 = st.columns([3, 2])
            d_c1.text_input("Libellé (auto)", value=depense['libelle'], key=f"depense_libelle_auto_{depense['id']}", disabled=True)
            d_c2.number_input("Montant mensuel (€) (auto)", value=float(depense.get('montant', 0.0)), key=f"depense_montant_auto_{depense['id']}", disabled=True, format="%.2f")

    # --- Dépenses fiscales (automatiques) ---
    st.markdown("---")
    st.subheader("🏛️ Fiscalité (auto)")
    fiscal_depenses = [d for d in st.session_state.depenses if 'source_id' in d and d.get('source_id') == 'fiscal_auto']
    if not fiscal_depenses:
        st.info("Aucune dépense fiscale automatique calculée.")
    else:
        for depense in fiscal_depenses:
            d_c1, d_c2, d_c3 = st.columns([3, 2, 1])
            d_c1.text_input("Libellé (auto)", value=depense['libelle'], key=f"depense_libelle_fiscal_{depense['id']}", disabled=True)
            d_c2.number_input("Montant mensuel (€) (auto)", value=float(depense.get('montant', 0.0)), key=f"depense_montant_fiscal_{depense['id']}", disabled=True, format="%.2f")
            with d_c3:
                st.write("")
                st.write("")
                if st.button("ℹ️", key=f"info_fiscal_{depense['id']}", help="Calcul basé sur les revenus du foyer"):
                    st.info("💡 Ce montant est calculé automatiquement en fonction des salaires et revenus fonciers renseignés. Il se met à jour automatiquement.")

    # --- Dépenses manuelles ---
    st.markdown("---")
    st.subheader("Autres dépenses manuelles")
    if st.button("➕ Ajouter une dépense manuelle", use_container_width=True):
        add_flux_item('depenses')

    manual_depenses = [d for d in st.session_state.depenses if 'source_id' not in d]
    if not manual_depenses:
        st.info("Cliquez sur 'Ajouter une dépense manuelle' pour commencer.")

    categories_depenses = ["Dépenses courantes", "Logement", "Transport", "Loisirs", "Impôts et taxes", "Enfants", "Santé", "Remboursement de prêts", "Autres"]
    for depense in manual_depenses:
        d_c1, d_c2, d_c3, d_c4 = st.columns([3, 2, 2, 1])
        depense['libelle'] = d_c1.text_input("Libellé", value=depense['libelle'], key=f"depense_libelle_{depense['id']}", placeholder="Ex: Courses, Loyer, Électricité...")
        depense['montant'] = d_c2.number_input("Montant mensuel (€)", value=float(depense.get('montant', 0.0)), min_value=0.0, step=50.0, format="%.2f", key=f"depense_montant_{depense['id']}")
        depense['categorie'] = d_c3.selectbox("Catégorie", options=categories_depenses, index=categories_depenses.index(depense['categorie']) if depense['categorie'] in categories_depenses else 0, key=f"depense_cat_{depense['id']}")
        with d_c4:
            st.write("")
            st.write("")
            if st.button("🗑️", key=f"del_depense_{depense['id']}", help="Supprimer cette dépense"):
                remove_flux_item('depenses', depense['id'])

def display_summary():
    """Affiche le résumé des flux et la capacité d'épargne."""
    st.markdown("---")
    st.header("📊 Synthèse des Flux")

    total_revenus = sum(r.get('montant', 0.0) for r in st.session_state.revenus)
    total_depenses = sum(d.get('montant', 0.0) for d in st.session_state.depenses)
    capacite_epargne = total_revenus - total_depenses

    s_c1, s_c2, s_c3 = st.columns(3)
    s_c1.metric("Total des Revenus Mensuels", f"{total_revenus:,.2f} €")
    s_c2.metric("Total des Dépenses Mensuelles", f"{total_depenses:,.2f} €")
    s_c3.metric("Capacité d'Épargne Mensuelle", f"{capacite_epargne:,.2f} €", delta=f"{capacite_epargne:,.2f} €")

    if capacite_epargne < 0:
        st.warning(f"Attention : Vos dépenses ({total_depenses:,.2f} €) dépassent vos revenus ({total_revenus:,.2f} €). Vous avez un déficit mensuel de {-capacite_epargne:,.2f} €.")

    st.subheader("Répartition des Revenus (Dépenses + Reste à vivre)")

    if total_revenus > 0:
        # Préparation des données pour le treemap
        df_depenses = pd.DataFrame(st.session_state.depenses)
        if not df_depenses.empty and df_depenses['montant'].sum() > 0:
            # Regrouper les dépenses par catégorie
            depenses_par_cat = df_depenses.groupby('categorie')['montant'].sum().reset_index()
            depenses_par_cat.rename(columns={'categorie': 'label'}, inplace=True)
            data_treemap = depenses_par_cat.to_dict('records')
        else:
            data_treemap = []

        # Ajouter le reste à vivre s'il est positif
        if capacite_epargne > 0:
            data_treemap.append({'label': 'Reste à vivre', 'montant': capacite_epargne})

        if data_treemap:
            df_treemap = pd.DataFrame(data_treemap)
            
            # Création des colonnes pour les graphiques
            tm_col1, tm_col2 = st.columns(2)

            with tm_col1:
                # Treemap Mensuel
                fig_mensuel = create_flux_treemap_mensuel(data_treemap, total_revenus)
                if fig_mensuel:
                    st.plotly_chart(fig_mensuel, use_container_width=True)

            with tm_col2:
                # Treemap Annuel
                fig_annuel = create_flux_treemap_annuel(data_treemap, total_revenus)
                if fig_annuel:
                    st.plotly_chart(fig_annuel, use_container_width=True)
    else:
        st.info("Ajoutez des revenus pour visualiser leur répartition.")

    # Ajout de la section de comparaison des revenus
    display_income_comparison_ui(total_revenus, st.session_state.depenses, capacite_epargne)

def display_income_comparison_ui(total_revenus_mensuels, depenses, capacite_epargne_mensuelle):
    """Affiche la comparaison du niveau de vie du foyer avec les données nationales."""
    st.markdown("---")

    # 1. Calcul des unités de consommation
    parents = st.session_state.get('parents', [])
    enfants = st.session_state.get('enfants', [])
    uc = calculate_consumption_units(parents, enfants)

    # 2. Calcul du revenu disponible annuel
    impots_et_taxes_mensuels = sum(d.get('montant', 0.0) for d in depenses if d.get('categorie') == 'Impôts et taxes')
    revenu_disponible_annuel = (total_revenus_mensuels - impots_et_taxes_mensuels) * 12
    revenu_disponible_mensuel = max(0, total_revenus_mensuels - impots_et_taxes_mensuels)

    if uc <= 0:
        st.warning("Le nombre d'unités de consommation est de 0. Impossible de calculer le niveau de vie.")
        return

    niveau_de_vie_foyer = revenu_disponible_annuel / uc
    decile_foyer = find_decile(niveau_de_vie_foyer, INSEE_DECILES_2021)
    taux_epargne_cible_pct = INSEE_SAVINGS_RATE_2017.get(decile_foyer, 0)
    epargne_cible_mensuelle = revenu_disponible_mensuel * (taux_epargne_cible_pct / 100)

    # 3. Affichage en deux colonnes principales (2/3 - 1/3)
    main_col1, main_col2 = st.columns([2, 1])

    with main_col1:
        st.subheader("📊 Positionnement du Foyer")
        
        # Métriques du positionnement (3 colonnes sur la même ligne)
        pos_col1, pos_col2, pos_col3 = st.columns(3)
        pos_col1.metric("Unités de Consommation", f"{uc:.2f} UC", help="Le premier adulte compte pour 1 UC, chaque personne de +14 ans pour 0.5 UC, et chaque enfant de -14 ans pour 0.3 UC.")
        pos_col2.metric("Revenu Disponible Annuel", f"{revenu_disponible_annuel:,.0f} €", help="Total des revenus annuels moins les impôts et taxes directs.")
        pos_col3.metric("Niveau de Vie par UC", f"{niveau_de_vie_foyer:,.0f} € / an", help="Revenu disponible annuel divisé par le nombre d'UC.")

        # Graphique de comparaison
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=['Votre Foyer'], x=[niveau_de_vie_foyer], name='Votre Niveau de Vie', orientation='h',
            marker=dict(color='rgba(23, 103, 166, 0.8)', line=dict(color='rgba(23, 103, 166, 1.0)', width=1)),
            text=f"<b>{niveau_de_vie_foyer:,.0f} €</b>", textposition='inside', insidetextanchor='middle'
        ))

        for label, value in INSEE_DECILES_2021.items():
            fig.add_vline(
                x=value, line_width=1, line_dash="dash", line_color="grey",
                annotation_text=f"<b>{label.split(' ')[0]}</b><br>{value:,.0f}€",
                annotation_position="top", annotation_font_size=10
            )

        decile_atteint = next((label for label, value in sorted(INSEE_DECILES_2021.items(), key=lambda item: item[1], reverse=True) if niveau_de_vie_foyer >= value), None)
        if decile_atteint:
            st.success(f"Votre niveau de vie vous place au-dessus du **{decile_atteint}** des foyers français.")
        else:
            st.info("Votre niveau de vie se situe dans le premier décile des foyers français.")

        fig.update_layout(
            title_text="Positionnement vs déciles français",
            xaxis_title="Niveau de vie annuel par UC (€)", yaxis_title="",
            showlegend=False, height=280, margin=dict(l=20, r=20, t=60, b=20), bargap=0.5,
            xaxis_range=[0, max(niveau_de_vie_foyer * 1.2, 50000)]
        )
        st.plotly_chart(fig, use_container_width=True)

    with main_col2:
        st.subheader("💰 Comparaison du Taux d'Épargne")
        
        # Métriques d'épargne
        sav_col1, sav_col2 = st.columns(2)
        sav_col1.metric(
            label="Votre Épargne Mensuelle",
            value=f"{capacite_epargne_mensuelle:,.0f} €",
            delta=f"{capacite_epargne_mensuelle - epargne_cible_mensuelle:,.0f} € vs. moyenne"
        )
        sav_col2.metric(
            label=f"Épargne Moyenne ({decile_foyer}e décile)",
            value=f"{epargne_cible_mensuelle:,.0f} €",
            help=f"Montant d'épargne mensuel moyen pour un foyer du {decile_foyer}e décile, correspondant à un taux de {taux_epargne_cible_pct}% du revenu disponible (Source: INSEE 2017)."
        )

        # Jauge d'épargne
        min_range = min(-100, capacite_epargne_mensuelle * 1.2, epargne_cible_mensuelle * 1.2)
        max_range = max(100, capacite_epargne_mensuelle * 1.2, epargne_cible_mensuelle * 1.2)

        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = capacite_epargne_mensuelle,
            number = {'prefix': "€ ", 'font': {'size': 30}},
            title = {"text": f"Épargne mensuelle (Cible: {epargne_cible_mensuelle:,.0f} €)", 'font': {'size': 16}},
            delta = {'reference': epargne_cible_mensuelle, 'increasing': {'color': "green"}, 'decreasing': {'color': "red"}},
            gauge = {'axis': {'range': [min_range, max_range]}, 'bar': {'color': "darkblue"}, 'threshold' : {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': epargne_cible_mensuelle}}))
        fig_gauge.update_layout(height=350, margin=dict(t=50, b=20, l=30, r=30))
        st.plotly_chart(fig_gauge, use_container_width=True)


def display_detailed_tables():
    """Affiche les tableaux détaillés des flux mensuels et annuels."""
    st.markdown("---")
    st.subheader("📊 Tableaux détaillés des Flux")

    # Création des données pour les tables
    revenus_data = []
    depenses_data = []

    # Récupération des données de revenus depuis session_state
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

    # Récupération des données de dépenses depuis session_state
    if 'depenses' in st.session_state and isinstance(st.session_state.depenses, list):
        for depense in st.session_state.depenses:
            montant = depense.get('montant', 0)
            if montant > 0:
                categorie = depense.get('categorie', 'Autres')
                libelle = depense.get('libelle', 'N/A')
                
                depenses_data.append({'Catégorie': categorie, 'Montant': montant, 'Détail': libelle})

    # --- Table détaillée des flux MENSUELS ---
    with st.expander("📅 Flux Mensuels", expanded=True):
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

    # --- Table détaillée des flux ANNUELS ---
    with st.expander("📅 Flux Annuels", expanded=False):
        col1_exp, col2_exp = st.columns(2)

        with col1_exp:
            st.markdown("### 💰 Revenus Annuels")
            if revenus_data:
                df_revenus_annual = pd.DataFrame(revenus_data)
                # Multiplier par 12 pour obtenir les valeurs annuelles
                df_revenus_annual['Montant'] = df_revenus_annual['Montant'] * 12
                # Calcul du total avant formatage
                total_revenus_annual = df_revenus_annual['Montant'].sum()
                # Formatage pour affichage
                df_revenus_annual['Montant'] = df_revenus_annual['Montant'].apply(lambda x: f"{x:,.0f} €".replace(',', ' '))
                st.dataframe(df_revenus_annual, use_container_width=True, hide_index=True)
                st.markdown(f"**Total revenus annuels : {total_revenus_annual:,.0f} €**".replace(',', ' '))
            else:
                st.info("Aucun revenu renseigné")

        with col2_exp:
            st.markdown("### 💸 Charges Annuelles")
            if depenses_data:
                df_charges_annual = pd.DataFrame(depenses_data)
                # Multiplier par 12 pour obtenir les valeurs annuelles
                df_charges_annual['Montant'] = df_charges_annual['Montant'] * 12
                # Calcul du total avant formatage
                total_charges_annual = df_charges_annual['Montant'].sum()
                # Formatage pour affichage
                df_charges_annual['Montant'] = df_charges_annual['Montant'].apply(lambda x: f"{x:,.0f} €".replace(',', ' '))
                st.dataframe(df_charges_annual, use_container_width=True, hide_index=True)
                st.markdown(f"**Total charges annuelles : {total_charges_annual:,.0f} €**".replace(',', ' '))
            else:
                st.info("Aucune charge renseignée")
