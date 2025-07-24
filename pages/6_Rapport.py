import streamlit as st
from datetime import date
import os
import io
import pandas as pd
import numpy as np
import plotly.io as pio
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
import importlib

from core.patrimoine_logic import get_patrimoine_df, find_associated_loans
from core.charts import (
    create_patrimoine_brut_treemap,
    create_patrimoine_net_treemap,
    create_patrimoine_net_donut
)

# --- Vérification de la disponibilité des modules et fonctions ---

def import_from(module_name, func_name):
    """Tente d'importer une fonction depuis un module de page."""
    try:
        module = importlib.import_module(f"pages.{module_name}")
        return getattr(module, func_name), True
    except (ImportError, AttributeError):
        return None, False

# --- Fonctions importées des autres pages ---
generate_immo_projection_data, FOCUS_IMMO_AVAILABLE = import_from("3_Focus_Immobilier", "generate_projection_data")
create_cash_flow_projection_fig, _ = import_from("3_Focus_Immobilier", "create_cash_flow_projection_fig")

calculate_weighted_income, CAP_ENDETTEMENT_AVAILABLE = import_from("7_Capacite_Endettement", "calculate_weighted_income")
calculate_current_debt_service, _ = import_from("7_Capacite_Endettement", "calculate_current_debt_service")

generate_gantt_data, PROJECTION_AVAILABLE = import_from("4_Projection", "generate_gantt_data")
generate_financial_projection, _ = import_from("4_Projection", "generate_financial_projection")

get_revenus_imposables_fiscalite, FOCUS_FISCALITE_AVAILABLE = import_from("8_Focus_Fiscalite", "get_revenus_imposables")
analyser_fiscalite_foyer_fiscalite, _ = import_from("8_Focus_Fiscalite", "analyser_fiscalite_foyer")
simuler_evolution_fiscalite, _ = import_from("8_Focus_Fiscalite", "simuler_evolution_fiscalite")
display_income_evolution_chart, _ = import_from("8_Focus_Fiscalite", "display_income_evolution_chart")

analyser_optimisation_per, OPTIMISATION_PER_AVAILABLE = import_from("9_Optimisation_PER", "analyser_optimisation_per")

# --- Vérification des dépendances critiques ---
try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False

try:
    from utils.openfisca_utils import analyser_fiscalite_foyer
    OPENFISCA_AVAILABLE = True
except ImportError:
    OPENFISCA_AVAILABLE = False

# --- Classe PDF personnalisée pour le rapport ---

class PDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.font_family_name = "Arial"
        self.currency_symbol = " EUR"

        font_dir = "assets/fonts"
        dejavu_sans_path = os.path.join(font_dir, 'DejaVuSans.ttf')
        dejavu_bold_path = os.path.join(font_dir, 'DejaVuSans-Bold.ttf')
        dejavu_italic_path = os.path.join(font_dir, 'DejaVuSans-Oblique.ttf')

        try:
            self.add_font('DejaVu', '', dejavu_sans_path, uni=True)
            self.add_font('DejaVu', 'B', dejavu_bold_path, uni=True)
            self.add_font('DejaVu', 'I', dejavu_italic_path, uni=True)
            self.font_family_name = "DejaVu"
            self.currency_symbol = " €"
        except (RuntimeError, FileNotFoundError):
            st.error(
                "**Police DejaVu non trouvée.** Le rapport PDF ne peut pas être généré.\n\n"
                "Veuillez créer un dossier `assets/fonts` et y placer les fichiers `DejaVuSans.ttf`, `DejaVuSans-Bold.ttf`, et `DejaVuSans-Oblique.ttf`."
            )
            st.stop()

    def header(self):
        self.set_font(self.font_family_name, 'B', 15)
        self.cell(80)
        self.cell(30, 10, "Rapport d'Audit Patrimonial", 0, 0, 'C')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font(self.font_family_name, 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font(self.font_family_name, 'B', 14)
        self.set_fill_color(230, 230, 230)
        self.cell(0, 10, title, 0, 1, 'L', 1)
        self.ln(5)

    def chapter_body(self, body):
        self.set_font(self.font_family_name, '', 11)
        self.multi_cell(0, 6, body)
        self.ln()

    def add_table(self, df, col_widths, title=""):
        if title:
            self.set_font(self.font_family_name, 'B', 12)
            self.cell(0, 10, title, 0, 1, 'L')
        self.set_font(self.font_family_name, 'B', 10)
        self.set_fill_color(240, 240, 240)
        for i, col_name in enumerate(df.columns):
            self.cell(col_widths[i], 7, str(col_name), 1, 0, 'C', 1)
        self.ln()
        self.set_font(self.font_family_name, '', 9)
        for _, row in df.iterrows():
            for i, item in enumerate(row):
                text = str(item)
                align = 'L'
                if isinstance(item, (int, float)):
                    text = f"{item:,.2f}{self.currency_symbol}"
                    align = 'R'
                self.cell(col_widths[i], 6, text, 1, 0, align)
            self.ln()
        self.ln(10)

    def add_figure_to_pdf(self, fig, width_percent=100, title=""):
        if title:
            self.set_font(self.font_family_name, 'B', 12)
            self.cell(0, 10, title, 0, 1, 'L')
        try:
            page_width = self.w - 2 * self.l_margin
            img_width = page_width * (width_percent / 100)
            img_height = img_width * 0.6
            img_bytes = pio.to_image(fig, format="png", width=int(img_width*5), height=int(img_height*5), scale=2)
            
            x_pos = (self.w - img_width) / 2
            self.image(io.BytesIO(img_bytes), x=x_pos, w=img_width)
            self.ln(img_height + 5)
        except Exception as e:
            self.set_text_color(255, 0, 0)
            self.multi_cell(0, 5, f"Erreur lors de la génération du graphique : {e}")
            self.set_text_color(0, 0, 0)
            self.ln()

# --- Fonctions pour générer les sections du rapport ---

def add_title_page(pdf, parents):
    pdf.add_page()
    pdf.set_font(pdf.font_family_name, 'B', 24)
    pdf.cell(0, 80, "Audit Patrimonial", 0, 1, 'C')
    pdf.set_font(pdf.font_family_name, 'I', 16)
    if parents:
        parent_names = " & ".join([p['prenom'] for p in parents if p.get('prenom')])
        pdf.cell(0, 20, f"Préparé pour {parent_names}", 0, 1, 'C')
    pdf.set_font(pdf.font_family_name, '', 12)
    pdf.cell(0, 10, f"Date du rapport : {date.today().strftime('%d/%m/%Y')}", 0, 1, 'C')

def add_family_section(pdf, parents, enfants):
    pdf.add_page()
    pdf.chapter_title("1. Composition du Foyer")
    pdf.set_font(pdf.font_family_name, 'B', 12)
    pdf.cell(0, 10, "Parents", 0, 1, 'L')
    pdf.set_font(pdf.font_family_name, '', 11)
    for p in parents:
        dob_str = p.get('date_naissance', date.today()).strftime('%d/%m/%Y')
        pdf.cell(0, 6, f"- {p.get('prenom', 'N/A')}, né(e) le {dob_str}", 0, 1, 'L')
    pdf.ln(5)
    if enfants:
        pdf.set_font(pdf.font_family_name, 'B', 12)
        pdf.cell(0, 10, "Enfants", 0, 1, 'L')
        pdf.set_font(pdf.font_family_name, '', 11)
        for e in enfants:
            dob_str = e.get('date_naissance', date.today()).strftime('%d/%m/%Y')
            pdf.cell(0, 6, f"- {e.get('prenom', 'N/A')}, né(e) le {dob_str}", 0, 1, 'L')

def add_patrimoine_section(pdf, actifs, passifs):
    pdf.add_page()
    pdf.chapter_title("2. Bilan et Visualisation du Patrimoine")
    df_patrimoine = get_patrimoine_df(actifs, passifs)
    if df_patrimoine.empty:
        pdf.chapter_body("Aucune donnée patrimoniale n'a été renseignée.")
        return
    total_actifs = df_patrimoine['Valeur Brute'].sum()
    total_passifs = df_patrimoine['Passif'].sum()
    patrimoine_net = df_patrimoine['Valeur Nette'].sum()
    pdf.chapter_body(
        f"Le total de vos actifs s'élève à {total_actifs:,.2f}{pdf.currency_symbol}, pour un passif de {total_passifs:,.2f}{pdf.currency_symbol}.\n"
        f"Votre patrimoine net est donc de {patrimoine_net:,.2f}{pdf.currency_symbol}."
    )
    df_display = df_patrimoine[['Libellé', 'Type', 'Valeur Brute', 'Passif', 'Valeur Nette']]
    pdf.add_table(df_display, [60, 40, 30, 30, 30], "Détail du patrimoine")
    
    fig_brut = create_patrimoine_brut_treemap(df_patrimoine)
    pdf.add_figure_to_pdf(fig_brut, width_percent=80, title="Répartition du Patrimoine Brut")
    
    fig_net_donut = create_patrimoine_net_donut(df_patrimoine)
    pdf.add_figure_to_pdf(fig_net_donut, width_percent=80, title="Répartition du Patrimoine Net")

def add_flux_section(pdf, revenus, depenses):
    pdf.add_page()
    pdf.chapter_title("3. Flux Financiers Mensuels")
    total_revenus = sum(r.get('montant', 0.0) for r in revenus)
    total_depenses = sum(d.get('montant', 0.0) for d in depenses)
    capacite_epargne = total_revenus - total_depenses
    pdf.chapter_body(
        f"Le total de vos revenus mensuels est de {total_revenus:,.2f}{pdf.currency_symbol} pour des dépenses de {total_depenses:,.2f}{pdf.currency_symbol}.\n"
        f"Votre capacité d'épargne mensuelle est de {capacite_epargne:,.2f}{pdf.currency_symbol}."
    )
    if revenus:
        df_revenus = pd.DataFrame(revenus)[['libelle', 'montant', 'type']]
        df_revenus.columns = ['Libellé', 'Montant', 'Type']
        pdf.add_table(df_revenus, [90, 50, 50], "Détail des revenus")
    if depenses:
        df_depenses = pd.DataFrame(depenses)[['libelle', 'montant', 'categorie']]
        df_depenses.columns = ['Libellé', 'Montant', 'Catégorie']
        pdf.add_table(df_depenses, [90, 50, 50], "Détail des dépenses")

def add_capacite_endettement_section(pdf, revenus, passifs, max_debt_ratio):
    pdf.add_page()
    pdf.chapter_title("4. Capacité d'Endettement")
    if not CAP_ENDETTEMENT_AVAILABLE:
        pdf.chapter_body("Le module de calcul de la capacité d'endettement n'est pas disponible.")
        return
        
    weighted_income_data = calculate_weighted_income(revenus)
    debt_data = calculate_current_debt_service(passifs)
    total_weighted_income = weighted_income_data["total"]
    total_current_debt = debt_data["total"]
    
    if total_weighted_income == 0:
        pdf.chapter_body("Les revenus pondérés sont nuls. Impossible de calculer la capacité d'endettement.")
        return

    current_debt_ratio_pct = (total_current_debt / total_weighted_income) * 100 if total_weighted_income > 0 else 0
    max_debt_service = total_weighted_income * (max_debt_ratio / 100)
    remaining_capacity = max(0, max_debt_service - total_current_debt)

    pdf.chapter_body(
        f"Vos revenus mensuels pondérés sont de {total_weighted_income:,.2f}{pdf.currency_symbol}.\n"
        f"Vos charges de prêts actuelles sont de {total_current_debt:,.2f}{pdf.currency_symbol}.\n"
        f"Votre taux d'endettement actuel est de {current_debt_ratio_pct:.2f} % (pour une cible de {max_debt_ratio} %).\n"
        f"Votre capacité de remboursement mensuelle restante est de {remaining_capacity:,.2f}{pdf.currency_symbol}."
    )
    
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number", value=current_debt_ratio_pct, number={'suffix': ' %'},
        title={'text': f"Taux d'endettement (Cible: {max_debt_ratio}%)"},
        gauge={'axis': {'range': [None, 50]}, 'bar': {'color': "darkblue"},
               'steps': [{'range': [0, max_debt_ratio], 'color': 'lightgreen'}, {'range': [max_debt_ratio, 50], 'color': 'lightcoral'}],
               'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': max_debt_ratio}}))
    pdf.add_figure_to_pdf(fig_gauge, width_percent=70)

