import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
from datetime import date

# Palette de couleurs unifiée pour tous les graphiques de la page
# Utilisation de la palette "Vivid" pour des couleurs vives et contrastées.
ASSET_TYPE_COLOR_MAP = {
    'Immobilier de jouissance': px.colors.qualitative.Vivid[0],
    'Immobilier productif': px.colors.qualitative.Vivid[1],
    'Actifs financiers': px.colors.qualitative.Vivid[2],
    'Autres actifs': px.colors.qualitative.Vivid[4],
    'Placements financiers': px.colors.qualitative.Vivid[2], # Pour le graphique "cible"
}

# Palette de couleurs pour les flux (utilise les mêmes couleurs de base que le patrimoine)
FLUX_CATEGORY_COLOR_MAP = {
    'Dépenses courantes': px.colors.qualitative.Vivid[9],      # Orange (même que Immobilier de jouissance)
    'Logement': px.colors.qualitative.Vivid[3],                # Violet-bleu (même que Immobilier productif) 
    'Transport': px.colors.qualitative.Vivid[4],               # Turquoise (même que Actifs financiers)
    'Loisirs': px.colors.qualitative.Vivid[3],                 # Vert clair
    'Impôts et taxes': px.colors.qualitative.Vivid[2],         # Rose-violet (même que Autres actifs)
    'Enfants': px.colors.qualitative.Vivid[5],                 # Vert foncé
    'Santé': px.colors.qualitative.Vivid[6],                   # Jaune-orange
    'Remboursement de prêts': px.colors.qualitative.Vivid[1],  # Bleu
    'Autres': px.colors.qualitative.Vivid[8],                  # Violet foncé
    'Reste à vivre': px.colors.qualitative.Vivid[0],           # Rouge-orange pour l'épargne
}

def create_patrimoine_brut_treemap(df_patrimoine):
    """Crée le treemap de répartition du patrimoine brut."""
    df_brut = df_patrimoine[df_patrimoine['Valeur Brute'] > 0]
    if not df_brut.empty:
        fig = px.treemap(
            df_brut, 
            path=['Type', 'Libellé'], 
            values='Valeur Brute', 
            color='Type', 
            color_discrete_map=ASSET_TYPE_COLOR_MAP,
            hover_data={'Valeur Brute': ':,.2f €'}
        )
        fig.update_traces(
            textinfo='label+percent root+value', 
            texttemplate='<b>%{label}</b><br>%{percentRoot}<br>%{value:,.0f}k€',
            textfont_size=12
        )
        # Conversion des valeurs en k€ pour l'affichage dans le template
        fig.data[0].values = [v/1000 for v in fig.data[0].values]
        fig.update_layout(margin=dict(t=10, l=10, r=10, b=10))
        return fig
    else:
        return None

def create_patrimoine_net_treemap(df_patrimoine):
    """Crée le treemap de répartition du patrimoine net."""
    df_net = df_patrimoine[df_patrimoine['Valeur Nette'] > 0]
    if not df_net.empty:
        fig = px.treemap(
            df_net, 
            path=['Type', 'Libellé'], 
            values='Valeur Nette', 
            color='Type', 
            color_discrete_map=ASSET_TYPE_COLOR_MAP,
            hover_data={'Valeur Nette': ':,.2f €'}
        )
        fig.update_traces(
            textinfo='label+percent root+value', 
            texttemplate='<b>%{label}</b><br>%{percentRoot}<br>%{value:,.0f}k€',
            textfont_size=12
        )
        # Conversion des valeurs en k€ pour l'affichage dans le template
        fig.data[0].values = [v/1000 for v in fig.data[0].values]
        fig.update_layout(margin=dict(t=10, l=10, r=10, b=10))
        return fig
    else:
        return None

