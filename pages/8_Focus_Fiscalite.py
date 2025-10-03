import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import date

import sys
import os
# Add project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


from core.fiscal_logic import get_revenus_imposables

try:
    from utils.openfisca_utils import analyser_fiscalite_foyer, simuler_evolution_fiscalite, add_bracket_lines_to_fig
    OPENFISCA_UTILITY_AVAILABLE = True
except ImportError as e:
    OPENFISCA_UTILITY_AVAILABLE = False
    st.session_state.openfisca_import_error = str(e)

def display_summary(results):
    """Affiche la synthèse des résultats fiscaux."""
    st.header("📊 Synthèse de votre imposition")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Impôt sur le Revenu Net", f"{results['ir_net']:,.2f} €")
    col2.metric("Prélèvements Sociaux (foncier)", f"{results['ps_foncier']:,.2f} €")
    col3.metric("Taux Marginal d'Imposition (TMI)", f"{results['tmi']:.0f} %")
    col4.metric("Taux d'imposition global", f"{results['taux_imposition_global']:.2f} %", help="Total (IR + PS) / Total des revenus bruts")

def display_quotient_familial_analysis(results):
    """Affiche l'analyse de l'impact du quotient familial."""
    st.header("👨‍👩‍👧‍👦 Analyse du Quotient Familial")

    col1, col2, col3 = st.columns(3)
    col1.metric("Nombre de parts fiscales", f"{results['parts_fiscales']:.2f}")
    col2.metric("Impôt SANS quotient familial", f"{results['ir_sans_quotient']:,.2f} €", help="Impôt qui serait dû sans les parts fiscales des enfants.")
    col3.metric(
        "Gain lié au quotient familial",
        f"{results['gain_quotient']:,.2f} €",
        delta=f"{results['gain_quotient']:,.2f} € d'économie",
        delta_color="inverse"
    )
    st.info("Le gain du quotient familial représente l'économie d'impôt réalisée grâce aux parts fiscales apportées par les personnes à charge (principalement les enfants).")

def display_tax_calculation_waterfall(results):
    """Affiche un graphique en cascade du calcul de l'impôt."""
    st.header("🌊 Décomposition du calcul de l'impôt")

    fig = go.Figure(go.Waterfall(
        name="Calcul IR",
        orientation="v",
        measure=["absolute", "relative", "total", "relative", "total"],
        x=[
            "Revenu Brut Global", "Abattement 10% (ou frais réels)",
            "Revenu Net Imposable", "Application du barème",
            "Impôt sur le Revenu Net"
        ],
        textposition="outside",
        y=[
            results['revenu_brut_global'],
            -(results['revenu_brut_global'] - results['revenu_net_imposable']),
            None, # Total
            -results['ir_net'], # Simplification : on montre directement l'impôt final
            None # Total
        ],
        text=[
            f"{results['revenu_brut_global']:,.0f} €",
            f"-{(results['revenu_brut_global'] - results['revenu_net_imposable']):,.0f} €",
            f"{results['revenu_net_imposable']:,.0f} €",
            f"-{results['ir_net']:,.0f} €",
            f"{results['ir_net']:,.0f} €"
        ],
        connector={"line": {"color": "rgb(63, 63, 63)"}},
    ))

    fig.update_layout(
        title="Du Revenu Brut Global à l'Impôt Net",
        showlegend=False,
        yaxis_title="Montant (€)"
    )
    st.plotly_chart(fig, use_container_width=True)

def debug_fisca(results):
    st.header('input to OpenFisca')
    st.json(results['simulation_data'], expanded=False)

def display_income_evolution_chart(results, revenu_brut_global_actuel, revenu_max_simu):
    """Affiche le graphique de l'évolution de l'impôt en fonction du revenu."""
    st.header("Évolution de l'impôt selon le revenu")

    df_evolution = results.get('df_evolution')
    bareme = results.get('bareme')
    ir_actuel = results.get('ir_net')

    if df_evolution is None or df_evolution.empty:
        st.warning("Les données pour le graphique d'évolution n'ont pas pu être générées.")
        return

    fig = px.line(df_evolution, x='Revenu', y='IR', labels={'Revenu': 'Revenu brut global (€)', 'IR': "Montant de l'IR (€)"})
    
    if bareme:
        fig = add_bracket_lines_to_fig(fig, df_evolution, bareme)

    # Ajouter le point pour la situation actuelle (aligné sur la courbe)
    fig.add_scatter(
        x=[revenu_brut_global_actuel], 
        y=[ir_actuel], 
        mode='markers',
        marker=dict(color='red', size=12, symbol='circle', line=dict(width=2, color='darkred')), 
        name='Votre situation',
        hovertemplate="<b>Votre situation actuelle</b><br>" +
                      "Revenus: %{x:,.0f}€<br>" +
                      "Impôt sur le revenu: %{y:,.0f}€<extra></extra>"
    )
    
    # Ajouter le texte dans une annotation séparée pour un meilleur contrôle
    fig.add_annotation(
        x=revenu_brut_global_actuel,
        y=ir_actuel,
        text=f"<b>Votre situation</b><br>Revenus: {revenu_brut_global_actuel:,.0f}€<br>IR: {ir_actuel:,.0f}€",
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor="red",
        ax=-80,  # Décalage horizontal de la flèche (négatif = vers la gauche)
        ay=-20,  # Décalage vertical de la flèche (négatif = vers le haut)
        bgcolor="rgba(255, 255, 255, 0.9)",
        bordercolor="red",
        borderwidth=1,
        borderpad=4,
        font=dict(size=14, color="black")  # Augmentation de 12 à 14
    )
    
    fig.update_layout(
        xaxis_ticksuffix='€', 
        yaxis_ticksuffix='€', 
        xaxis_range=[0, revenu_max_simu],
        title="Évolution de l'impôt selon le revenu",
        # Augmentation de la taille des polices
        font=dict(size=14),  # Taille de police générale
        title_font=dict(size=18),  # Titre principal
        xaxis=dict(
            tickfont=dict(size=14),  # Étiquettes de l'axe X
            title=dict(font=dict(size=16))  # Titre de l'axe X
        ),
        yaxis=dict(
            tickfont=dict(size=14),  # Étiquettes de l'axe Y
            title=dict(font=dict(size=16))  # Titre de l'axe Y
        ),
        legend=dict(
            font=dict(size=14)  # Police de la légende
        )
    )
    st.plotly_chart(fig, use_container_width=True)