def add_projection_section(pdf, parents, enfants, passifs, settings, duree_projection):
    pdf.add_page()
    pdf.chapter_title("5. Projection des Étapes de Vie")
    if not PROJECTION_AVAILABLE:
        pdf.chapter_body("Le module de projection n'est pas disponible.")
        return

    gantt_data = generate_gantt_data(parents, enfants, settings, duree_projection)
    df_projection = generate_financial_projection(parents, enfants, passifs, settings, duree_projection)

    if not gantt_data or df_projection.empty:
        pdf.chapter_body("Données insuffisantes pour générer les projections.")
        return

    fig_gantt = ff.create_gantt(gantt_data, colors={'Actif': 'rgb(0, 128, 0)', 'Retraite': 'rgb(255, 165, 0)', 'Études': 'rgb(0, 0, 255)', 'Scolarisé': 'rgb(173, 216, 230)'},
                                index_col='Resource', show_colorbar=True, group_tasks=True)
    fig_gantt.update_layout(title_text='Frise Chronologique du Foyer', height=len(parents + enfants) * 60 + 100)
    pdf.add_figure_to_pdf(fig_gantt, width_percent=100)

    cols_to_stack = [col for col in ['Reste à vivre', 'Impôt sur le revenu', 'Prélèvements Sociaux', 'Mensualités Prêts', 'Autres Dépenses', 'Coût des études'] if col in df_projection.columns]
    fig_proj_fin = px.bar(df_projection, x='Année', y=cols_to_stack, title="Répartition des revenus du foyer", barmode='stack')
    if 'Revenus du foyer' in df_projection.columns:
        fig_proj_fin.add_scatter(x=df_projection['Année'], y=df_projection['Revenus du foyer'], mode='lines', name='Total Revenus', line=dict(color='black', dash='dot'))
    pdf.add_figure_to_pdf(fig_proj_fin, width_percent=100)

