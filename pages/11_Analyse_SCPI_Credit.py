import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy.optimize import fsolve

st.set_page_config(page_title="Analyse SCPI à Crédit", layout="wide")

st.title("🏢 Analyse d'Investissement SCPI à Crédit")
st.markdown("---")

# Paramètres dans la barre latérale
with st.sidebar:
    st.header("⚙️ Paramètres")
    
    # Section Hypothèses de l'investissement
    st.markdown("### 🏢 **Hypothèses de l'investissement**")
    
    with st.container():
        st.markdown('<div style="background-color: #e8f4fd; padding: 10px; border-radius: 5px;">', unsafe_allow_html=True)
        montant = st.number_input("**Montant**", value=50000, step=1000, format="%d")
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    div_col1, div_col2 = st.columns(2)
    with div_col1:
        dividende_net = st.number_input("Dividende net distribué", value=5.70, step=0.1, format="%.2f")
    with div_col2:
        st.write("**Montant annuel**")
        st.write(f"💰 {dividende_net/100 * montant:,.2f} €")
    
    # Délai de jouissance (déplacé sous le dividende)
    delai_jouissance = st.number_input("Délai de jouissance (en mois)", value=3, step=1, format="%d", min_value=0, max_value=12)
    
    # Organisation sur deux colonnes
    invest_col1, invest_col2 = st.columns(2)
    
    with invest_col1:
        evolution_part = st.number_input("Evolution valeur de la part", value=1.00, step=0.1, format="%.2f")
        apport = st.number_input("**Apport**", value=500, step=100, format="%d")
        
    with invest_col2:
        frais_entree = st.number_input("Frais d'entrée (%)", value=1.00, step=0.1, format="%.2f")
        charges = st.number_input("Charges annuelles", value=0, step=50, format="%d")
    
    # Affichage des montants calculés
    st.write(f"**Frais d'entrée:** {frais_entree/100 * montant:,.0f} €")
    st.write(f"**Montant à financer:** {montant - apport:,.0f} €")
    montant_finance = montant - apport

    # Section Hypothèses du financement
    st.markdown("### 💰 **Hypothèses du financement**")
    
    # Organisation sur deux colonnes
    finance_col1, finance_col2 = st.columns(2)
    
    with finance_col1:
        taux_interet = st.number_input("Taux d'intérêt annuel", value=5.00, step=0.1, format="%.2f")
        duree_emprunt = st.number_input("Durée de l'emprunt", value=25, step=1, format="%d")
        nb_mois_differe = st.number_input("Nombre de mois de différé", value=3, step=1, format="%d", min_value=0, max_value=24)
        
    with finance_col2:
        taux_assurance = st.number_input("Taux d'assurance", value=0.20, step=0.01, format="%.2f")
        type_differe = st.selectbox("Type de différé", 
                                   options=["Différé partiel", "Différé total"],
                                   index=0)
    
    # Calcul des mensualités
    taux_mensuel = taux_interet / 100 / 12
    nb_mensualites = duree_emprunt * 12
    
    if taux_mensuel > 0:
        mensualite_hors_assurance = montant_finance * (taux_mensuel * (1 + taux_mensuel)**nb_mensualites) / ((1 + taux_mensuel)**nb_mensualites - 1)
    else:
        mensualite_hors_assurance = montant_finance / nb_mensualites
    
    mensualite_assurance = montant_finance * taux_assurance / 100 / 12
    mensualite_avec_assurance = mensualite_hors_assurance + mensualite_assurance
    
    # Calcul de la mensualité pendant le différé (si différé partiel)
    if type_differe == "Différé partiel":
        mensualite_differe = mensualite_assurance  # Seulement assurance pendant le différé
    else:
        mensualite_differe = 0  # Aucun remboursement pendant le différé total
    
    st.write(f"**Mensualité SCPI hors assurance avec différé {nb_mois_differe} mois:** {mensualite_hors_assurance:,.2f} €")
    st.write(f"**Mensualité SCPI avec assurance avec différé {nb_mois_differe} mois:** {mensualite_avec_assurance:,.2f} €")
    if nb_mois_differe > 0:
        st.write(f"**Mensualité pendant le différé ({type_differe.lower()}):** {mensualite_differe:,.2f} €")

    # Section Fiscalité
    st.markdown("### 📊 **Fiscalité**")
    
    # Organisation sur deux colonnes
    fiscal_col1, fiscal_col2 = st.columns(2)
    
    with fiscal_col1:
        tmi = st.number_input("TMI (%)", value=30.0, step=0.1, format="%.1f")
        
    with fiscal_col2:
        charges_sociales = st.number_input("Charges sociales (%)", value=17.20, step=0.1, format="%.2f")
    
    total_fiscal = tmi + charges_sociales
    st.write(f"**Total fiscal:** {total_fiscal:.1f}%")
    
    # Paramètres de revente
    st.markdown("### 📅 **Paramètres de revente**")
    si_revente_ans = st.number_input("Revente prévue à l'année", value=15, step=1, format="%d", min_value=1, max_value=25)

