import streamlit as st
import pandas as pd
import plotly.express as px
from core.projection_logic import calculate_age
from core.charts import create_gantt_chart_fig

def display_settings_ui(parents, enfants):
    """Affiche les widgets pour configurer les paramètres de la projection."""
    with st.expander("⚙️ Paramètres de la projection", expanded=True):
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
    return st.session_state.projection_settings

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

    # 3. Ajouter les montants totaux au sommet de chaque barre
    # Calculer les totaux par année
    totaux_par_annee = df_crd.sum(axis=1)
    
    # Ajouter les annotations avec les montants en k€
    for annee, total in totaux_par_annee.items():
        if total > 0:  # Seulement si il y a un montant à afficher
            fig.add_annotation(
                x=annee,
                y=total,
                text=f"<b>{total/1000:.0f}k€</b>",
                showarrow=False,
                font=dict(color="black", size=12, family="Arial Black"),
                bgcolor="rgba(255,255,255,0.8)",  # Fond blanc semi-transparent
                bordercolor="black",
                borderwidth=1,
                xanchor='center',
                yanchor='bottom',
                yshift=5  # Décalage vers le haut
            )

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
    
    if not parents:
        st.info("Aucun parent renseigné pour l'analyse de transition.")
        return
    
    if df_projection.empty:
        st.warning("Aucune donnée de projection disponible pour l'analyse.")
        return
    
    # Identifier les années de départ à la retraite des parents
    annees_retraite = []
    for parent in parents:
        prenom = parent.get('prenom')
        dob = parent.get('date_naissance')
        
        if prenom and dob and prenom in settings:
            age_retraite = settings[prenom]['retraite']
            annee_retraite = dob.year + age_retraite
            annees_retraite.append((annee_retraite, prenom))
    
    if not annees_retraite:
        st.warning("Informations manquantes pour calculer les années de départ à la retraite.")
        return
    
    # Trier les années de retraite
    annees_retraite.sort()
    premiere_retraite = annees_retraite[0][0]
    
    # Créer les options pour les selectbox
    annees_disponibles = sorted(df_projection['Année'].unique())
    
    # Options pour l'année 1 (situation actuelle et années avant départs)
    options_annee1 = {}
    annee_actuelle = min(annees_disponibles)
    options_annee1[f"Situation actuelle ({annee_actuelle})"] = annee_actuelle
    
    # Ajouter les années avant chaque départ à la retraite
    for annee_retraite, prenom in annees_retraite:
        annee_avant_retraite = annee_retraite - 1
        if annee_avant_retraite in annees_disponibles and annee_avant_retraite != annee_actuelle:
            if len(annees_retraite) == 1:
                # Un seul parent
                options_annee1[f"Année avant départ ({annee_avant_retraite})"] = annee_avant_retraite
            else:
                # Plusieurs parents - spécifier le nom
                options_annee1[f"Avant retraite de {prenom} ({annee_avant_retraite})"] = annee_avant_retraite
    
    # Options pour l'année 2 (années après les départs à la retraite)
    options_annee2 = {}
    for annee_retraite, prenom in annees_retraite:
        if annee_retraite in annees_disponibles:
            if len(annees_retraite) == 1:
                options_annee2[f"Première année de retraite ({annee_retraite})"] = annee_retraite
            else:
                options_annee2[f"Retraite de {prenom} ({annee_retraite})"] = annee_retraite
    
    # Ajouter les années suivantes si disponibles
    for annee in annees_disponibles:
        if annee > premiere_retraite and annee not in [ar[0] for ar in annees_retraite]:
            options_annee2[f"Année {annee}"] = annee
    
    if not options_annee2:
        st.warning("Aucune année de retraite disponible dans les données de projection.")
        return
    
    # Interface de sélection des années
    st.markdown("### � Sélection des années à comparer")
    
    col1, col2 = st.columns(2)
    
    with col1:
        annee1_key = st.selectbox(
            "Année 1 (référence)",
            options=list(options_annee1.keys()),
            index=0,
            key="transition_annee1_selectbox",
            help="Choisissez l'année de référence (situation avant retraite)"
        )
        annee1 = options_annee1[annee1_key]
    
    with col2:
        annee2_key = st.selectbox(
            "Année 2 (comparaison)",
            options=list(options_annee2.keys()),
            index=0,
            key="transition_annee2_selectbox",
            help="Choisissez l'année de comparaison (situation après retraite)"
        )
        annee2 = options_annee2[annee2_key]
    
    # Vérifier que les années sont différentes
    if annee1 == annee2:
        st.error("⚠️ Veuillez sélectionner deux années différentes pour la comparaison.")
        return
    
    st.info(f"📊 **Comparaison sélectionnée :** {annee1_key} vs {annee2_key}")
    
    # Filtrer les données pour les deux années sélectionnées
    df_transition = df_projection[
        df_projection['Année'].isin([annee1, annee2])
    ].copy()
    
    if df_transition.empty:
        st.warning(f"Aucune donnée disponible pour les années {annee1} et {annee2}.")
        return
    
    # Préparer les données pour le graphique (conversion en montants mensuels)
    # Ordre des catégories simplifiées avec regroupement fiscal
    categories_ordre = [
        'Reste à vivre',
        'Fiscalité & Taxes',  # Regroupement IR + PS + Taxes Foncières
        'Coût des études',
        'Autres Dépenses',
        'Charges Immobilières',
        'Mensualités Prêts'
    ]
    
    donnees_graphique = []
    for _, row in df_transition.iterrows():
        annee = int(row['Année'])
        if annee == annee1:
            label_annee = f"Année {annee}\n({annee1_key.split('(')[0].strip()})"
        else:
            label_annee = f"Année {annee}\n({annee2_key.split('(')[0].strip()})"
        
        # Regrouper les catégories fiscales
        fiscalite_total = (
            row.get('Prélèvements Sociaux', 0) +
            row.get('Impôt sur le revenu', 0) +
            row.get('Taxes Foncières', 0)
        )
        
        # Conversion des montants annuels en mensuels et empilement
        # Logique identique aux graphiques de projection : empiler toutes les composantes
        categories_donnees = {
            'Reste à vivre': row.get('Reste à vivre', 0),
            'Fiscalité & Taxes': fiscalite_total,
            'Coût des études': row.get('Coût des études', 0),
            'Autres Dépenses': row.get('Autres Dépenses', 0),
            'Charges Immobilières': row.get('Charges Immobilières', 0),
            'Mensualités Prêts': row.get('Mensualités Prêts', 0)
        }
        
        for categorie in categories_ordre:
            if categorie in categories_donnees and categories_donnees[categorie] > 0:
                montant_mensuel = categories_donnees[categorie] / 12
                donnees_graphique.append({
                    'Période': label_annee, 
                    'Type': categorie, 
                    'Montant': montant_mensuel, 
                    'Valeur_num': montant_mensuel
                })
    
    df_graph = pd.DataFrame(donnees_graphique)
    
    # Créer le graphique en barres empilées avec les mêmes couleurs que les projections
    import plotly.express as px
    
    # Carte de couleurs cohérente avec les graphiques de projection (adaptée aux nouvelles catégories)
    couleurs_projection = [
        '#636EFA',  # Reste à vivre (bleu)
        '#EF553B',  # Fiscalité & Taxes (rouge - regroupement IR+PS+Taxes)
        '#AB63FA',  # Coût des études (violet)
        '#FFA15A',  # Autres Dépenses (orange)
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
        if annee == annee1:
            label_annee = f"Année {annee}\n({annee1_key.split('(')[0].strip()})"
        else:
            label_annee = f"Année {annee}\n({annee2_key.split('(')[0].strip()})"
        
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
        barmode='stack',  # Mode empilé comme les projections
        width=800,  # Largeur fixe du graphique pour contrôler l'espacement
        bargap=0.6  # Augmenter l'espacement entre les barres pour les rendre plus élancées
    )
    
    # Réduire significativement la largeur des barres pour un aspect plus élancé
    fig.update_traces(width=0.25, selector=dict(type='bar'))
    
    # Ajouter les valeurs au centre de chaque barre (solution anti-superposition avancée)
    # Calculer les positions Y pour centrer le texte dans chaque segment
    for periode in df_graph['Période'].unique():
        df_periode = df_graph[df_graph['Période'] == periode].copy()
        
        # Trier selon l'ordre des catégories pour calculer les positions correctement
        df_periode['ordre'] = df_periode['Type'].map({cat: i for i, cat in enumerate(categories_ordre)})
        df_periode = df_periode.sort_values('ordre')
        
        # Calculer le total pour cette période pour déterminer la stratégie d'affichage
        total_periode = df_periode['Montant'].sum()
        
        # Calculer les positions Y cumulées et déterminer quels montants afficher
        cumul = 0
        annotations_a_afficher = []
        
        for _, row in df_periode.iterrows():
            montant = row['Montant']
            categorie = row['Type']
            if montant > 0:  # Seulement pour les montants positifs
                # Position Y au centre du segment
                y_position = cumul + (montant / 2)
                
                # Calculer la hauteur du segment pour déterminer si on peut afficher
                hauteur_segment = montant
                pourcentage_du_total = (montant / total_periode) * 100 if total_periode > 0 else 0
                
                # Critères d'affichage plus stricts pour éviter les superpositions
                afficher_montant = False
                font_size = 10
                
                if hauteur_segment >= 300 and pourcentage_du_total >= 15:
                    # Segments larges et significatifs - afficher catégorie + montant
                    afficher_montant = True
                    font_size = 11
                elif hauteur_segment >= 200 and pourcentage_du_total >= 10:
                    # Segments moyens - afficher catégorie + montant
                    afficher_montant = True
                    font_size = 10
                elif hauteur_segment >= 150 and pourcentage_du_total >= 8:
                    # Petits segments - afficher seulement le montant
                    afficher_montant = True
                    font_size = 9
                
                # Formater le texte selon la taille du segment
                if montant >= 1000:
                    text_montant = f"{montant/1000:.1f}k€"
                else:
                    text_montant = f"{montant:.0f}€"
                
                # Créer le texte d'annotation avec ou sans catégorie selon l'espace
                if hauteur_segment >= 200 and pourcentage_du_total >= 10:
                    # Segments suffisamment grands : afficher catégorie + montant avec style élégant
                    categorie_courte = {
                        'Reste à vivre': 'Reste à vivre',
                        'Fiscalité & Taxes': 'Fiscalité', 
                        'Coût des études': 'Études',
                        'Autres Dépenses': 'Autres',
                        'Charges Immobilières': 'Charges Immo',
                        'Mensualités Prêts': 'Prêts'
                    }.get(categorie, categorie)
                    
                    # Formatage simplifié sans séparateurs décoratifs
                    text_annotation = f"{categorie_courte}\n{text_montant}"
                else:
                    # Petits segments : seulement le montant
                    text_annotation = text_montant
                
                if afficher_montant:
                    annotations_a_afficher.append({
                        'x': periode,
                        'y': y_position,
                        'text': text_annotation,
                        'font_size': font_size,
                        'hauteur': hauteur_segment,
                        'categorie': categorie
                    })
                
                cumul += montant
        
        # Vérifier et ajuster les annotations pour éviter les superpositions
        # Trier par position Y pour détecter les conflits
        annotations_a_afficher.sort(key=lambda x: x['y'])
        
        # Filtrer les annotations trop proches (éviter superposition)
        annotations_finales = []
        derniere_y = -1000  # Position très basse pour commencer
        
        for ann in annotations_a_afficher:
            # Distance minimale entre les annotations (en pixels approximatifs)
            distance_min = 40  # Ajustable selon la hauteur du graphique
            
            if ann['y'] - derniere_y >= distance_min:
                annotations_finales.append(ann)
                derniere_y = ann['y']
            elif len(annotations_finales) == 0:
                # Garder au moins une annotation si c'est la première
                annotations_finales.append(ann)
                derniere_y = ann['y']
        
        # Si on a trop peu d'annotations visibles, garder les plus importantes
        if len(annotations_finales) < len(annotations_a_afficher) and len(annotations_finales) < 3:
            # Reprendre les 2-3 segments les plus importants
            annotations_importantes = sorted(annotations_a_afficher, 
                                           key=lambda x: x['hauteur'], 
                                           reverse=True)[:3]
            
            # Espacer verticalement ces annotations importantes
            if len(annotations_importantes) > 1:
                annotations_finales = []
                for i, ann in enumerate(annotations_importantes):
                    # Espacer les annotations sur la hauteur disponible
                    espacement = total_periode / (len(annotations_importantes) + 1)
                    nouvelle_y = espacement * (i + 1)
                    ann['y'] = nouvelle_y
                    annotations_finales.append(ann)
            else:
                annotations_finales = annotations_importantes
        
        # Ajouter les annotations finales au graphique avec un style amélioré
        for ann in annotations_finales:
            # Définir les couleurs selon la catégorie pour plus de cohérence
            couleur_fond = {
                'Reste à vivre': 'rgba(99, 110, 250, 0.9)',  # Bleu - correspond à #636EFA
                'Fiscalité': 'rgba(239, 85, 59, 0.9)',       # Rouge - correspond à #EF553B  
                'Études': 'rgba(171, 99, 250, 0.9)',         # Violet - correspond à #AB63FA
                'Autres': 'rgba(255, 161, 90, 0.9)',         # Orange - correspond à #FFA15A
                'Charges Immo': 'rgba(255, 102, 146, 0.9)',  # Rose - correspond à #FF6692
                'Prêts': 'rgba(182, 232, 128, 0.9)'          # Vert clair - correspond à #B6E880
            }
            
            # Extraire la catégorie du texte d'annotation
            categorie_key = ann['text'].split('\n')[0] if '\n' in ann['text'] else 'Autres'
            bg_color = couleur_fond.get(categorie_key, 'rgba(50, 50, 50, 0.85)')
            
            fig.add_annotation(
                x=ann['x'],
                y=ann['y'],
                text=f"<b style='color:white;'>{ann['text']}</b>",
                showarrow=False,
                font=dict(
                    color="white", 
                    size=ann['font_size'], 
                    family="Inter, -apple-system, BlinkMacSystemFont, sans-serif"
                ),
                bgcolor=bg_color,
                bordercolor="rgba(255, 255, 255, 0.3)",
                borderwidth=1,
                borderpad=4,
                xanchor='center',
                yanchor='middle',
                # Ajouter un effet d'ombre
                opacity=0.95,
                # Coins arrondis simulés avec du padding
                width=None,
                height=None
            )
    
    st.plotly_chart(fig, use_container_width=False, width=800)
    
    # Calcul des KPI de comparaison (en montants mensuels)
    data_annee1 = df_transition[df_transition['Année'] == annee1].iloc[0]
    data_annee2 = df_transition[df_transition['Année'] == annee2].iloc[0]
    
    # Conversion en montants mensuels
    revenus_annee1_mensuel = data_annee1['Revenus du foyer'] / 12
    revenus_annee2_mensuel = data_annee2['Revenus du foyer'] / 12
    reste_annee1_mensuel = data_annee1['Reste à vivre'] / 12
    reste_annee2_mensuel = data_annee2['Reste à vivre'] / 12
    
    # Calcul des ratios
    ratio_revenus = (revenus_annee2_mensuel / revenus_annee1_mensuel) if revenus_annee1_mensuel > 0 else 0
    ratio_reste_vivre = (reste_annee2_mensuel / reste_annee1_mensuel) if reste_annee1_mensuel > 0 else 0
    
    # Affichage des KPI
    st.markdown("### 📊 Indicateurs de transition (montants mensuels)")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label=f"Revenus {annee1}",
            value=f"{revenus_annee1_mensuel:,.0f} €/mois",
            help=f"Revenus mensuels moyens pendant l'année {annee1}"
        )
    
    with col2:
        variation_revenus = revenus_annee2_mensuel - revenus_annee1_mensuel
        st.metric(
            label=f"Revenus {annee2}",
            value=f"{revenus_annee2_mensuel:,.0f} €/mois",
            delta=f"{variation_revenus:,.0f} €",
            help=f"Revenus mensuels moyens pendant l'année {annee2}"
        )
    
    with col3:
        st.metric(
            label=f"Reste à vivre {annee1}",
            value=f"{reste_annee1_mensuel:,.0f} €/mois",
            help=f"Capacité d'épargne mensuelle moyenne pendant l'année {annee1}"
        )
    
    with col4:
        variation_reste_vivre = reste_annee2_mensuel - reste_annee1_mensuel
        st.metric(
            label=f"Reste à vivre {annee2}",
            value=f"{reste_annee2_mensuel:,.0f} €/mois",
            delta=f"{variation_reste_vivre:,.0f} €",
            help=f"Capacité d'épargne mensuelle moyenne pendant l'année {annee2}"
        )
    
    # Ratios
    st.markdown("### 🎯 Ratios de transition")
    col1, col2 = st.columns(2)
    
    with col1:
        couleur_revenus = "normal" if ratio_revenus >= 0.8 else "inverse"
        st.metric(
            label=f"Ratio Revenus ({annee2}/{annee1})",
            value=f"{ratio_revenus:.1%}",
            delta=f"{(ratio_revenus - 1):.1%}",
            delta_color=couleur_revenus,
            help=f"Pourcentage de maintien des revenus mensuels entre {annee1} et {annee2}"
        )
    
    with col2:
        couleur_reste = "normal" if ratio_reste_vivre >= 0.8 else "inverse"
        st.metric(
            label=f"Ratio Reste à vivre ({annee2}/{annee1})",
            value=f"{ratio_reste_vivre:.1%}",
            delta=f"{(ratio_reste_vivre - 1):.1%}",
            delta_color=couleur_reste,
            help=f"Pourcentage de maintien de la capacité d'épargne mensuelle entre {annee1} et {annee2}"
        )
    
    # Tableau détaillé de comparaison
    st.markdown("### 📋 Détail de la comparaison par catégorie (montants mensuels)")
    
    # Préparation des données pour le tableau
    # Colonnes d'intérêt et leurs libellés - toutes les catégories du graphique
    colonnes_comparaison = {
        # Revenus
        'Revenus bruts du foyer': '💼 Salaires et pensions',
        'Loyers perçus': '�️ Revenus locatifs',
        'Autres revenus': '💰 Autres revenus',
        'Revenus du foyer': '📊 TOTAL REVENUS',
        # Charges et dépenses (toutes les catégories du graphique)
        'Mensualités Prêts': '🏠 Mensualités Prêts',
        'Charges Immobilières': '🔧 Charges Immobilières',
        'Taxes Foncières': '🏛️ Taxes Foncières',
        'Autres Dépenses': '🛒 Autres Dépenses',
        'Coût des études': '🎓 Coût des études',
        'Impôt sur le revenu': '💸 Impôt sur le revenu',
        'Prélèvements Sociaux': '🏥 Prélèvements Sociaux',
        # Totaux et résultats
        'Total charges': '📊 TOTAL CHARGES',
        'Reste à vivre': '💎 RESTE À VIVRE'
    }
    
    # Création du tableau de comparaison
    data_tableau = []
    
    for colonne, libelle in colonnes_comparaison.items():
        if colonne in data_annee1.index and colonne in data_annee2.index:
            montant_annuel_annee1 = data_annee1[colonne]
            montant_annuel_annee2 = data_annee2[colonne]
            
            # Conversion en montants mensuels
            montant_mensuel_annee1 = montant_annuel_annee1 / 12
            montant_mensuel_annee2 = montant_annuel_annee2 / 12
            
            # Calcul de la variation mensuelle
            variation_mensuelle = montant_mensuel_annee2 - montant_mensuel_annee1
            variation_pourcentage = (variation_mensuelle / montant_mensuel_annee1 * 100) if montant_mensuel_annee1 != 0 else 0
            
            # Déterminer le type de ligne pour le style
            is_total_line = 'TOTAL' in colonne or 'RESTE À VIVRE' in colonne
            
            data_tableau.append({
                'Catégorie': libelle,
                f'{annee1} (€/mois)': f"{montant_mensuel_annee1:,.0f}",
                f'{annee2} (€/mois)': f"{montant_mensuel_annee2:,.0f}",
                'Variation (€/mois)': f"{variation_mensuelle:+,.0f}",
                'Variation (%)': f"{variation_pourcentage:+.1f}%",
                'is_total': is_total_line
            })
    
    df_tableau = pd.DataFrame(data_tableau)
    
    # Séparer les données par type pour un meilleur affichage
    df_revenus = df_tableau[df_tableau['Catégorie'].str.contains('💼|�️|💰|📊.*REVENUS')]
    df_charges = df_tableau[df_tableau['Catégorie'].str.contains('🏠|🔧|🏛️|🛒|🎓|💸|🏥')]
    df_totaux = df_tableau[df_tableau['Catégorie'].str.contains('📊.*CHARGES|💎')]
    
    # Fonction de style pour le tableau
    def style_tableau_complet(df):
        """Applique un style selon le type de ligne"""
        styles = []
        for _, row in df.iterrows():
            if row.get('is_total', False):
                styles.append(['background-color: #f0f0f0; font-weight: bold'] * (len(row) - 1))
            else:
                styles.append([''] * (len(row) - 1))
        return styles
    
    def color_variation(val):
        """Colore les variations selon leur signe"""
        if isinstance(val, str):
            if val.startswith('+') and not val.startswith('+0'):
                return 'color: green; font-weight: bold'
            elif val.startswith('-'):
                return 'color: red; font-weight: bold'
        return ''
    
    # Affichage des tableaux par section avec largeurs de colonnes optimisées
    if not df_revenus.empty:
        st.markdown("#### 💰 Revenus")
        df_revenus_display = df_revenus.drop('is_total', axis=1)
        styled_revenus = df_revenus_display.style.apply(
            lambda x: ['background-color: #f0f0f0; font-weight: bold'] * len(x) if '📊' in x['Catégorie'] else [''] * len(x), 
            axis=1
        )
        styled_revenus = styled_revenus.applymap(color_variation, subset=['Variation (€/mois)', 'Variation (%)'])
        
        st.dataframe(
            styled_revenus, 
            use_container_width=False,
            hide_index=True,
            column_config={
                "Catégorie": st.column_config.TextColumn("Catégorie", width="medium"),
                f"{annee1} (€/mois)": st.column_config.TextColumn(f"{annee1} (€/mois)", width="small"),
                f"{annee2} (€/mois)": st.column_config.TextColumn(f"{annee2} (€/mois)", width="small"),
                "Variation (€/mois)": st.column_config.TextColumn("Variation (€/mois)", width="small"),
                "Variation (%)": st.column_config.TextColumn("Variation (%)", width="small")
            }
        )
    
    if not df_charges.empty:
        st.markdown("#### 💳 Charges et dépenses")
        df_charges_display = df_charges.drop('is_total', axis=1)
        styled_charges = df_charges_display.style.apply(lambda x: [''] * len(x), axis=1)
        styled_charges = styled_charges.applymap(color_variation, subset=['Variation (€/mois)', 'Variation (%)'])
        
        st.dataframe(
            styled_charges, 
            use_container_width=False,
            hide_index=True,
            column_config={
                "Catégorie": st.column_config.TextColumn("Catégorie", width="medium"),
                f"{annee1} (€/mois)": st.column_config.TextColumn(f"{annee1} (€/mois)", width="small"),
                f"{annee2} (€/mois)": st.column_config.TextColumn(f"{annee2} (€/mois)", width="small"),
                "Variation (€/mois)": st.column_config.TextColumn("Variation (€/mois)", width="small"),
                "Variation (%)": st.column_config.TextColumn("Variation (%)", width="small")
            }
        )
    
    if not df_totaux.empty:
        st.markdown("#### 📊 Synthèse")
        df_totaux_display = df_totaux.drop('is_total', axis=1)
        styled_totaux = df_totaux_display.style.apply(
            lambda x: ['background-color: #f0f0f0; font-weight: bold'] * len(x), axis=1
        )
        styled_totaux = styled_totaux.applymap(color_variation, subset=['Variation (€/mois)', 'Variation (%)'])
        
        st.dataframe(
            styled_totaux, 
            use_container_width=False,
            hide_index=True,
            column_config={
                "Catégorie": st.column_config.TextColumn("Catégorie", width="medium"),
                f"{annee1} (€/mois)": st.column_config.TextColumn(f"{annee1} (€/mois)", width="small"),
                f"{annee2} (€/mois)": st.column_config.TextColumn(f"{annee2} (€/mois)", width="small"),
                "Variation (€/mois)": st.column_config.TextColumn("Variation (€/mois)", width="small"),
                "Variation (%)": st.column_config.TextColumn("Variation (%)", width="small")
            }
        )
    
    # Note explicative
    st.caption(
        f"💡 **Note :** Ce tableau compare les montants mensuels entre {annee1} (dernière année avant retraite) "
        f"et {annee2} (première année de retraite complète). Les variations positives sont en vert, "
        f"les négatives en rouge. Toutes les catégories correspondent exactement aux segments du graphique ci-dessus."
    )