def add_immo_focus_section(pdf, actifs, passifs, tmi, projection_duration):
    productive_assets = [a for a in actifs if a.get('type') == "Immobilier productif"]
    if not productive_assets: return

    pdf.add_page()
    pdf.chapter_title("6. Focus Immobilier Locatif")
    if not FOCUS_IMMO_AVAILABLE:
        pdf.chapter_body("Le module d'analyse immobilière n'est pas disponible.")
        return

    for asset in productive_assets:
        if asset.get('loyers_mensuels') is None: continue
        pdf.set_font(pdf.font_family_name, 'B', 12)
        pdf.cell(0, 10, f"Analyse de : {asset.get('libelle', 'Sans nom')}", 0, 1, 'L')
        pdf.ln(2)
        loans = find_associated_loans(asset.get('id'), passifs)
        df_projection = generate_immo_projection_data(asset, loans, tmi, 17.2, projection_duration)
        if df_projection.empty: continue
        
        fig_cf = create_cash_flow_projection_fig(df_projection)
        pdf.add_figure_to_pdf(fig_cf, width_percent=80)

def add_fiscalite_section(pdf, parents, enfants, revenus_salaires, revenu_foncier_net, annee, revenu_max_graphique, est_parent_isole):
    pdf.add_page()
    pdf.chapter_title("7. Focus Fiscalité")
    if not OPENFISCA_AVAILABLE or not FOCUS_FISCALITE_AVAILABLE:
        pdf.chapter_body("Le module d'analyse fiscale (OpenFisca) n'est pas disponible.")
        return

    results = analyser_fiscalite_foyer_fiscalite(annee, parents, enfants, revenus_salaires, revenu_foncier_net, est_parent_isole)
    
    pdf.chapter_body(
        f"Pour l'année {annee}, votre impôt sur le revenu net est estimé à {results['ir_net']:,.2f}{pdf.currency_symbol}.\n"
        f"Votre Taux Marginal d'Imposition (TMI) est de {results['tmi']:.0f} %.\n"
        f"L'économie d'impôt liée au quotient familial est de {results['gain_quotient']:,.2f}{pdf.currency_symbol}."
    )
    
    df_evol, bareme = simuler_evolution_fiscalite(annee, parents, enfants, revenu_foncier_net, est_parent_isole, revenu_max_graphique)
    results['df_evolution'] = df_evol
    results['bareme'] = bareme
    
    fig = display_income_evolution_chart(results, sum(revenus_salaires.values()), revenu_max_graphique)
    if fig:
        pdf.add_figure_to_pdf(fig, width_percent=100)