# Contenu principal - Tableau d'amortissement

# Calcul du tableau d'amortissement (après définition de toutes les variables)
if 'tmi' in locals() and 'charges_sociales' in locals():
    # Calcul du tableau d'amortissement
    data = []
    capital_restant = montant_finance
    dividende_annuel = dividende_net / 100 * montant
    deficit_foncier_reporte = 0  # Pour gérer le report de déficit foncier
    
    for annee in range(1, min(si_revente_ans + 1, duree_emprunt + 1)):  # S'arrêter à l'année de revente
        # Calculs pour l'année
        interets_annuels = 0
        amortissement_annuel = 0
        capital_restant_temp = capital_restant
        
        # Dividende effectif en fonction du délai de jouissance
        if annee == 1 and delai_jouissance > 0:
            # Première année avec délai de jouissance
            mois_dividende_effectifs = 12 - delai_jouissance
            dividende_annuel_effectif = dividende_annuel * (mois_dividende_effectifs / 12)
        else:
            dividende_annuel_effectif = dividende_annuel
        
        for mois in range(12):
            if capital_restant_temp > 0:
                # Gestion du différé
                est_en_differe = (annee == 1 and mois < nb_mois_differe)
                
                if est_en_differe:
                    # Pendant le différé
                    interet_mois = capital_restant_temp * taux_mensuel
                    if type_differe == "Différé partiel":
                        # Différé partiel : on paye seulement l'assurance
                        amortissement_mois = 0
                    else:
                        # Différé total : on ne paye rien, les intérêts s'ajoutent au capital
                        amortissement_mois = -interet_mois  # Les intérêts s'ajoutent au capital
                        interet_mois = 0  # Pas de paiement d'intérêts pendant le différé total
                else:
                    # Fonctionnement normal
                    interet_mois = capital_restant_temp * taux_mensuel
                    amortissement_mois = mensualite_hors_assurance - interet_mois
                
                interets_annuels += interet_mois
                amortissement_annuel += amortissement_mois
                capital_restant_temp -= amortissement_mois
                
                if capital_restant_temp < 0:
                    capital_restant_temp = 0
        
        # Calculs fiscaux et de rentabilité
        charges_deductibles = interets_annuels + charges + mensualite_assurance * 12
        bilan_foncier_annuel = dividende_annuel_effectif - charges_deductibles
        
        # Gestion du déficit foncier avec report
        # Si on a un déficit reporté des années précédentes, on l'utilise d'abord
        if deficit_foncier_reporte > 0:
            # On compense le bilan positif avec le déficit reporté
            if bilan_foncier_annuel > 0:
                # Utilisation partielle ou totale du déficit reporté
                compensation = min(deficit_foncier_reporte, bilan_foncier_annuel)
                bilan_foncier_total = bilan_foncier_annuel - compensation
                deficit_foncier_reporte -= compensation
            else:
                # Bilan annuel négatif, on accumule les déficits
                bilan_foncier_total = bilan_foncier_annuel  # Reste négatif
                deficit_foncier_reporte += abs(bilan_foncier_annuel)
        else:
            # Pas de déficit reporté
            bilan_foncier_total = bilan_foncier_annuel
            if bilan_foncier_annuel < 0:
                deficit_foncier_reporte = abs(bilan_foncier_annuel)
        
        # Impact fiscal avec les paramètres définis
        taux_fiscal_total = (tmi + charges_sociales) / 100
        
        if bilan_foncier_total > 0:
            # Bilan positif = supplément d'impôt à payer (impact négatif)
            impact_fiscal = -(bilan_foncier_total * taux_fiscal_total)
        else:
            # Bilan négatif ou nul = pas d'impôt à payer
            impact_fiscal = 0
        
        dividende_net_apres_fiscalite = dividende_annuel_effectif + impact_fiscal
        
        # Calcul de la mensualité annuelle effective selon le différé
        if annee == 1 and nb_mois_differe > 0:
            # Première année avec différé
            mois_normaux = 12 - nb_mois_differe
            if type_differe == "Différé partiel":
                # Différé partiel : assurance pendant le différé + mensualité normale après
                mensualite_annuelle_effective = (mensualite_differe * nb_mois_differe) + (mensualite_avec_assurance * mois_normaux)
            else:
                # Différé total : rien pendant le différé + mensualité normale après
                mensualite_annuelle_effective = mensualite_avec_assurance * mois_normaux
        else:
            # Années normales
            mensualite_annuelle_effective = mensualite_avec_assurance * 12
        
        # Rentabilité (sur le montant total incluant frais d'entrée)
        rentabilite_locative = (dividende_net_apres_fiscalite / montant) * 100
        
        # Effort d'épargne
        effort_epargne_annuel = mensualite_annuelle_effective - dividende_net_apres_fiscalite
        effort_epargne_mensuel = effort_epargne_annuel / 12
        
        # Valeur de revente potentielle des parts (évolution sur montant HORS frais d'entrée)
        # La revalorisation s'applique sur la valeur d'investissement moins les frais d'entrée
        montant_net_pour_revalorisation = montant - (frais_entree / 100 * montant)
        valeur_parts_potentielle = montant_net_pour_revalorisation * ((1 + evolution_part / 100) ** annee)
        
        # Flux de trésorerie pour le calcul du TRI
        # Le flux TRI représente ce que l'investisseur sort (-) ou récupère (+) de sa poche
        flux_tri_annuel = -effort_epargne_annuel  # Négatif car c'est une sortie de fonds
        
        data.append({
            'Année': annee,
            'Mensualité annuelle': int(mensualite_annuelle_effective),
            'Montant dividende brut': int(dividende_annuel_effectif),
            'Intérêts + ADI': int(interets_annuels + mensualite_assurance * 12),
            'Charges déductibles': int(charges_deductibles),
            'Bilan foncier': int(bilan_foncier_total),
            'Impact fiscal': int(impact_fiscal),
            'Déficit reportable': int(deficit_foncier_reporte),
            'Montant dividende net': int(dividende_net_apres_fiscalite),
            'Rentabilité locative': f"{rentabilite_locative:.2f}%",
            'Effort d\'épargne annuel': int(effort_epargne_annuel),
            'Cumul effort épargne': 0,  # Sera calculé après création du DataFrame
            'Effort d\'épargne mensuel': int(effort_epargne_mensuel),
            'Valeur parts': int(valeur_parts_potentielle),
            'CRD': int(capital_restant_temp),
            'Flux TRI': int(flux_tri_annuel)
        })
        
        capital_restant = capital_restant_temp
    
    # Création du DataFrame
    df_amortissement = pd.DataFrame(data)
    
    # Calcul du cumul d'effort d'épargne
    cumul_effort = 0
    for i in range(len(df_amortissement)):
        cumul_effort += df_amortissement.loc[i, 'Effort d\'épargne annuel']
        df_amortissement.loc[i, 'Cumul effort épargne'] = int(cumul_effort)
    
    # Ajout du flux de revente pour l'année de revente dans le tableau
    if si_revente_ans <= len(data):
        # Ajout du flux de revente dans la colonne Flux TRI pour l'année de revente
        idx_revente = si_revente_ans - 1  # Index 0-based
        
        # Utiliser le CRD réel du tableau au lieu de la valeur saisie manuellement
        crd_reel_revente = df_amortissement.loc[idx_revente, 'CRD']
        valeur_parts_revente = df_amortissement.loc[idx_revente, 'Valeur parts']
        flux_revente = valeur_parts_revente - crd_reel_revente
        
        df_amortissement.loc[idx_revente, 'Flux TRI'] = (
            df_amortissement.loc[idx_revente, 'Flux TRI'] + flux_revente
        )
        # Mettre à jour la note avec les vraies valeurs
        df_amortissement.loc[idx_revente, 'Note'] = f'Incl. revente: +{flux_revente:,.0f}€'
    
    # Compléter les lignes qui n'ont pas de note
    df_amortissement['Note'] = df_amortissement.get('Note', '').fillna('')
    
    # Calcul correct du total effort d'épargne jusqu'à la revente
    # Utiliser directement la valeur du cumul dans le tableau
    if si_revente_ans <= len(df_amortissement):
        idx_revente = si_revente_ans - 1
        total_effort_epargne_reel = df_amortissement.loc[idx_revente, 'Cumul effort épargne']
    else:
        total_effort_epargne_reel = 0
    
    # Calculs automatiques avec les valeurs réelles du tableau
    if si_revente_ans <= len(data):
        idx_revente = si_revente_ans - 1
        crd_reel_revente = df_amortissement.loc[idx_revente, 'CRD']
        valeur_parts_revente = df_amortissement.loc[idx_revente, 'Valeur parts']
        solde_remboursement_reel = valeur_parts_revente - crd_reel_revente
    else:
        # Fallback si pas de données (ne devrait jamais arriver)
        solde_remboursement_reel = 0
        st.error("⚠️ Erreur dans le calcul: année de revente supérieure à la durée du tableau")
    
    benefice_net_reel = solde_remboursement_reel - total_effort_epargne_reel
    
    # Fonction pour calculer le TRI correct
    def calculer_tri_correct():
        # Construction des flux de trésorerie annuels directement depuis le tableau
        flux_tresorerie = []  # SANS flux initial (comme Excel)
        
        for i, row in df_amortissement.iterrows():
            if row['Année'] <= si_revente_ans:
                flux_tresorerie.append(row['Flux TRI'])
        
        # Fonction pour calculer la VAN (méthode Excel - flux commencent à année 1)
        def van_excel_style(taux):
            return sum([flux / (1 + taux) ** (i+1) for i, flux in enumerate(flux_tresorerie)])
        
        # Résolution numérique pour trouver le TRI (taux qui rend VAN = 0)
        try:
            # Méthode de Brent (plus stable qu'fsolve, comme Excel)
            from scipy.optimize import brentq
            tri_solution = brentq(van_excel_style, -0.99, 5.0)  # Recherche entre -99% et 500%
            return tri_solution * 100  # Conversion en pourcentage
        except:
            try:
                # Fallback avec fsolve si Brent échoue
                tri_solution = fsolve(van_excel_style, 0.05)[0]  # Estimation initiale à 5%
                return tri_solution * 100  # Conversion en pourcentage
            except:
                # En cas d'échec total, approximation simple
                if len(flux_tresorerie) > 1:
                    flux_positifs = [f for f in flux_tresorerie if f > 0]
                    flux_negatifs = [f for f in flux_tresorerie if f < 0]
                    if flux_positifs and flux_negatifs:
                        return ((sum(flux_positifs) / abs(sum(flux_negatifs))) ** (1/len(flux_tresorerie)) - 1) * 100
                return 0
    
    # Calcul du TRI corrigé
    tri_reel = calculer_tri_correct()

