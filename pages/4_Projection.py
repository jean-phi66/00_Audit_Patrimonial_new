import streamlit as st
import pandas as pd
import plotly.figure_factory as ff
from datetime import date, timedelta
import plotly.express as px

try:
    from utils.openfisca_utils import calculer_impot_openfisca
    OPENFISCA_UTILITY_AVAILABLE = True
except ImportError:
    OPENFISCA_UTILITY_AVAILABLE = False


# --- Fonctions de logique métier ---

def calculate_age(born, on_date=None):
    """Calcule l'âge à une date donnée."""
    if not born:
        return 0
    if on_date is None:
        on_date = date.today()
    return on_date.year - born.year - ((on_date.month, on_date.day) < (born.month, born.day))

def generate_gantt_data(parents, enfants, settings, projection_duration):
    """Génère les données pour le diagramme de Gantt avec une logique de fin de projection corrigée."""
    gantt_data = []
    today = date.today()
    annee_fin_projection = today.year + projection_duration

    # --- Traitement des parents ---
    for parent in parents:
        prenom = parent.get('prenom')
        dob = parent.get('date_naissance')
        if not prenom or not dob:
            continue

        age_retraite = settings[prenom]['retraite']
        annee_retraite = dob.year + age_retraite
        
        finish_actif = min(annee_retraite, annee_fin_projection)

        if today.year <= finish_actif:
            gantt_data.append(dict(
                Task=prenom,
                Start=f"{today.year}-01-01",
                Finish=f"{finish_actif}-12-31",
                Resource="Actif"
            ))

        start_retraite = annee_retraite + 1
        if start_retraite <= annee_fin_projection:
            gantt_data.append(dict(
                Task=prenom,
                Start=f"{start_retraite}-01-01",
                Finish=f"{annee_fin_projection}-12-31",
                Resource="Retraite"
            ))

    # --- Traitement des enfants ---
    for enfant in enfants:
        prenom = enfant.get('prenom')
        dob = enfant.get('date_naissance')
        if not prenom or not dob:
            continue

        age_debut_etudes = settings[prenom]['debut_etudes']
        duree_etudes = settings[prenom]['duree_etudes']
        
        annee_debut_etudes = dob.year + age_debut_etudes
        annee_fin_etudes = annee_debut_etudes + duree_etudes
        age_retraite_ref = settings[parents[0]['prenom']]['retraite'] if parents and parents[0].get('prenom') in settings else 64
        annee_retraite_enfant = dob.year + age_retraite_ref

        start_scolarise = max(today.year, dob.year)
        finish_scolarise = min(annee_debut_etudes, annee_fin_projection)
        if start_scolarise <= finish_scolarise:
            gantt_data.append(dict(
                Task=prenom,
                Start=f"{start_scolarise}-01-01",
                Finish=f"{finish_scolarise}-12-31",
                Resource="Scolarisé"
            ))

        start_etudes = annee_debut_etudes + 1
        finish_etudes = min(annee_fin_etudes, annee_fin_projection)
        if start_etudes <= finish_etudes:
            gantt_data.append(dict(
                Task=prenom,
                Start=f"{start_etudes}-01-01",
                Finish=f"{finish_etudes}-12-31",
                Resource="Études"
            ))

        start_actif = annee_fin_etudes + 1
        finish_actif = min(annee_retraite_enfant, annee_fin_projection)
        if start_actif <= finish_actif:
            gantt_data.append(dict(
                Task=prenom,
                Start=f"{start_actif}-01-01",
                Finish=f"{finish_actif}-12-31",
                Resource="Actif"
            ))
            
        start_retraite_enfant = annee_retraite_enfant + 1
        if start_retraite_enfant <= annee_fin_projection:
            gantt_data.append(dict(
                Task=prenom,
                Start=f"{start_retraite_enfant}-01-01",
                Finish=f"{annee_fin_projection}-12-31",
                Resource="Retraite"
            ))

    return gantt_data

