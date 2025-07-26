import streamlit as st
import pandas as pd
import plotly.express as px
from core.projection_logic import calculate_age
from core.charts import create_gantt_chart_fig

def display_settings_ui(parents, enfants):
    """Affiche les widgets pour configurer les paramètres de la projection."""
    with st.expander("⚙️ Paramètres de la projection", expanded=True):
        duree_projection = st.number_input(
            "Durée de la projection (années)",
            min_value=1, max_value=50, value=25, step=1,
            help="Nombre d'années à projeter après le départ à la retraite des parents."
        )
        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("👨‍👩‍👧 Parents")
            for parent in parents:
                prenom = parent.get('prenom')
                if prenom:
                    # 1. Initialisation des paramètres de projection s'ils n'existent pas
                    if prenom not in st.session_state.projection_settings:
                        st.session_state.projection_settings[prenom] = {
                            'retraite': 64, 
                            'revenu_actuel': 0,  # Sera écrasé par la synchro
                            'pension_annuelle': 25000
                        }
                    
                    # 2. Synchronisation systématique du revenu depuis la page Flux
                    salaire_mensuel = 0
                    for revenu in st.session_state.get('revenus', []):
                        if revenu.get('type') == 'Salaire' and revenu.get('libelle') == f"Salaire {prenom}":
                            salaire_mensuel = revenu.get('montant', 0)
                            break
                    revenu_annuel_depuis_flux = salaire_mensuel * 12
                    st.session_state.projection_settings[prenom]['revenu_actuel'] = revenu_annuel_depuis_flux

                    # 3. Affichage des paramètres
                    age_actuel = calculate_age(parent.get('date_naissance'))
                    st.session_state.projection_settings[prenom]['retraite'] = st.number_input(f"Âge de départ à la retraite de {prenom}", min_value=age_actuel, max_value=75, value=st.session_state.projection_settings[prenom]['retraite'], key=f"retraite_{prenom}")
                    st.number_input(f"Revenu annuel brut de {prenom} (activité)", value=st.session_state.projection_settings[prenom]['revenu_actuel'], disabled=True, key=f"revenu_{prenom}", help="Cette valeur est synchronisée depuis la page 'Flux' et n'est pas modifiable ici.")
                    st.session_state.projection_settings[prenom]['pension_annuelle'] = st.number_input(f"Pension de retraite annuelle de {prenom}", 0, 200000, st.session_state.projection_settings[prenom].get('pension_annuelle', 25000), step=500, key=f"pension_{prenom}")

        with col2:
            st.subheader("👶 Enfants")
            if not enfants:
                st.info("Aucun enfant renseigné.")
            for enfant in enfants:
                prenom = enfant.get('prenom')
                if prenom:
                    if prenom not in st.session_state.projection_settings:
                        st.session_state.projection_settings[prenom] = {
                            'debut_etudes': 18, 
                            'duree_etudes': 5,
                            'cout_etudes_annuel': 10000
                        }
                    st.session_state.projection_settings[prenom]['debut_etudes'] = st.number_input(f"Âge de début des études de {prenom}", 15, 25, st.session_state.projection_settings[prenom]['debut_etudes'], key=f"debut_{prenom}")
                    st.session_state.projection_settings[prenom]['duree_etudes'] = st.number_input(f"Durée des études de {prenom} (ans)", 1, 8, st.session_state.projection_settings[prenom]['duree_etudes'], key=f"duree_{prenom}")
                    st.session_state.projection_settings[prenom]['cout_etudes_annuel'] = st.number_input(f"Coût annuel des études de {prenom} (€)", 0, 50000, st.session_state.projection_settings[prenom].get('cout_etudes_annuel', 10000), step=500, key=f"cout_etudes_{prenom}")
                    st.markdown("---")
    return duree_projection, st.session_state.projection_settings

def display_gantt_chart(gantt_data, duree_projection, parents, enfants):
    """Affiche la frise chronologique (diagramme de Gantt)."""
    st.header("📊 Frise Chronologique du Foyer")
    if not gantt_data:
        st.info("Les données sont insuffisantes ou la période de projection est trop courte pour générer la frise chronologique.")
        return

    fig = create_gantt_chart_fig(gantt_data, duree_projection, parents, enfants)
    if fig:
        st.plotly_chart(fig, use_container_width=True)

def display_loan_crd_chart(df_projection, passifs):
    """Affiche un graphique de l'évolution du Capital Restant Dû des prêts."""
    if not passifs:
        st.info("Aucun passif (prêt) renseigné.")
        return

    # 1. Préparation des données pour le graphique
    loan_options = {p['id']: p.get('libelle') or f"Prêt {p['id'][:4]}..." for p in passifs}
    crd_columns = [col for col in df_projection.columns if col.startswith('CRD_')]
    
    if not crd_columns:
        st.info("Aucune donnée de Capital Restant Dû à afficher.")
        return

    df_crd = df_projection[['Année'] + crd_columns].copy()
    df_crd.columns = ['Année'] + [loan_options.get(col.replace('CRD_', ''), col) for col in df_crd.columns[1:]]
    df_crd = df_crd.set_index('Année')

    # 2. Création du graphique
    fig = px.bar(df_crd, x=df_crd.index, y=df_crd.columns, title="Répartition du Capital Restant Dû par Emprunt", labels={'value': "Capital Restant Dû (€)", 'index': "Année", 'variable': 'Prêt'})
    fig.update_layout(barmode='stack', yaxis_title="Capital Restant Dû (€)", xaxis_title="Année", legend_title_text='Prêts')

    st.plotly_chart(fig, use_container_width=True)