# Affichage des KPI principaux
st.markdown("### 📊 **KPI de l'investissement**")

kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5 = st.columns(5)

with kpi_col1:
    st.metric(
        label="💎 Valeur des parts",
        value=f"{valeur_parts_revente:,.0f} €",
        help=f"Valeur des parts à l'année {si_revente_ans}"
    )

with kpi_col2:
    st.metric(
        label="💳 CRD restant",
        value=f"{crd_reel_revente:,.0f} €",
        help=f"Capital restant dû à l'année {si_revente_ans}"
    )

with kpi_col3:
    st.metric(
        label="📈 Total effort d'épargne",
        value=f"{total_effort_epargne_reel:,.0f} €",
        help=f"Cumul de l'effort d'épargne sur {si_revente_ans} ans"
    )

with kpi_col4:
    capital_constitue = valeur_parts_revente - crd_reel_revente
    st.metric(
        label="🏆 Capital constitué",
        value=f"{capital_constitue:,.0f} €",
        help="Montant net récupéré après revente et solde du crédit"
    )

with kpi_col5:
    st.metric(
        label="📊 TRI",
        value=f"{tri_reel:.2f} %",
        help="Taux de Rendement Interne de l'investissement"
    )

# Deuxième ligne de KPI - Détails opérationnels
kpi2_col1, kpi2_col2, kpi2_col3, kpi2_col4, kpi2_col5, kpi2_col6 = st.columns(6)