def generate_financial_projection(parents, enfants, settings, projection_duration):
    """Génère les données de projection financière année par année."""
    projection_data = []
    today = date.today()

    # Récupérer les paramètres de revenus pour chaque parent
    income_settings = {}
    for p in parents:
        prenom = p['prenom']
        income_settings[prenom] = {
            'revenu_actuel': settings[prenom].get('revenu_actuel', 0),
            'taux_remplacement_retraite': settings[prenom].get('taux_remplacement_retraite', 0.7)
        }

    for i in range(projection_duration + 1):
        annee = today.year + i
        current_date_in_year = date(annee, 1, 1)
        year_data = {'Année': annee}
        
        revenus_annuels_parents = {}
        
        # --- Traitement des parents ---
        for parent in parents:
            prenom = parent['prenom']
            dob = parent['date_naissance']
            age = calculate_age(dob, current_date_in_year)
            year_data[f'Âge {prenom}'] = age
            
            age_retraite = settings[prenom]['retraite']
            
            if age < age_retraite:
                revenu = income_settings[prenom]['revenu_actuel']
            else:
                revenu = income_settings[prenom]['revenu_actuel'] * income_settings[prenom]['taux_remplacement_retraite']
            
            revenus_annuels_parents[prenom] = revenu
            year_data[f'Revenu {prenom}'] = revenu

        # --- Calculs pour le foyer ---
        total_revenus_foyer = sum(revenus_annuels_parents.values())
        year_data['Revenus bruts du foyer'] = total_revenus_foyer
        
        # --- Déterminer les enfants à charge pour l'année en cours ---
        enfants_a_charge_annee = []
        for enfant in enfants:
            prenom_enfant = enfant.get('prenom')
            dob_enfant = enfant.get('date_naissance')
            if not prenom_enfant or not dob_enfant:
                continue

            # Récupérer les paramètres d'études pour l'enfant
            settings_enfant = settings.get(prenom_enfant, {})
            age_debut_etudes = settings_enfant.get('debut_etudes', 18)
            duree_etudes = settings_enfant.get('duree_etudes', 5)

            annee_fin_etudes = dob_enfant.year + age_debut_etudes + duree_etudes

            # L'enfant est considéré à charge si l'année de projection est <= à l'année de fin d'études.
            # OpenFisca gère ensuite les limites d'âge (ex: < 25 ans) sur cette liste pré-filtrée.
            if annee <= annee_fin_etudes:
                enfants_a_charge_annee.append(enfant)

        # --- Calcul de l'impôt ---
        if OPENFISCA_UTILITY_AVAILABLE:
            est_parent_isole = len(parents) == 1
            impot = calculer_impot_openfisca(
                annee=annee,
                parents=parents,
                enfants=enfants_a_charge_annee,
                revenus_annuels=revenus_annuels_parents,
                est_parent_isole=est_parent_isole
            )
        else:
            # Fallback si OpenFisca n'est pas disponible
            impot = total_revenus_foyer * 0.15

        year_data['Impôt sur le revenu'] = impot
        year_data['Revenus nets du foyer'] = total_revenus_foyer - impot
        
        projection_data.append(year_data)
        
    df = pd.DataFrame(projection_data)
    # S'assurer que les colonnes clés existent même si vides
    for col in ['Année', 'Revenus bruts du foyer', 'Impôt sur le revenu', 'Revenus nets du foyer']:
        if col not in df.columns:
            df[col] = 0
            
    return df

# --- Fonctions d'interface utilisateur (UI) ---

def display_settings_ui(parents, enfants):
    """Affiche les widgets pour configurer les paramètres de la projection."""
    with st.expander("⚙️ Paramètres de la projection", expanded=True):
        duree_projection = st.number_input(
            "Durée de la projection (années)",
            min_value=1, max_value=50, value=20, step=1,
            help="Nombre d'années à projeter après le départ à la retraite des parents."
        )
        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("👨‍👩‍👧 Parents")
            for parent in parents:
                prenom = parent.get('prenom')
                if prenom:
                    if prenom not in st.session_state.projection_settings:
                        st.session_state.projection_settings[prenom] = {'retraite': 64, 'revenu_actuel': 50000, 'taux_remplacement_retraite': 0.7}
                    age_actuel = calculate_age(parent.get('date_naissance'))
                    st.session_state.projection_settings[prenom]['retraite'] = st.number_input(f"Âge de départ à la retraite de {prenom}", min_value=age_actuel, max_value=75, value=st.session_state.projection_settings[prenom]['retraite'], key=f"retraite_{prenom}")
                    st.session_state.projection_settings[prenom]['revenu_actuel'] = st.number_input(f"Revenu annuel brut de {prenom}", 0, 500000, st.session_state.projection_settings[prenom].get('revenu_actuel', 50000), step=1000, key=f"revenu_{prenom}")
                    st.session_state.projection_settings[prenom]['taux_remplacement_retraite'] = st.slider(f"Taux de remplacement retraite de {prenom}", 0.0, 1.0, st.session_state.projection_settings[prenom].get('taux_remplacement_retraite', 0.7), 0.05, key=f"tx_rempl_{prenom}")

        with col2:
            st.subheader("👶 Enfants")
            if not enfants:
                st.info("Aucun enfant renseigné.")
            for enfant in enfants:
                prenom = enfant.get('prenom')
                if prenom:
                    if prenom not in st.session_state.projection_settings:
                        st.session_state.projection_settings[prenom] = {'debut_etudes': 18, 'duree_etudes': 5}
                    st.session_state.projection_settings[prenom]['debut_etudes'] = st.number_input(f"Âge de début des études de {prenom}", 15, 25, st.session_state.projection_settings[prenom]['debut_etudes'], key=f"debut_{prenom}")
                    st.session_state.projection_settings[prenom]['duree_etudes'] = st.number_input(f"Durée des études de {prenom} (ans)", 1, 8, st.session_state.projection_settings[prenom]['duree_etudes'], key=f"duree_{prenom}")
                    st.markdown("---")
    return duree_projection, st.session_state.projection_settings

