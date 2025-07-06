import streamlit as st
from datetime import date
import os
import io
import pandas as pd
import plotly.io as pio
import importlib
from core.patrimoine_logic import get_patrimoine_df, find_associated_loan

# Importation dynamique du module car son nom commence par un chiffre, ce qui est un identifiant invalide.
focus_immo_module = importlib.import_module("pages.3_Focus_Immobilier")
generate_projection_data = focus_immo_module.generate_projection_data
create_cash_flow_projection_fig = focus_immo_module.create_cash_flow_projection_fig
create_leverage_projection_fig = focus_immo_module.create_leverage_projection_fig

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False

# --- Classe PDF personnalisée pour le rapport ---

class PDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.font_family_name = "Arial"  # Police de secours
        self.currency_symbol = " EUR"    # Symbole monétaire de secours

        # Définir les chemins vers les polices locales
        font_dir = "assets/fonts"
        dejavu_sans_path = os.path.join(font_dir, 'DejaVuSans.ttf')
        dejavu_bold_path = os.path.join(font_dir, 'DejaVuSans-Bold.ttf')
        dejavu_italic_path = os.path.join(font_dir, 'DejaVuSans-Oblique.ttf')

        try:
            # Ajouter les polices Unicode depuis les fichiers locaux
            self.add_font('DejaVu', '', dejavu_sans_path, uni=True)
            self.add_font('DejaVu', 'B', dejavu_bold_path, uni=True)
            self.add_font('DejaVu', 'I', dejavu_italic_path, uni=True)
            self.font_family_name = "DejaVu"
            self.currency_symbol = " €"
        except (RuntimeError, FileNotFoundError):
            st.error(
                "**Police DejaVu non trouvée.** Le rapport PDF ne peut pas être généré.\n\n"
                "Pour résoudre ce problème, veuillez inclure les polices avec l'application :\n"
                "1. Créez un dossier `assets` à la racine de votre projet, puis un sous-dossier `fonts` (`assets/fonts`).\n"
                "2. Téléchargez les polices DejaVu (fichier `dejavu-fonts-ttf-2.37.zip`) depuis le site officiel.\n"
                "3. Décompressez l'archive et copiez `DejaVuSans.ttf`, `DejaVuSans-Bold.ttf`, et `DejaVuSans-Oblique.ttf` dans le dossier `assets/fonts`."
            )
            st.stop()

    def header(self):
        # Logo (optionnel, à décommenter si vous avez un fichier logo.png)
        # self.image('assets/logo.png', 10, 8, 33)
        self.set_font(self.font_family_name, 'B', 15)
        self.cell(80) # Décalage vers la droite
        self.cell(30, 10, "Rapport d'Audit Patrimonial", 0, 0, 'C')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font(self.font_family_name, 'I', 8)
        page_number_text = f'Page {self.page_no()}/{{nb}}'
        self.cell(0, 10, page_number_text, 0, 0, 'C')

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

        # Header
        self.set_font(self.font_family_name, 'B', 10)
        self.set_fill_color(240, 240, 240)
        for i, col_name in enumerate(df.columns):
            self.cell(col_widths[i], 7, str(col_name), 1, 0, 'C', 1)
        self.ln()

        # Data
        self.set_font(self.font_family_name, '', 9)
        for index, row in df.iterrows():
            for i, item in enumerate(row):
                # Formatage des nombres
                if isinstance(item, (int, float)):
                    text = f"{item:,.2f}{self.currency_symbol}"
                    align = 'R'
                else:
                    text = str(item)
                    align = 'L'
                self.cell(col_widths[i], 6, text, 1, 0, align)
            self.ln()
        self.ln(10)

# --- Fonctions pour générer les sections du rapport ---