with kpi2_col1:
    # Calcul du loyer mensuel (dividende mensuel)
    loyer_mensuel = (dividende_net / 100 * montant) / 12
    st.metric(
        label="🏠 Loyer mensuel",
        value=f"{loyer_mensuel:,.0f} €",
        help="Dividende mensuel brut perçu"
    )

with kpi2_col2:
    st.metric(
        label="💰 Mensualité crédit",
        value=f"{mensualite_avec_assurance:,.0f} €",
        help="Mensualité totale (capital + intérêts + assurance)"
    )

with kpi2_col3:
    # Calcul de la fiscalité mensuelle moyenne
    if 'df_amortissement' in locals() and len(df_amortissement) > 0:
        impacts_fiscaux = []
        for row in data:
            impacts_fiscaux.append(row['Impact fiscal'])
        fiscalite_annuelle_moyenne = sum(impacts_fiscaux) / len(impacts_fiscaux)
        fiscalite_mensuelle = fiscalite_annuelle_moyenne / 12
    else:
        fiscalite_mensuelle = 0
    
    st.metric(
        label="🧾 Fiscalité moyenne",
        value=f"{fiscalite_mensuelle:,.0f} €/mois",
        help="Impact fiscal mensuel moyen (économie d'impôt si négatif)"
    )