def display_gantt_chart(gantt_data, duree_projection, parents, enfants):
    """Affiche la frise chronologique (diagramme de Gantt)."""
    st.header("📊 Frise Chronologique du Foyer")
    if not gantt_data:
        st.info("Les données sont insuffisantes ou la période de projection est trop courte pour générer la frise chronologique.")
        return

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
    
    # 1. Trouver toutes les dates de début d'événement uniques
    event_dates = sorted(list(set(pd.to_datetime(d['Start']).date() for d in gantt_data)))

    for event_date in event_dates:
        # 2. Dessiner une ligne verticale pour chaque événement
        event_shapes.append(
            dict(type='line', x0=event_date, x1=event_date, y0=-0.5, y1=len(y_labels)-0.5, 
                 line=dict(color='Grey', width=1, dash='dot'))
        )
        
        # 3. Ajouter une annotation d'âge pour chaque membre à cette date
        for member in all_members:
            prenom = member.get('prenom')
            dob = member.get('date_naissance')
            if not prenom or not dob or prenom not in y_labels:
                continue
            
            age_at_event = calculate_age(dob, on_date=event_date)
            y_pos = y_labels.index(prenom)
            
            event_annotations.append(
                dict(x=event_date, y=y_pos, text=f"<b>{age_at_event} ans</b>", showarrow=False, 
                     font=dict(color='black', size=10), bgcolor='rgba(255,255,255,0.6)',
                     xanchor='center', yanchor='bottom', yshift=5)
            )

    start_date_chart = date.today()
    end_date_chart = date(start_date_chart.year + duree_projection, 12, 31)
    fig.update_layout(
        title_text='Activités par membre du foyer au fil du temps',
        xaxis_title='Année', yaxis_title='Membre du Foyer',
        xaxis_range=[start_date_chart.strftime('%Y-%m-%d'), end_date_chart.strftime('%Y-%m-%d')],
        annotations=bar_annotations + event_annotations, 
        shapes=event_shapes,
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

def display_financial_projection(df_projection):
    """Affiche le tableau et le graphique de la projection financière."""
    st.header("📈 Projection Financière Annuelle")
    if not OPENFISCA_UTILITY_AVAILABLE:
        st.warning("Le module OpenFisca n'est pas installé. Les calculs d'impôts seront des estimations simplifiées (taux forfaitaire de 15%).\n\nPour un calcul précis, veuillez installer le package `openfisca-france`.")

    if df_projection.empty:
        st.info("Aucune donnée de projection financière à afficher.")
        return

    st.subheader("Tableau de projection")
    df_display = df_projection.copy()
    income_cols = [col for col in df_display.columns if 'Revenu' in col or 'Impôt' in col]
    format_dict = {col: '{:,.0f} €' for col in income_cols}
    st.dataframe(df_display.style.format(format_dict))

    st.subheader("Graphique d'évolution des revenus et de l'impôt")
    fig_proj = px.line(
        df_projection, x='Année', y=['Revenus bruts du foyer', 'Impôt sur le revenu', 'Revenus nets du foyer'],
        title="Évolution des finances du foyer",
        labels={'value': 'Montant (€)', 'variable': 'Indicateur'}
    )
    st.plotly_chart(fig_proj, use_container_width=True)

# --- Exécution Principale ---

def main():
    """Fonction principale pour exécuter la page de projection."""
    st.title("🗓️ Projection des grandes étapes de vie")
    st.markdown("Définissez les âges clés pour chaque membre du foyer afin de visualiser une frise chronologique de leurs activités.")

    if 'parents' not in st.session_state or not st.session_state.parents or not st.session_state.parents[0].get('prenom'):
        st.warning("⚠️ Veuillez d'abord renseigner les informations du foyer dans la page **1_Famille**.")
        st.stop()

    if 'projection_settings' not in st.session_state:
        st.session_state.projection_settings = {}

    parents = st.session_state.parents
    enfants = st.session_state.enfants

    duree_projection, settings = display_settings_ui(parents, enfants)

    gantt_data = generate_gantt_data(parents, enfants, settings, duree_projection)
    display_gantt_chart(gantt_data, duree_projection, parents, enfants)

    df_projection = generate_financial_projection(parents, enfants, settings, duree_projection)
    display_financial_projection(df_projection)

if __name__ == "__main__":
    main()