def add_title_page(pdf, parents):
    """Ajoute la page de titre du rapport."""
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
    """Ajoute la section sur la composition du foyer."""
    pdf.add_page()
    pdf.chapter_title("1. Composition du Foyer")
    
    pdf.set_font(pdf.font_family_name, 'B', 12)
    pdf.cell(0, 10, "Parents", 0, 1, 'L')
    pdf.set_font(pdf.font_family_name, '', 11)
    for p in parents:
        dob = p.get('date_naissance')
        dob_str = dob.strftime('%d/%m/%Y') if dob else "N/A"
        pdf.cell(0, 6, f"- {p.get('prenom', 'N/A')}, né(e) le {dob_str}", 0, 1, 'L')
    pdf.ln(5)

    if enfants:
        pdf.set_font(pdf.font_family_name, 'B', 12)
        pdf.cell(0, 10, "Enfants", 0, 1, 'L')
        pdf.set_font(pdf.font_family_name, '', 11)
        for e in enfants:
            dob = e.get('date_naissance')
            dob_str = dob.strftime('%d/%m/%Y') if dob else "N/A"
            pdf.cell(0, 6, f"- {e.get('prenom', 'N/A')}, né(e) le {dob_str}", 0, 1, 'L')

def add_patrimoine_section(pdf, actifs, passifs):
    """Ajoute la section sur le bilan patrimonial."""
    pdf.add_page()
    pdf.chapter_title("2. Bilan Patrimonial")

    df_patrimoine = get_patrimoine_df(actifs, passifs)
    if df_patrimoine.empty:
        pdf.chapter_body("Aucune donnée patrimoniale n'a été renseignée.")
        return

    total_actifs = df_patrimoine['Valeur Brute'].sum()
    total_passifs = df_patrimoine['Passif'].sum()
    patrimoine_net = df_patrimoine['Valeur Nette'].sum()

    pdf.chapter_body(
        f"Le total de vos actifs s'élève à {total_actifs:,.2f}{pdf.currency_symbol}.\n"
        f"Le total de vos passifs (dettes) est de {total_passifs:,.2f}{pdf.currency_symbol}.\n"
        f"Votre patrimoine net est donc de {patrimoine_net:,.2f}{pdf.currency_symbol}."
    )

    df_display = df_patrimoine[['Libellé', 'Type', 'Valeur Brute', 'Passif', 'Valeur Nette']]
    col_widths = [60, 40, 30, 30, 30]
    pdf.add_table(df_display, col_widths, "Détail du patrimoine")