with kpi2_col4:
    # Calcul de l'effort d'épargne mensuel moyen
    if 'df_amortissement' in locals() and len(df_amortissement) > 0:
        efforts_mensuels = []
        for row in data:
            efforts_mensuels.append(row['Effort d\'épargne mensuel'])
        effort_moyen = sum(efforts_mensuels) / len(efforts_mensuels)
    else:
        effort_moyen = 0
    
    st.metric(
        label="📊 Effort épargne moyen",
        value=f"{effort_moyen:,.0f} €/mois",
        help="Effort d'épargne mensuel moyen sur la période"
    )

with kpi2_col5:
    # Calcul de l'enrichissement mensuel
    # Enrichissement = Capital constitué / nombre de mois (pour illustrer l'effet de levier)
    enrichissement_mensuel = capital_constitue / (si_revente_ans * 12)
    
    st.metric(
        label="💎 Enrichissement mensuel",
        value=f"{enrichissement_mensuel:,.0f} €/mois",
        help="Capital constitué divisé par la durée de l'investissement (illustre l'effet de levier du crédit)"
    )

with kpi2_col6:
    # Calcul de l'effet de levier
    # Effet de levier = Enrichissement mensuel / Effort d'épargne mensuel moyen
    if effort_moyen > 0:
        effet_levier = enrichissement_mensuel / effort_moyen
        multiplicateur = effet_levier
    else:
        effet_levier = 0
        multiplicateur = 0
    
    st.metric(
        label="⚡ Effet de levier",
        value=f"{multiplicateur:.2f}x",
        delta=f"{effet_levier*100:.1f}%" if effet_levier > 0 else "0%",
        help="Ratio enrichissement mensuel / effort d'épargne mensuel (illustre l'efficacité du levier financier)"
    )

