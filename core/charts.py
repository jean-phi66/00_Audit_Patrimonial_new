import pandas as pd
import plotly.express as px
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
        fig.update_traces(textinfo='label+percent root', textfont_size=14)
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
        fig.update_traces(textinfo='label+percent root', textfont_size=14)
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