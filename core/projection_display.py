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

def display_retirement_transition_analysis(df_projection, parents, settings):
    """Affiche l'analyse de la transition vers la retraite avec graphiques en barres et KPI."""
    st.subheader("🔍 Transition vers la retraite")
    st.markdown("Comparaison de la situation financière entre le dernier mois d'activité (décembre N-1) et le premier mois de retraite (janvier N).")
    
    if not parents:
        st.info("Aucun parent renseigné pour l'analyse de transition.")
        return
    
    # Trouver l'année de départ à la retraite (prendre le premier parent)
    premier_parent = parents[0]
    prenom = premier_parent.get('prenom')
    dob = premier_parent.get('date_naissance')
    
    if not prenom or not dob or prenom not in settings:
        st.warning("Informations manquantes pour calculer l'année de départ à la retraite.")
        return
    
    age_retraite = settings[prenom]['retraite']
    annee_retraite = dob.year + age_retraite
    annee_avant_retraite = annee_retraite - 1
    
    st.info(f"📅 Analyse basée sur le départ à la retraite de **{prenom}** en **janvier {annee_retraite}** (à {age_retraite} ans)")
    st.caption(f"Comparaison : **Année {annee_avant_retraite}** (dernière année d'activité) vs **Année {annee_retraite}** (première année de retraite)")
    st.markdown(f"💡 *Équivalent à comparer Décembre {annee_avant_retraite} vs Janvier {annee_retraite} en termes de revenus mensuels*")
    
    # Filtrer les données pour les deux années clés
    df_transition = df_projection[
        df_projection['Année'].isin([annee_avant_retraite, annee_retraite])
    ].copy()
    
    if df_transition.empty:
        st.warning(f"Aucune donnée disponible pour les années {annee_avant_retraite} et {annee_retraite}.")
        return
    
    # Préparer les données pour le graphique (conversion en montants mensuels)
    # Ordre des catégories identique aux graphiques de projection
    categories_ordre = [
        'Reste à vivre',
        'Prélèvements Sociaux', 
        'Impôt sur le revenu',
        'Coût des études',
        'Autres Dépenses',
        'Taxes Foncières',
        'Charges Immobilières',
        'Mensualités Prêts'
    ]
    
    donnees_graphique = []
    for _, row in df_transition.iterrows():
        annee = int(row['Année'])
        if annee == annee_avant_retraite:
            label_annee = f"Année {annee}\n(Dernière année d'activité)"
        else:
            label_annee = f"Année {annee}\n(Première année de retraite)"
        
        # Conversion des montants annuels en mensuels et empilement
        # Logique identique aux graphiques de projection : empiler toutes les composantes
        for categorie in categories_ordre:
            if categorie in row and row[categorie] > 0:
                montant_mensuel = row[categorie] / 12
                donnees_graphique.append({
                    'Période': label_annee, 
                    'Type': categorie, 
                    'Montant': montant_mensuel, 
                    'Valeur_num': montant_mensuel
                })
    
    df_graph = pd.DataFrame(donnees_graphique)
    
    # Créer le graphique en barres empilées avec les mêmes couleurs que les projections
    import plotly.express as px
    
    # Carte de couleurs cohérente avec les graphiques de projection
    # Utiliser les couleurs par défaut de Plotly dans le même ordre que les projections
    couleurs_projection = [
        '#636EFA',  # Reste à vivre (bleu)
        '#EF553B',  # Prélèvements Sociaux (rouge)
        '#00CC96',  # Impôt sur le revenu (vert)
        '#AB63FA',  # Coût des études (violet)
        '#FFA15A',  # Autres Dépenses (orange)
        '#19D3F3',  # Taxes Foncières (cyan)
        '#FF6692',  # Charges Immobilières (rose)
        '#B6E880',  # Mensualités Prêts (vert clair)
    ]
    
    color_discrete_map = {}
    for i, categorie in enumerate(categories_ordre):
        if i < len(couleurs_projection):
            color_discrete_map[categorie] = couleurs_projection[i]
    
    fig = px.bar(
        df_graph,
        x='Période',
        y='Montant',
        color='Type',
        title="Comparaison des revenus mensuels : Répartition par poste de dépense",
        labels={'Montant': 'Montant Mensuel (€)', 'Période': ''},
        height=500,
        color_discrete_map=color_discrete_map,
        category_orders={'Type': categories_ordre}
    )
    
    # Ajouter une ligne pour les revenus totaux (référence)
    periodes = []
    revenus = []
    for _, row in df_transition.iterrows():
        annee = int(row['Année'])
        if annee == annee_avant_retraite:
            label_annee = f"Année {annee}\n(Dernière année d'activité)"
        else:
            label_annee = f"Année {annee}\n(Première année de retraite)"
        
        periodes.append(label_annee)
        revenus.append(row['Revenus du foyer'] / 12)
    
    fig.add_scatter(
        x=periodes,
        y=revenus,
        mode='markers+text',
        name='Total Revenus',
        text=[f"<b>{r:,.0f}€</b>" for r in revenus],  # Texte en gras
        textposition="top center",
        textfont=dict(size=16, color='red'),  # Police plus grande et rouge
        marker=dict(color='red', size=12, symbol='diamond'),
        showlegend=True
    )
    
    # Personnaliser l'affichage
    fig.update_layout(
        yaxis_title='Montant Mensuel (€)',
        xaxis_title='',
        legend_title_text='Postes de dépenses',
        barmode='stack'  # Mode empilé comme les projections
    )
    
    # Réduire la largeur des barres pour l'esthétique (seulement les barres, pas les scatter)
    fig.update_traces(width=0.5, selector=dict(type='bar'))
    
    # Ajouter les valeurs au centre de chaque barre
    # Calculer les positions Y pour centrer le texte dans chaque segment
    for periode in df_graph['Période'].unique():
        df_periode = df_graph[df_graph['Période'] == periode].copy()
        
        # Trier selon l'ordre des catégories pour calculer les positions correctement
        df_periode['ordre'] = df_periode['Type'].map({cat: i for i, cat in enumerate(categories_ordre)})
        df_periode = df_periode.sort_values('ordre')
        
        # Calculer les positions Y cumulées pour centrer le texte
        cumul = 0
        for _, row in df_periode.iterrows():
            montant = row['Montant']
            if montant > 0:  # Seulement pour les montants positifs
                # Position Y au centre du segment
                y_position = cumul + (montant / 2)
                
                # Ajouter l'annotation avec police plus grande
                fig.add_annotation(
                    x=periode,
                    y=y_position,
                    text=f"{montant:,.0f}€",
                    showarrow=False,
                    font=dict(color="white", size=14, family="Arial Black"),
                    bgcolor="rgba(0,0,0,0.3)",  # Fond semi-transparent pour la lisibilité
                    bordercolor="white",
                    borderwidth=1
                )
                
                cumul += montant
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Calcul des KPI de comparaison (en montants mensuels)
    data_avant = df_transition[df_transition['Année'] == annee_avant_retraite].iloc[0]
    data_retraite = df_transition[df_transition['Année'] == annee_retraite].iloc[0]
    
    # Conversion en montants mensuels
    revenus_avant_mensuel = data_avant['Revenus du foyer'] / 12
    revenus_retraite_mensuel = data_retraite['Revenus du foyer'] / 12
    reste_avant_mensuel = data_avant['Reste à vivre'] / 12
    reste_retraite_mensuel = data_retraite['Reste à vivre'] / 12
    
    # Calcul des ratios
    ratio_revenus = (revenus_retraite_mensuel / revenus_avant_mensuel) if revenus_avant_mensuel > 0 else 0
    ratio_reste_vivre = (reste_retraite_mensuel / reste_avant_mensuel) if reste_avant_mensuel > 0 else 0
    
    # Affichage des KPI
    st.markdown("### 📊 Indicateurs de transition (montants mensuels)")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label=f"Revenus {annee_avant_retraite}",
            value=f"{revenus_avant_mensuel:,.0f} €/mois",
            help=f"Revenus mensuels moyens pendant l'année d'activité {annee_avant_retraite}"
        )
    
    with col2:
        variation_revenus = revenus_retraite_mensuel - revenus_avant_mensuel
        st.metric(
            label=f"Revenus {annee_retraite}",
            value=f"{revenus_retraite_mensuel:,.0f} €/mois",
            delta=f"{variation_revenus:,.0f} €",
            help=f"Revenus mensuels moyens pendant l'année de retraite {annee_retraite}"
        )
    
    with col3:
        st.metric(
            label=f"Reste à vivre {annee_avant_retraite}",
            value=f"{reste_avant_mensuel:,.0f} €/mois",
            help=f"Capacité d'épargne mensuelle moyenne pendant l'année d'activité {annee_avant_retraite}"
        )
    
    with col4:
        variation_reste_vivre = reste_retraite_mensuel - reste_avant_mensuel
        st.metric(
            label=f"Reste à vivre {annee_retraite}",
            value=f"{reste_retraite_mensuel:,.0f} €/mois",
            delta=f"{variation_reste_vivre:,.0f} €",
            help=f"Capacité d'épargne mensuelle moyenne pendant l'année de retraite {annee_retraite}"
        )
    
    # Ratios
    st.markdown("### 🎯 Ratios de transition")
    col1, col2 = st.columns(2)
    
    with col1:
        couleur_revenus = "normal" if ratio_revenus >= 0.8 else "inverse"
        st.metric(
            label=f"Ratio Revenus ({annee_retraite}/{annee_avant_retraite})",
            value=f"{ratio_revenus:.1%}",
            delta=f"{(ratio_revenus - 1):.1%}",
            delta_color=couleur_revenus,
            help=f"Pourcentage de maintien des revenus mensuels entre {annee_avant_retraite} et {annee_retraite}"
        )
    
    with col2:
        couleur_reste = "normal" if ratio_reste_vivre >= 0.8 else "inverse"
        st.metric(
            label=f"Ratio Reste à vivre ({annee_retraite}/{annee_avant_retraite})",
            value=f"{ratio_reste_vivre:.1%}",
            delta=f"{(ratio_reste_vivre - 1):.1%}",
            delta_color=couleur_reste,
            help=f"Pourcentage de maintien de la capacité d'épargne mensuelle entre {annee_avant_retraite} et {annee_retraite}"
        )
    
    # Analyse textuelle
    st.markdown("### 💡 Analyse de la transition")
    if ratio_revenus >= 0.8:
        st.success(f"✅ **Excellente transition** : Les revenus mensuels sont maintenus à {ratio_revenus:.1%} lors du passage à la retraite.")
    elif ratio_revenus >= 0.6:
        st.warning(f"⚠️ **Transition modérée** : Les revenus mensuels chutent à {ratio_revenus:.1%} lors du passage à la retraite.")
    else:
        st.error(f"🚨 **Transition difficile** : Les revenus mensuels chutent significativement à {ratio_revenus:.1%} lors du passage à la retraite.")
    
    if ratio_reste_vivre >= 0.8:
        st.success(f"✅ **Capacité d'épargne maintenue** : Le reste à vivre mensuel représente {ratio_reste_vivre:.1%} du niveau d'avant retraite.")
    elif ratio_reste_vivre >= 0.5:
        st.warning(f"⚠️ **Capacité d'épargne réduite** : Le reste à vivre mensuel représente {ratio_reste_vivre:.1%} du niveau d'avant retraite.")
    else:
        st.error(f"🚨 **Capacité d'épargne fortement impactée** : Le reste à vivre mensuel ne représente que {ratio_reste_vivre:.1%} du niveau d'avant retraite.")