st.markdown("---")

# Affichage du tableau d'amortissement dans un expander
with st.expander("📈 **Tableau d'amortissement détaillé**", expanded=False):
    # Configuration de l'affichage du tableau avec couleurs
    def color_negative_red(val):
        if isinstance(val, str):
            return ''
        color = 'red' if val < 0 else 'black'
        return f'color: {color}'

    # Affichage du tableau avec style
    styled_df = df_amortissement.style.applymap(color_negative_red, subset=['Bilan foncier', 'Impact fiscal', 'Effort d\'épargne annuel', 'Effort d\'épargne mensuel', 'Flux TRI'])

    st.dataframe(styled_df, use_container_width=True, height=600)

# Graphique Waterfall - Décomposition du capital final
st.markdown("### 💧 **Analyse Waterfall - Composition du capital final**")

# Calcul des composants pour le waterfall
loyers_totaux = sum([row['Montant dividende brut'] for row in data])
mensualites_totales = sum([row['Mensualité annuelle'] for row in data])
impact_fiscal_total = sum([row['Impact fiscal'] for row in data])
plus_value_parts = valeur_parts_revente - montant

# Données pour le graphique waterfall
categories = [
    'Total mensualités',
    'Fiscalité',
    'Loyers',
    'Effort épargne',
    'Valeur de revente',
    'CRD',
    'Capital constitué'
]

valeurs = [
    -mensualites_totales,  # Sortie d'argent (négatif)
    impact_fiscal_total,   # Économie ou coût fiscal
    loyers_totaux,         # Entrée d'argent (positif)
    total_effort_epargne_reel,  # Effort d'épargne du tableau d'amortissement (positif)
    valeur_parts_revente,  # Valeur de revente des parts (positif)
    -crd_reel_revente,     # CRD restant à rembourser (négatif)
    capital_constitue      # Capital final constitué
]

# Calcul des positions pour le waterfall
positions_y = []
cumul = 0  # On commence à 0

for i, val in enumerate(valeurs):
    if i == 0:  # Total mensualités (première barre, négative)
        positions_y.append(0)  # Base à 0
        cumul = val
    elif i == len(valeurs) - 1:  # Capital constitué (dernière barre)
        positions_y.append(capital_constitue)
    else:
        if val > 0:
            positions_y.append(cumul)
            cumul += val
        else:
            positions_y.append(cumul + val)
            cumul += val

# Couleurs pour le graphique
couleurs = []
for i, val in enumerate(valeurs):
    if i == 0:  # Total mensualités (coût)
        couleurs.append('#F18F01')  # Orange pour les coûts
    elif i == 1:  # Fiscalité
        couleurs.append('#A23B72' if val > 0 else '#F18F01')  # Rose si économie, orange si coût
    elif i == 2:  # Loyers (gain)
        couleurs.append('#A23B72')  # Rose pour les gains
    elif i == 3:  # Effort épargne (coût initial mais affiché positivement)
        couleurs.append('#2E86AB')  # Bleu pour l'effort d'épargne
    elif i == 4:  # Valeur de revente (gain)
        couleurs.append('#A23B72')  # Rose pour les gains
    elif i == 5:  # CRD (coût)
        couleurs.append('#F18F01')  # Orange pour les coûts
    elif i == len(valeurs) - 1:  # Capital final
        couleurs.append('#2E86AB')  # Bleu pour le résultat final
    else:
        couleurs.append('#2E86AB')  # Bleu par défaut