def add_per_section(pdf, per_results):
    pdf.add_page()
    pdf.chapter_title("8. Optimisation PER")
    if not OPENFISCA_AVAILABLE or not OPTIMISATION_PER_AVAILABLE:
        pdf.chapter_body("Le module d'optimisation PER (OpenFisca) n'est pas disponible.")
        return
    if not per_results or "error" in per_results:
        pdf.chapter_body("Aucune simulation PER n'a été effectuée ou la simulation a échoué.")
        return

    ir_initial = per_results['df_one_shot']['IR'].values[0]
    versement_optimal = per_results['versement_optimal_PER']
    impot_final = per_results['impot_avec_versement']
    economie = ir_initial - impot_final
    
    pdf.chapter_body(
        f"Votre impôt initial est de {ir_initial:,.2f}{pdf.currency_symbol}.\n"
        f"Un versement PER optimal de {versement_optimal:,.2f}{pdf.currency_symbol} permettrait de réduire votre impôt à {impot_final:,.2f}{pdf.currency_symbol}.\n"
        f"L'économie d'impôt réalisée serait de {economie:,.2f}{pdf.currency_symbol}."
    )

def generate_report(selections, parents, enfants, actifs, passifs, revenus, depenses, per_results, settings):
    pdf = PDF()
    pdf.alias_nb_pages()
    
    add_title_page(pdf, parents)
    if selections['famille']: add_family_section(pdf, parents, enfants)
    if selections['patrimoine']: add_patrimoine_section(pdf, actifs, passifs)
    if selections['flux']: add_flux_section(pdf, revenus, depenses)
    if selections['endettement']: add_capacite_endettement_section(pdf, revenus, passifs, settings['max_debt_ratio'])
    if selections['projection']: add_projection_section(pdf, parents, enfants, passifs, settings['projection_settings'], settings['duree_projection'])
    if selections['immo']: add_immo_focus_section(pdf, actifs, passifs, settings['immo_tmi'], settings['immo_projection_duration'])
    
    if selections['fiscalite'] or selections['per']:
        revenus_salaires, revenu_foncier_net = get_revenus_imposables_fiscalite()
        if selections['fiscalite']: add_fiscalite_section(pdf, parents, enfants, revenus_salaires, revenu_foncier_net, settings['annee_fiscalite'], settings['revenu_max_fiscalite'], settings['est_parent_isole_fiscalite'])
        if selections['per']: add_per_section(pdf, per_results)

    return bytes(pdf.output(dest='S'))