def create_patrimoine_net_donut(df_patrimoine):
    """Crée le donut chart de répartition du patrimoine net par type d'actif."""
    df_net_by_type = df_patrimoine[df_patrimoine['Valeur Nette'] > 0].groupby('Type')['Valeur Nette'].sum().reset_index()
    if not df_net_by_type.empty:
        fig = px.pie(
            df_net_by_type,
            names='Type',
            values='Valeur Nette',
            hole=0.4,
            color='Type',
            color_discrete_map=ASSET_TYPE_COLOR_MAP
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(showlegend=True, legend_title_text='Type d\'Actif', margin=dict(t=50, l=10, r=10, b=10))
        return fig
    else:
        return None

def create_patrimoine_ideal_donut():
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
        color_discrete_map=ASSET_TYPE_COLOR_MAP
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(showlegend=True, legend_title_text='Catégorie', margin=dict(t=50, l=10, r=10, b=10))
    return fig

def create_patrimoine_brut_stacked_bar(df_patrimoine):
    """Crée un graphique en barres empilées horizontales pour la répartition brute entre immobilier et financier."""
    if df_patrimoine.empty:
        return None
    
    # Regrouper les données par grandes catégories
    immobilier_brut = df_patrimoine[
        df_patrimoine['Type'].isin(['Immobilier de jouissance', 'Immobilier productif'])
    ]['Valeur Brute'].sum()
    
    financier_brut = df_patrimoine[
        df_patrimoine['Type'] == 'Actifs financiers'
    ]['Valeur Brute'].sum()
    
    autres_brut = df_patrimoine[
        df_patrimoine['Type'] == 'Autres actifs'
    ]['Valeur Brute'].sum()
    
    total = immobilier_brut + financier_brut + autres_brut
    
    if total == 0:
        return None
    
    # Calcul des pourcentages
    immo_pct = (immobilier_brut / total) * 100
    financier_pct = (financier_brut / total) * 100
    autres_pct = (autres_brut / total) * 100
    
    # Création du graphique avec plotly.graph_objects pour avoir un vrai stacked bar
    fig = go.Figure()
    
    # Ajouter les barres empilées
    if immo_pct > 0:
        fig.add_trace(go.Bar(
            name='Immobilier',
            y=['Répartition'],
            x=[immo_pct],
            orientation='h',
            marker_color=px.colors.qualitative.Vivid[0],
            text=f'{immo_pct:.1f}%',
            textposition='inside',
            textfont=dict(color='white', size=12)
        ))
    
    if financier_pct > 0:
        fig.add_trace(go.Bar(
            name='Actifs financiers',
            y=['Répartition'],
            x=[financier_pct],
            orientation='h',
            marker_color=px.colors.qualitative.Vivid[2],
            text=f'{financier_pct:.1f}%',
            textposition='inside',
            textfont=dict(color='white', size=12)
        ))
        
    if autres_pct > 0:
        fig.add_trace(go.Bar(
            name='Autres actifs',
            y=['Répartition'],
            x=[autres_pct],
            orientation='h',
            marker_color=px.colors.qualitative.Vivid[4],
            text=f'{autres_pct:.1f}%',
            textposition='inside',
            textfont=dict(color='white', size=12)
        ))
    
    fig.update_layout(
        title="Répartition Immobilier vs Financier (Brut)",
        title_font_size=12,
        barmode='stack',
        xaxis_title="Pourcentage",
        yaxis_title="",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=120,
        margin=dict(t=50, l=10, r=10, b=10),
        xaxis=dict(range=[0, 100], showgrid=False),
        yaxis=dict(showticklabels=False)
    )
    
    return fig

def create_patrimoine_net_stacked_bar(df_patrimoine):
    """Crée un graphique en barres empilées horizontales pour la répartition nette entre immobilier et financier."""
    if df_patrimoine.empty:
        return None
    
    # Regrouper les données par grandes catégories
    immobilier_net = df_patrimoine[
        df_patrimoine['Type'].isin(['Immobilier de jouissance', 'Immobilier productif'])
    ]['Valeur Nette'].sum()
    
    financier_net = df_patrimoine[
        df_patrimoine['Type'] == 'Actifs financiers'
    ]['Valeur Nette'].sum()
    
    autres_net = df_patrimoine[
        df_patrimoine['Type'] == 'Autres actifs'
    ]['Valeur Nette'].sum()
    
    total = immobilier_net + financier_net + autres_net
    
    if total <= 0:
        return None
    
    # Calcul des pourcentages
    immo_pct = (immobilier_net / total) * 100
    financier_pct = (financier_net / total) * 100
    autres_pct = (autres_net / total) * 100
    
    # Création du graphique avec plotly.graph_objects pour avoir un vrai stacked bar
    fig = go.Figure()
    
    # Ajouter les barres empilées
    if immo_pct > 0:
        fig.add_trace(go.Bar(
            name='Immobilier',
            y=['Répartition'],
            x=[immo_pct],
            orientation='h',
            marker_color=px.colors.qualitative.Vivid[0],
            text=f'{immo_pct:.1f}%',
            textposition='inside',
            textfont=dict(color='white', size=12)
        ))
    
    if financier_pct > 0:
        fig.add_trace(go.Bar(
            name='Actifs financiers',
            y=['Répartition'],
            x=[financier_pct],
            orientation='h',
            marker_color=px.colors.qualitative.Vivid[2],
            text=f'{financier_pct:.1f}%',
            textposition='inside',
            textfont=dict(color='white', size=12)
        ))
        
    if autres_pct > 0:
        fig.add_trace(go.Bar(
            name='Autres actifs',
            y=['Répartition'],
            x=[autres_pct],
            orientation='h',
            marker_color=px.colors.qualitative.Vivid[4],
            text=f'{autres_pct:.1f}%',
            textposition='inside',
            textfont=dict(color='white', size=12)
        ))
    
    fig.update_layout(
        title="Répartition Immobilier vs Financier (Net)",
        title_font_size=12,
        barmode='stack',
        xaxis_title="Pourcentage",
        yaxis_title="",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=120,
        margin=dict(t=50, l=10, r=10, b=10),
        xaxis=dict(range=[0, 100], showgrid=False),
        yaxis=dict(showticklabels=False)
    )
    
    return fig

def create_gantt_chart_fig(gantt_data, duree_projection, parents, enfants):
    """Crée la figure du graphique Gantt avec annotations d'âges aux étapes clés."""
    if not gantt_data:
        return None

    def calculate_age(born, on_date):
        """Calcule l'âge à une date donnée."""
        if not born:
            return 0
        return on_date.year - born.year - ((on_date.month, on_date.day) < (born.month, born.day))

    colors = {'Actif': 'rgb(0, 128, 0)', 'Retraite': 'rgb(255, 165, 0)', 'Études': 'rgb(0, 0, 255)', 'Scolarisé': 'rgb(173, 216, 230)'}
    fig = ff.create_gantt(gantt_data, colors=colors, index_col='Resource', show_colorbar=False, group_tasks=True, showgrid_x=True, showgrid_y=True)

    # --- Annotations pour le statut (Actif, Retraite...) au centre des barres ---
    bar_annotations = []
    y_labels = list(fig.layout.yaxis.ticktext)
    for d in gantt_data:
        try:
            start_date = pd.to_datetime(d['Start'])
            end_date = pd.to_datetime(d['Finish'])
            if (end_date - start_date).days > 180:
                center_date = start_date + (end_date - start_date) / 2
                y_pos = y_labels.index(d['Task'])
                bar_annotations.append(dict(x=center_date.strftime('%Y-%m-%d'), y=y_pos, text=d['Resource'], showarrow=False, font=dict(color='white', size=12, weight='bold'), align='center', xanchor='center', yanchor='middle', yref='y'))
        except (ValueError, TypeError):
            continue

    # --- Lignes verticales et annotations d'âge pour les événements clés ---
    event_annotations = []
    event_shapes = []
    all_members = parents + enfants
    
    # Trouver toutes les dates de début d'événement uniques
    event_dates = sorted(list(set(pd.to_datetime(d['Start']).date() for d in gantt_data)))

    for event_date in event_dates:
        # Dessiner une ligne verticale pour chaque événement
        event_shapes.append(
            dict(type='line', x0=event_date, x1=event_date, y0=-0.5, y1=len(y_labels)-0.5, 
                 line=dict(color='Grey', width=1, dash='dot'))
        )
        
        # Ajouter une annotation d'âge pour chaque membre à cette date
        for member in all_members:
            prenom = member.get('prenom')
            dob = member.get('date_naissance')
            if not prenom or not dob or prenom not in y_labels:
                continue
            
            age_at_event = calculate_age(dob, on_date=event_date)
            y_pos = y_labels.index(prenom)
            
            event_annotations.append(
                dict(x=event_date, y=y_pos, text=f"<b>{age_at_event} ans</b>", showarrow=False, 
                     font=dict(color='black', size=14), bgcolor='rgba(255,255,255,0.9)',
                     xanchor='center', yanchor='bottom', yshift=5)
            )

    start_date_chart = date.today()
    end_date_chart = date(start_date_chart.year + duree_projection, 12, 31)
    fig.update_layout(
        title_text='Activités par membre du foyer au fil du temps',
        xaxis_title='Année',
        xaxis_range=[start_date_chart.strftime('%Y-%m-%d'), end_date_chart.strftime('%Y-%m-%d')],
        annotations=bar_annotations + event_annotations, 
        shapes=event_shapes,
        showlegend=False,
        yaxis=dict(
            title='Membre du Foyer',
            tickfont=dict(size=14)
        ),
        height=len(parents + enfants) * 80 + 150
    )
    return fig


def create_flux_treemap_mensuel(data_treemap, total_revenus):
    """Crée le treemap mensuel des flux (avec palette Vivid)."""
    if not data_treemap:
        return None
        
    df_treemap = pd.DataFrame(data_treemap)
    fig = px.treemap(
        df_treemap,
        path=['label'],
        values='montant',
        color='label',
        color_discrete_map=FLUX_CATEGORY_COLOR_MAP,
        title="Vue Mensuelle"
    )
    fig.update_traces(
        texttemplate='%{label}<br><b>%{value:,.0f} €</b>',
        hovertemplate='%{label}: %{value:,.0f} €<extra></extra>',
        textfont_size=14
    )
    fig.update_layout(margin=dict(t=50, l=10, r=10, b=10))
    return fig


def create_flux_treemap_annuel(data_treemap, total_revenus):
    """Crée le treemap annuel des flux (avec palette Vivid)."""
    if not data_treemap:
        return None
        
    df_treemap = pd.DataFrame(data_treemap)
    # Conversion en annuel
    df_annuel = df_treemap.copy()
    df_annuel['montant'] *= 12
    total_revenus_annuel = total_revenus * 12
    
    fig = px.treemap(
        df_annuel, 
        path=['label'],
        values='montant',
        color='label',
        color_discrete_map=FLUX_CATEGORY_COLOR_MAP,
        title="Vue Annuelle"
    )
    fig.update_traces(
        texttemplate='%{label}<br><b>%{value:,.0f} €</b>',
        hovertemplate='%{label}: %{value:,.0f} €<extra></extra>',
        textfont_size=14
    )
    fig.update_layout(margin=dict(t=50, l=10, r=10, b=10))
    return fig


def create_flux_treemap_mensuel_old(data_treemap, total_revenus):
    """Crée le treemap mensuel des flux."""
    if not data_treemap:
        return None
        
    df_treemap = pd.DataFrame(data_treemap)
    fig = px.treemap(
        df_treemap,
        #path=[px.Constant(f"Revenus Mensuels ({total_revenus:,.0f} €)"), 'label'],
        values='montant', 
        title="Vue Mensuelle"
    )
    fig.update_traces(
        texttemplate='%{label}<br><b>%{value:,.0f} €</b>',
        hovertemplate='%{label}: %{value:,.0f} €<extra></extra>',
        textfont_size=14
    )
    fig.update_layout(margin=dict(t=50, l=10, r=10, b=10))
    return fig


def create_flux_treemap_annuel_old(data_treemap, total_revenus):
    """Crée le treemap annuel des flux."""
    if not data_treemap:
        return None
        
    df_treemap = pd.DataFrame(data_treemap)
    # Conversion en annuel
    df_annuel = df_treemap.copy()
    df_annuel['montant'] *= 12
    total_revenus_annuel = total_revenus * 12
    
    fig = px.treemap(
        df_annuel, 
        #path=[px.Constant(f"Revenus Annuels ({total_revenus_annuel:,.0f} €)"), 'label'],
        values='montant', 
        title="Vue Annuelle"
    )
    fig.update_traces(
        texttemplate='%{label}<br><b>%{value:,.0f} €</b>',
        hovertemplate='%{label}: %{value:,.0f} €<extra></extra>',
        textfont_size=14
    )
    fig.update_layout(margin=dict(t=50, l=10, r=10, b=10))
    return fig

def create_patrimoine_brut_composite(df_patrimoine):
    """Crée une image composite avec treemap + barres empilées pour le patrimoine brut."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    
    # Créer les sous-graphiques
    fig_treemap = create_patrimoine_brut_treemap(df_patrimoine)
    fig_bar = create_patrimoine_brut_stacked_bar(df_patrimoine)
    
    if not fig_treemap or not fig_bar:
        return None
    
    # Créer une figure avec des sous-graphiques
    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.8, 0.2],  # 80% pour le treemap, 20% pour la barre
        specs=[[{"type": "treemap"}], [{"type": "bar"}]],
        subplot_titles=("Répartition du Patrimoine Brut", ""),
        vertical_spacing=0.05
    )
    
    # Ajouter le treemap
    for trace in fig_treemap.data:
        fig.add_trace(trace, row=1, col=1)
    
    # Ajouter les barres empilées
    for trace in fig_bar.data:
        fig.add_trace(trace, row=2, col=1)
    
    # Mise à jour du layout
    fig.update_layout(
        height=600,
        barmode='stack',  # Forcer le mode empilé
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.1,
            xanchor="center",
            x=0.5
        ),
        margin=dict(t=60, l=10, r=10, b=80)
    )
    
    # Mise à jour des axes de la barre
    fig.update_xaxes(title_text="Pourcentage", range=[0, 100], row=2, col=1)
    fig.update_yaxes(showticklabels=False, row=2, col=1)
    
    return fig

def create_patrimoine_net_composite(df_patrimoine):
    """Crée une image composite avec treemap + barres empilées pour le patrimoine net."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    
    # Créer les sous-graphiques
    fig_treemap = create_patrimoine_net_treemap(df_patrimoine)
    fig_bar = create_patrimoine_net_stacked_bar(df_patrimoine)
    
    if not fig_treemap or not fig_bar:
        return None
    
    # Créer une figure avec des sous-graphiques
    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.8, 0.2],  # 80% pour le treemap, 20% pour la barre
        specs=[[{"type": "treemap"}], [{"type": "bar"}]],
        subplot_titles=("Répartition du Patrimoine Net", ""),
        vertical_spacing=0.05
    )
    
    # Ajouter le treemap
    for trace in fig_treemap.data:
        fig.add_trace(trace, row=1, col=1)
    
    # Ajouter les barres empilées
    for trace in fig_bar.data:
        fig.add_trace(trace, row=2, col=1)
    
    # Mise à jour du layout
    fig.update_layout(
        height=600,
        barmode='stack',  # Forcer le mode empilé
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.1,
            xanchor="center",
            x=0.5
        ),
        margin=dict(t=60, l=10, r=10, b=80)
    )
    
    # Mise à jour des axes de la barre
    fig.update_xaxes(title_text="Pourcentage", range=[0, 100], row=2, col=1)
    fig.update_yaxes(showticklabels=False, row=2, col=1)
    
    return fig