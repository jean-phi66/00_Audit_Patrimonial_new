import pandas as pd
import plotly.express as px

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