def add_flux_section(pdf, revenus, depenses):
    """Ajoute la section sur les flux financiers."""
    pdf.add_page()
    pdf.chapter_title("3. Flux Financiers Mensuels")

    total_revenus = sum(r.get('montant', 0.0) for r in revenus)
    total_depenses = sum(d.get('montant', 0.0) for d in depenses)
    capacite_epargne = total_revenus - total_depenses

    pdf.chapter_body(
        f"Le total de vos revenus mensuels est de {total_revenus:,.2f}{pdf.currency_symbol}.\n"
        f"Le total de vos dépenses mensuelles est de {total_depenses:,.2f}{pdf.currency_symbol}.\n"
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

def add_immo_focus_section(pdf, actifs, passifs):
    """Ajoute la section focus immobilier avec les graphiques de projection."""
    productive_assets = [a for a in actifs if a.get('type') == "Immobilier productif"]
    if not productive_assets:
        return

    pdf.add_page()
    pdf.chapter_title("4. Focus Immobilier")

    # Récupérer les paramètres de simulation depuis le session_state
    tmi = st.session_state.get('immo_tmi', 30)
    projection_duration = st.session_state.get('immo_projection_duration', 15)
    social_tax = 17.2

    for asset in productive_assets:
        if asset.get('loyers_mensuels') is None:
            continue

        pdf.set_font(pdf.font_family_name, 'B', 12)
        pdf.cell(0, 10, f"Analyse de : {asset.get('libelle', 'Sans nom')}", 0, 1, 'L')
        pdf.ln(2)

        loan = find_associated_loan(asset.get('id'), passifs)
        df_projection = generate_projection_data(asset, loan, tmi, social_tax, projection_duration)

        if df_projection.empty:
            pdf.chapter_body("Pas de données de projection à afficher pour ce bien.")
            continue

        try:
            fig_cf = create_cash_flow_projection_fig(df_projection)
            fig_lev = create_leverage_projection_fig(df_projection)

            img_bytes_cf = pio.to_image(fig_cf, format="png", width=600, height=350, scale=2)
            img_bytes_lev = pio.to_image(fig_lev, format="png", width=600, height=350, scale=2)

            page_width = pdf.w - 2 * pdf.l_margin
            img_width = page_width / 2 - 5

            y_pos = pdf.get_y()
            pdf.image(io.BytesIO(img_bytes_cf), w=img_width)
            pdf.set_xy(pdf.l_margin + img_width + 10, y_pos)
            pdf.image(io.BytesIO(img_bytes_lev), w=img_width)
            pdf.ln(10)

        except Exception as e:
            pdf.set_font(pdf.font_family_name, '', 10)
            pdf.set_text_color(255, 0, 0)
            pdf.multi_cell(0, 5, f"Erreur lors de la génération des graphiques pour ce bien : {e}")
            pdf.set_text_color(0, 0, 0)
            pdf.ln(5)

def generate_report(parents, enfants, actifs, passifs, revenus, depenses):
    """Fonction principale pour créer l'objet PDF."""
    pdf = PDF()
    pdf.alias_nb_pages() # Active le comptage total des pages pour le footer

    # 1. Page de titre
    add_title_page(pdf, parents)

    # 2. Section Famille
    add_family_section(pdf, parents, enfants)

    # 3. Section Patrimoine
    add_patrimoine_section(pdf, actifs, passifs)

    # 4. Section Flux
    add_flux_section(pdf, revenus, depenses)

    # 5. Section Focus Immobilier
    add_immo_focus_section(pdf, actifs, passifs)

    # Génération du PDF en mémoire
    return bytes(pdf.output(dest='S'))

# --- Interface Streamlit ---

def main():
    st.title("📄 Génération de Rapport")
    st.markdown("Cette page vous permet de générer un rapport PDF synthétisant toutes les informations saisies dans l'application.")

    if not FPDF_AVAILABLE:
        st.error(
            "La bibliothèque `fpdf2` est nécessaire pour générer des rapports.\n"
            "Veuillez l'installer en exécutant la commande suivante dans votre terminal :\n\n"
            "`pip install fpdf2`"
        )
        st.stop()

    # Vérifier que les données de base existent
    if 'parents' not in st.session_state or not st.session_state.parents:
        st.warning("⚠️ Veuillez d'abord renseigner les informations du foyer dans la page **1_Famille**.")
        st.stop()

    st.markdown("---")
    st.info("Cliquez sur le bouton ci-dessous pour générer votre rapport personnalisé au format PDF.")

    # Bouton pour lancer la génération
    if st.button("🚀 Générer mon rapport PDF", use_container_width=True):
        with st.spinner("Création du rapport en cours..."):
            # Récupération de toutes les données du session_state
            parents = st.session_state.get('parents', [])
            enfants = st.session_state.get('enfants', [])
            actifs = st.session_state.get('actifs', [])
            passifs = st.session_state.get('passifs', [])
            revenus = st.session_state.get('revenus', [])
            depenses = st.session_state.get('depenses', [])

            # Génération du rapport
            pdf_data = generate_report(parents, enfants, actifs, passifs, revenus, depenses)

            # Création du nom de fichier dynamique
            client_name = parents[0].get('prenom', 'client') if parents else 'client'
            file_name = f"Rapport_Patrimonial_{client_name}_{date.today().strftime('%Y-%m-%d')}.pdf"

            # Bouton de téléchargement
            st.download_button(
                label="✅ Télécharger le rapport PDF",
                data=pdf_data,
                file_name=file_name,
                mime="application/pdf",
                use_container_width=True
            )

if __name__ == "__main__":
    main()