def display_projection_table(df_projection):
    """Affiche le tableau de la projection financière."""
    st.subheader("Tableau de projection")
    df_display = df_projection.copy()

    # Identifier les colonnes monétaires à formater pour éviter les erreurs sur les colonnes de texte (Statut) ou d'âge.
    money_cols = [
        col for col in df_display.columns
        if 'Revenu' in col
        or 'Impôt' in col
        or 'Dépenses' in col
        or 'Reste à vivre' in col
        or 'Prêts' in col
        or 'Charges' in col
        or 'Taxes' in col
        or 'Coût' in col
        or 'Loyers' in col
        or 'Prélèvements' in col
    ]
    format_dict = {col: '{:,.0f} €' for col in money_cols}
    st.dataframe(df_display.style.format(format_dict), use_container_width=True)

def display_projection_chart(df_projection):
    """Affiche le graphique de la projection financière."""
    st.subheader("Graphique de répartition des revenus")

    # Définir les colonnes à empiler, dans l'ordre souhaité
    cols_to_stack = [
        'Reste à vivre',
        'Prélèvements Sociaux',
        'Impôt sur le revenu',
        'Coût des études',
        'Autres Dépenses',
        'Taxes Foncières',
        'Charges Immobilières',
        'Mensualités Prêts'
    ]

    # Filtrer les colonnes qui existent réellement dans le df pour éviter les erreurs
    existing_cols_to_stack = [col for col in cols_to_stack if col in df_projection.columns]

    # Créer le graphique à barres empilées
    fig_bar = px.bar(
        df_projection,
        x='Année',
        y=existing_cols_to_stack,
        title="Répartition des revenus du foyer (Dépenses + Reste à vivre)",
        labels={'value': 'Montant (€)', 'variable': 'Catégorie'},
        height=500
    )

    # Ajouter une ligne pour le total des revenus pour référence
    if 'Revenus du foyer' in df_projection.columns:
        fig_bar.add_scatter(
            x=df_projection['Année'],
            y=df_projection['Revenus du foyer'],
            mode='lines',
            name='Total des Revenus',
            line=dict(color='black', width=2, dash='dot')
        )

    fig_bar.update_layout(barmode='stack', yaxis_title='Montant (€)', xaxis_title='Année', legend_title_text='Postes de dépenses et Reste à vivre')
    st.plotly_chart(fig_bar, use_container_width=True)

def display_annual_tax_chart(df_projection):
    """Affiche le graphique de l'évolution de la fiscalité annuelle."""
    st.subheader("Évolution de la fiscalité annuelle")
    st.markdown("Ce graphique montre le montant de l'impôt sur le revenu et des prélèvements sociaux payés chaque année.")

    df_fiscalite = df_projection[['Année', 'Impôt sur le revenu', 'Prélèvements Sociaux']].copy()
    
    # Utiliser melt pour avoir un format long adapté à px.bar avec color
    df_plot = df_fiscalite.melt(id_vars=['Année'], value_vars=['Impôt sur le revenu', 'Prélèvements Sociaux'],
                                var_name='Type de fiscalité', value_name='Montant')

    fig = px.bar(
        df_plot,
        x='Année',
        y='Montant',
        color='Type de fiscalité',
        title="Fiscalité annuelle (Impôt sur le Revenu + Prélèvements Sociaux)",
        labels={'Montant': 'Montant Annuel (€)'},
        height=400,
        barmode='stack',
        color_discrete_map={
            'Impôt sur le revenu': 'indianred',
            'Prélèvements Sociaux': 'lightsalmon'
        }
    )
    
    fig.update_layout(
        yaxis_title='Montant Annuel (€)',
        xaxis_title='Année',
        legend_title_text='Composants'
    )
    st.plotly_chart(fig, use_container_width=True)

def display_cumulative_tax_at_retirement(df_projection, parents, settings):
    """Affiche les métriques du cumul de la fiscalité au départ à la retraite."""
    st.subheader("Cumul de la fiscalité au départ à la retraite")

    df_fiscalite = df_projection[['Année', 'Impôt sur le revenu', 'Prélèvements Sociaux']].copy()
    df_fiscalite['Fiscalité Annuelle'] = df_fiscalite['Impôt sur le revenu'] + df_fiscalite['Prélèvements Sociaux']
    df_fiscalite['Fiscalité Cumulée'] = df_fiscalite['Fiscalité Annuelle'].cumsum()

    if not parents:
        st.info("Aucun parent renseigné pour calculer le cumul.")
        return

    cols = st.columns(len(parents))
    for i, parent in enumerate(parents):
        with cols[i]:
            prenom = parent.get('prenom')
            dob = parent.get('date_naissance')
            if prenom and dob and prenom in settings:
                age_retraite = settings[prenom]['retraite']
                annee_retraite = dob.year + age_retraite

                # Trouver le cumul pour cette année-là
                cumul_data = df_fiscalite[df_fiscalite['Année'] == annee_retraite]
                if not cumul_data.empty:
                    cumul_a_retraite = cumul_data.iloc[0]['Fiscalité Cumulée']
                    st.metric(
                        label=f"Total impôts payés à la retraite de {prenom} ({annee_retraite})",
                        value=f"{cumul_a_retraite:,.0f} €",
                        help="Cumul de l'IR et des PS payés depuis le début de la projection jusqu'à l'année de départ à la retraite incluse."
                    )
                else:
                    st.metric(
                        label=f"Total impôts payés à la retraite de {prenom} ({annee_retraite})",
                        value="N/A",
                        help=f"L'année de retraite ({annee_retraite}) est en dehors de la période de projection."
                    )