#def main():
st.title("🔎 Focus Fiscalité")
st.markdown("Analysez en détail l'imposition sur le revenu de votre foyer pour l'année en cours.")

# --- Vérifications initiales ---
if not OPENFISCA_UTILITY_AVAILABLE:
    error_msg = st.session_state.get('openfisca_import_error', "Erreur inconnue.")
    st.error(
        "**Le module OpenFisca n'a pas pu être chargé.** L'analyse fiscale ne peut pas être effectuée.\n\n"
        f"**Erreur technique :** `{error_msg}`\n\n"
        "Veuillez vous assurer que le package `openfisca-france` est bien installé dans votre environnement Python."
    )
    st.stop()

if 'parents' not in st.session_state or not st.session_state.parents:
    st.warning("⚠️ Veuillez d'abord renseigner les informations du foyer dans la page **1_Famille**.")
    st.stop()

# --- Préparation des données ---
parents = st.session_state.get('parents', [])
enfants = st.session_state.get('enfants', []) 

total_salary_check = sum(r.get('montant', 0) for r in st.session_state.get('revenus', []) if r.get('type') == 'Salaire')

if total_salary_check == 0:
    st.warning("⚠️ Veuillez renseigner les salaires dans la page **4_Flux** pour lancer l'analyse.")
    st.stop()

# --- Paramètres de simulation ---
st.sidebar.header("Paramètres de l'analyse")
annee_simulation = st.sidebar.number_input("Année d'imposition", min_value=2020, max_value=date.today().year, value=date.today().year)

# Détection automatique du parent isolé, avec possibilité de forcer
is_single_parent_auto = len(parents) == 1 and len(enfants) > 0
if is_single_parent_auto:
    est_parent_isole = st.sidebar.checkbox(
        "Cocher la case T (Parent isolé)", 
        value=is_single_parent_auto,
        help="Cochez cette case si vous êtes célibataire, divorcé(e), séparé(e) ou veuf(ve) et que vous vivez seul(e) avec vos enfants à charge."
    )
else:
    est_parent_isole = False

# Calculer les revenus en amont pour les utiliser dans les valeurs par défaut des widgets.
revenus_salaires, revenu_foncier_net = get_revenus_imposables(annee_simulation)

revenu_max_graphique = st.sidebar.number_input(
    "Revenu maximum pour les graphiques", 
    min_value=50000, max_value=500000, value=max(150000, int(sum(revenus_salaires.values()) * 1.2)), step=10000
)

# --- Lancement de l'analyse ---
with st.spinner("Analyse de la fiscalité en cours avec OpenFisca..."):
    try:
        resultats_fiscaux = analyser_fiscalite_foyer(
            annee=annee_simulation,
            parents=parents,
            enfants=enfants,
            revenus_annuels=revenus_salaires,
            revenu_foncier_net=revenu_foncier_net,
            est_parent_isole=est_parent_isole
        )

        # Lancer la simulation pour le graphique
        df_evolution, bareme = simuler_evolution_fiscalite(
            annee=annee_simulation, parents=parents, enfants=enfants,
            revenu_foncier_net=revenu_foncier_net, est_parent_isole=est_parent_isole,
            revenu_max_simu=revenu_max_graphique
        )
        resultats_fiscaux['df_evolution'] = df_evolution
        resultats_fiscaux['bareme'] = bareme
    except Exception as e:
        st.error(f"Une erreur est survenue lors du calcul avec OpenFisca : {e}")
        st.stop()

# --- Affichage des résultats ---
display_summary(resultats_fiscaux)
st.markdown("---")
display_quotient_familial_analysis(resultats_fiscaux)
#st.markdown("---")
#display_tax_calculation_waterfall(resultats_fiscaux)
st.markdown("---")
display_income_evolution_chart(resultats_fiscaux, sum(revenus_salaires.values()) + revenu_foncier_net, revenu_max_graphique)
st.markdown("---")
debug_fisca(resultats_fiscaux)