# Création du graphique waterfall avec Plotly
import plotly.graph_objects as go

fig = go.Figure()

# Barres principales
for i, (cat, val, pos, couleur) in enumerate(zip(categories, valeurs, positions_y, couleurs)):
    if i == 0:  # Première barre (Total mensualités - négatif)
        fig.add_trace(go.Bar(
            x=[cat],
            y=[abs(val)],
            base=[val],
            name=cat,
            marker_color=couleur,
            text=f'{val:,.0f} €',
            textposition='outside',
            showlegend=False
        ))
    elif i == len(valeurs) - 1:  # Dernière barre (capital final)
        fig.add_trace(go.Bar(
            x=[cat],
            y=[val],
            name=cat,
            marker_color=couleur,
            text=f'{val:,.0f} €',
            textposition='outside',
            showlegend=False
        ))
    else:  # Barres intermédiaires
        if val > 0:
            fig.add_trace(go.Bar(
                x=[cat],
                y=[val],
                base=[pos],
                name=cat,
                marker_color=couleur,
                text=f'+{val:,.0f} €',
                textposition='outside',
                showlegend=False
            ))
        else:
            fig.add_trace(go.Bar(
                x=[cat],
                y=[abs(val)],
                base=[pos],
                name=cat,
                marker_color=couleur,
                text=f'{val:,.0f} €',
                textposition='outside',
                showlegend=False
            ))

# Lignes de connexion entre les étapes
# Simplifiées pour la nouvelle structure
for i in range(len(categories) - 1):
    if i < len(categories) - 2:  # Toutes les connexions sauf vers la dernière barre
        cumul_actuel = sum(valeurs[:i+1])
        cumul_suivant = sum(valeurs[:i+2])
        
        fig.add_shape(
            type="line",
            x0=i + 0.4,
            y0=cumul_actuel,
            x1=i + 1 - 0.4,
            y1=cumul_actuel,
            line=dict(color="lightgray", width=1, dash="dot")
        )

# Mise en forme du graphique
fig.update_layout(
    title="Décomposition du capital constitué - Analyse des flux financiers",
    xaxis_title="Composants",
    yaxis_title="Montant (€)",
    template="plotly_white",
    height=500,
    showlegend=False,
    yaxis=dict(
        tickformat=',.0f',
        title_font_size=14
    ),
    xaxis=dict(
        title_font_size=14,
        tickangle=45
    ),
    title_font_size=16,
    title_x=0.5
)

# Ajout d'annotations explicatives
fig.add_annotation(
    text=f"🏆 Capital constitué: {capital_constitue:,.0f} €<br>💰 Effort d'épargne total: {total_effort_epargne_reel:,.0f} €<br>⚡ Effet de levier: {capital_constitue/total_effort_epargne_reel:.1f}x",
    xref="paper", yref="paper",
    x=0.02, y=0.98,
    showarrow=False,
    font=dict(size=12),
    align="left",
    bordercolor="black",
    borderwidth=1,
    bgcolor="white"
)

# Annotation pour expliquer le calcul final
fig.add_annotation(
    text=f"💡 Le waterfall montre comment chaque flux<br>contribue au capital final constitué",
    xref="paper", yref="paper",
    x=0.98, y=0.02,
    showarrow=False,
    font=dict(size=11),
    align="right",
    bordercolor="blue",
    borderwidth=1,
    bgcolor="lightblue"
)

st.plotly_chart(fig, use_container_width=True)