# --- Interface Streamlit ---

st.title("📄 Génération de Rapport")
st.markdown("Cochez les sections que vous souhaitez inclure dans votre rapport PDF personnalisé.")

if not FPDF_AVAILABLE:
    st.error("La bibliothèque `fpdf2` est nécessaire. Installez-la avec `pip install fpdf2`.")
    st.stop()
if 'parents' not in st.session_state or not st.session_state.parents:
    st.warning("⚠️ Veuillez d'abord renseigner les informations du foyer (page **1_Famille**).")
    st.stop()

# --- Sélection des sections ---
st.markdown("---")
st.subheader("Choix des sections du rapport")

cols = st.columns(2)
with cols[0]:
    st.markdown("##### 📋 Blocs principaux")
    selections = {
        'famille': st.checkbox("1. Composition du Foyer", value=True),
        'patrimoine': st.checkbox("2. Bilan Patrimonial", value=True),
        'flux': st.checkbox("3. Flux Financiers", value=True),
        'endettement': st.checkbox("4. Capacité d'Endettement", value=True, disabled=not CAP_ENDETTEMENT_AVAILABLE),
    }
with cols[1]:
    st.markdown("##### 🔎 Analyses & Projections")
    selections['projection'] = st.checkbox("5. Projection des Étapes de Vie", value=True, disabled=not PROJECTION_AVAILABLE)
    selections['immo'] = st.checkbox("6. Focus Immobilier Locatif", value=True, disabled=not FOCUS_IMMO_AVAILABLE)
    selections['fiscalite'] = st.checkbox("7. Focus Fiscalité", value=True, disabled=not OPENFISCA_AVAILABLE)
    
    per_sim_done = 'per_simulation_results' in st.session_state and "error" not in st.session_state.per_simulation_results
    selections['per'] = st.checkbox("8. Optimisation PER", value=True, disabled=not OPENFISCA_AVAILABLE or not per_sim_done, help="Nécessite d'avoir lancé une simulation sur la page Optimisation PER.")

st.markdown("---")

if st.button("🚀 Générer mon rapport PDF", use_container_width=True, type="primary"):
    with st.spinner("Création du rapport en cours..."):
        # --- Récupération de toutes les données et paramètres nécessaires ---
        parents = st.session_state.get('parents', [])
        enfants = st.session_state.get('enfants', [])
        actifs = st.session_state.get('actifs', [])
        passifs = st.session_state.get('passifs', [])
        revenus = st.session_state.get('revenus', [])
        depenses = st.session_state.get('depenses', [])
        per_results = st.session_state.get('per_simulation_results', {})

        # Récupération des paramètres des autres pages
        settings = {
            'max_debt_ratio': st.session_state.get('endettement_max_debt_ratio', 35),
            'projection_settings': st.session_state.get('projection_settings', {}),
            'duree_projection': st.session_state.get('projection_duree', 25),
            'immo_tmi': st.session_state.get('immo_tmi', 30),
            'immo_projection_duration': st.session_state.get('immo_projection_duration', 10),
            'annee_fiscalite': st.session_state.get('fiscalite_annee', date.today().year),
            'revenu_max_fiscalite': st.session_state.get('fiscalite_revenu_max', 150000),
            'est_parent_isole_fiscalite': st.session_state.get('fiscalite_parent_isole', False)
        }

        # Génération du rapport
        pdf_data = generate_report(selections, parents, enfants, actifs, passifs, revenus, depenses, per_results, settings)

        # Création du nom de fichier dynamique
        client_name = parents[0].get('prenom', 'client') if parents else 'client'
        file_name = f"Rapport_Patrimonial_{client_name}_{date.today().strftime('%Y-%m-%d')}.pdf"

        st.success("✅ Rapport généré avec succès !")
        st.download_button(
            label="📥 Télécharger le rapport PDF",
            data=pdf_data,
            file_name=file_name,
            mime="application/pdf",
            use_container_width=True
        )
