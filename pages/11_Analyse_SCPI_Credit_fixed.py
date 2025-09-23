import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy.optimize import fsolve

st.set_page_config(page_title="Analyse SCPI à Crédit", layout="wide")

st.title("🏢 Analyse d'Investissement SCPI à Crédit")
st.markdown("---")

# Interface utilisateur avec deux colonnes principales
col1, col2 = st.columns([1, 2])

with col1:
    # Section Hypothèses de l'investissement
    st.markdown("### 🏢 **Hypothèses de l'investissement**")
    
    with st.container():
        st.markdown('<div style="background-color: #e8f4fd; padding: 10px; border-radius: 5px;">', unsafe_allow_html=True)
        montant = st.number_input("**Montant**", value=50000, step=1000, format="%d")
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    dividende_net = st.number_input("Dividende net distribué", value=5.70, step=0.1, format="%.2f")
    st.write(f"💰 {dividende_net/100 * montant:,.2f} €")
    
    evolution_part = st.number_input("Evolution valeur de la part", value=1.00, step=0.1, format="%.2f")
    
    frais_entree = st.number_input("Frais d'entrée (dossier bancaire + caution / nantissement + notaire)", value=1.00, step=0.1, format="%.2f")
    st.write(f"💰 {frais_entree/100 * montant:,.2f} €")
    
    apport_col1, apport_col2 = st.columns(2)
    with apport_col1:
        st.write("**Apport**")
        st.write("500")
    with apport_col2:
        montant_finance = st.number_input("**Montant à financer**", value=50000, step=1000, format="%d")
    
    charges = st.number_input("Charges (Taxe Foncière + assurances + Copropriété)", value=0, step=50, format="%d")
    st.write(f"💰 {charges:,.2f} €")

    # Section Hypothèses du financement
    st.markdown("### 💰 **Hypothèses du financement**")
    
    taux_interet = st.number_input("Taux d'intérêt annuel", value=5.00, step=0.1, format="%.2f")
    taux_assurance = st.number_input("Taux d'assurance", value=0.20, step=0.01, format="%.2f")
    duree_emprunt = st.number_input("Durée de l'emprunt", value=25, step=1, format="%d")
    
    # Calcul des mensualités
    taux_mensuel = taux_interet / 100 / 12
    nb_mensualites = duree_emprunt * 12
    
    if taux_mensuel > 0:
        mensualite_hors_assurance = montant_finance * (taux_mensuel * (1 + taux_mensuel)**nb_mensualites) / ((1 + taux_mensuel)**nb_mensualites - 1)
    else:
        mensualite_hors_assurance = montant_finance / nb_mensualites
    
    mensualite_assurance = montant_finance * taux_assurance / 100 / 12
    mensualite_avec_assurance = mensualite_hors_assurance + mensualite_assurance
    
    st.write(f"**Mensualité SCPI hors assurance avec différé 3 mois:** {mensualite_hors_assurance:,.2f} €")
    st.write(f"**Mensualité SCPI avec assurance avec différé 3 mois:** {mensualite_avec_assurance:,.2f} €")

    # Section Fiscalité
    st.markdown("### 📊 **Fiscalité**")
    
    with st.container():
        st.markdown('<div style="background-color: #dc3545; color: white; padding: 10px; border-radius: 5px; text-align: center; font-weight: bold;">', unsafe_allow_html=True)
        st.markdown("**Fiscalité**")
        st.markdown("</div>", unsafe_allow_html=True)
    
    tmi = st.number_input("TMI (Tranche Marginale d'Imposition)", value=30.0, step=0.1, format="%.1f")
    charges_sociales = st.number_input("% Charges sociales", value=17.20, step=0.1, format="%.2f")
    total_fiscal = tmi + charges_sociales
    st.write(f"**Total:** {total_fiscal:.1f}%")
    
    # Section En synthèse
    st.markdown("### 🎯 **En synthèse**")
    
    with st.container():
        st.markdown('<div style="background-color: #6f42c1; color: white; padding: 10px; border-radius: 5px; text-align: center; font-weight: bold;">', unsafe_allow_html=True)
        st.markdown("**En synthèse**")
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Calculs de synthèse
    mensualite_si_revente = st.number_input("Mensualité de", value=608.81, step=0.01, format="%.2f")
    st.write("€")
    
    si_revente_ans = st.number_input("Si revente des SCPI à", value=15, step=1, format="%d")
    st.write("ans")
    
    prix_revente = st.number_input("Au prix de", value=104487, step=100, format="%d")
    st.write("€")
    
    capital_restant_revente = st.number_input("Capital restant dû", value=55116, step=100, format="%d")
    st.write("€")

with col2:
    # Tableau d'amortissement
    st.markdown("### 📈 **Tableau d'amortissement**")
    st.write("*Le tableau sera affiché après configuration des paramètres fiscaux*")

# Calcul du tableau d'amortissement (après définition de toutes les variables)
if 'tmi' in locals() and 'charges_sociales' in locals():
    # Calcul du tableau d'amortissement
    data = []
    capital_restant = montant_finance
    dividende_annuel = dividende_net / 100 * montant
    
    for annee in range(1, min(17, duree_emprunt + 1)):  # Limiter à 16 ans pour l'affichage
        # Calculs pour l'année
        interets_annuels = 0
        amortissement_annuel = 0
        capital_restant_temp = capital_restant
        
        for mois in range(12):
            if capital_restant_temp > 0:
                interet_mois = capital_restant_temp * taux_mensuel
                amortissement_mois = mensualite_hors_assurance - interet_mois
                
                interets_annuels += interet_mois
                amortissement_annuel += amortissement_mois
                capital_restant_temp -= amortissement_mois
                
                if capital_restant_temp < 0:
                    capital_restant_temp = 0
        
        # Calculs fiscaux et de rentabilité
        charges_deductibles = interets_annuels + charges + mensualite_assurance * 12
        bilan_foncier = dividende_annuel - charges_deductibles
        
        # Impact fiscal avec les paramètres définis
        taux_fiscal_total = (tmi + charges_sociales) / 100
        impact_fiscal = bilan_foncier * taux_fiscal_total if bilan_foncier > 0 else bilan_foncier * taux_fiscal_total
        
        dividende_net_apres_fiscalite = dividende_annuel + impact_fiscal
        
        # Rentabilité
        rentabilite_locative = (dividende_net_apres_fiscalite / montant) * 100
        
        # Effort d'épargne
        effort_epargne_annuel = mensualite_avec_assurance * 12 - dividende_net_apres_fiscalite
        effort_epargne_mensuel = effort_epargne_annuel / 12
        
        data.append({
            'Année': annee,
            'Mensualité annuelle': int(mensualite_avec_assurance * 12),
            'Montant dividende brut': int(dividende_annuel),
            'Intérêts + ADI': int(interets_annuels + mensualite_assurance * 12),
            'Charges déductibles': int(charges_deductibles),
            'Bilan foncier': int(bilan_foncier),
            'Impact fiscal': int(impact_fiscal),
            'Montant dividende net': int(dividende_net_apres_fiscalite),
            'Rentabilité locative': f"{rentabilite_locative:.2f}%",
            'Effort d\'épargne annuel': int(effort_epargne_annuel),
            'Effort d\'épargne mensuel': int(effort_epargne_mensuel)
        })
        
        capital_restant = capital_restant_temp
    
    # Création du DataFrame
    df_amortissement = pd.DataFrame(data)
    
    # Calcul correct du total effort d'épargne jusqu'à la revente
    total_effort_epargne_reel = sum([
        row['Effort d\'épargne annuel'] 
        for row in data 
        if row['Année'] <= si_revente_ans
    ])
    
    # Calculs automatiques
    solde_remboursement = prix_revente - capital_restant_revente
    benefice_net_reel = solde_remboursement - total_effort_epargne_reel
    
    # Fonction pour calculer le TRI correct
    def calculer_tri_correct():
        # Investissement initial (négatif car c'est une sortie de fonds)
        apport_initial = 500  # Apport personnel
        frais_entree_euros = frais_entree / 100 * montant
        investissement_initial = -(apport_initial + frais_entree_euros)
        
        # Construction des flux de trésorerie annuels
        flux_tresorerie = [investissement_initial]  # Année 0
        
        for i, row in enumerate(data):
            if row['Année'] <= si_revente_ans:
                # Flux réel = -Effort d'épargne (car c'est ce que l'investisseur sort de sa poche)
                effort_epargne_annuel = row['Effort d\'épargne annuel']
                
                if row['Année'] == si_revente_ans:
                    # Dernière année : -effort d'épargne + prix de revente - capital restant dû
                    flux_annuel = -effort_epargne_annuel + prix_revente - capital_restant_revente
                else:
                    # Années normales : l'investisseur sort l'effort d'épargne de sa poche
                    flux_annuel = -effort_epargne_annuel
                
                flux_tresorerie.append(flux_annuel)
        
        # Fonction pour calculer la VAN
        def van(taux):
            return sum([flux / (1 + taux) ** i for i, flux in enumerate(flux_tresorerie)])
        
        # Résolution numérique pour trouver le TRI (taux qui rend VAN = 0)
        try:
            tri_solution = fsolve(van, 0.05)[0]  # Estimation initiale à 5%
            return tri_solution * 100  # Conversion en pourcentage
        except:
            # En cas d'échec de la résolution numérique, utiliser une approximation
            if len(flux_tresorerie) > 1:
                total_gains = sum(flux_tresorerie[1:])
                if investissement_initial != 0:
                    return (total_gains / abs(investissement_initial)) ** (1/len(flux_tresorerie[1:])) - 1
            return 0
    
    # Calcul du TRI corrigé
    tri_reel = calculer_tri_correct()

# Affichage des résultats corrigés dans la colonne 1
with col1:
    st.write(f"**Total effort d'épargne (corrigé):** {total_effort_epargne_reel:,.0f} €")
    st.write(f"**Bénéfice net de l'opération (corrigé):** {benefice_net_reel:,.0f} €")
    
    st.markdown("---")
    st.markdown(f"**Soit un taux de rendement interne (TRI) de:** {tri_reel:.2f}%")
    st.markdown("*️⃣ TRI calculé selon la méthode financière standard (VAN = 0)*")
    
    st.markdown("---")
    st.markdown(f"*Il faudrait placer votre effort d'épargne à un taux de* **{tri_reel:.2f}%**")
    st.markdown(f"*pour obtenir un capital de* **{solde_remboursement:,.0f} €**")
    st.markdown(f"*au bout de* **{si_revente_ans} ans**")
    
    # Affichage détaillé du calcul TRI (optionnel, en expander)
    with st.expander("📊 Détails du calcul du TRI"):
        st.markdown("**Méthode de calcul :**")
        st.markdown("Le TRI est le taux d'actualisation qui rend la Valeur Actuelle Nette (VAN) égale à zéro.")
        st.markdown("**Formule :** VAN = Σ(Flux_année / (1 + TRI)^année) = 0")
        
        st.markdown("**Flux de trésorerie pris en compte :**")
        st.markdown(f"• **Année 0 :** -{500 + frais_entree/100 * montant:,.0f} € (Apport + Frais d'entrée)")
        st.markdown(f"• **Années 1 à {si_revente_ans-1} :** -Effort d'épargne (ce que vous sortez de votre poche)")
        st.markdown(f"• **Année {si_revente_ans} :** -Effort d'épargne + Prix revente - Capital restant dû")
        st.markdown(f"  = -Effort + {prix_revente:,.0f} € - {capital_restant_revente:,.0f} € = +{prix_revente - capital_restant_revente:,.0f} € net de revente")
        
        st.markdown(f"**Investissement initial :** {500 + frais_entree/100 * montant:,.0f} € (apport + frais)")
        
        st.markdown("**Flux de trésorerie annuels :**")
        flux_detail = []
        for i, row in enumerate(data):
            if row['Année'] <= si_revente_ans:
                effort_epargne_annuel = row['Effort d\'épargne annuel']
                
                if row['Année'] == si_revente_ans:
                    flux_annuel = -effort_epargne_annuel + prix_revente - capital_restant_revente
                    flux_detail.append(f"Année {row['Année']}: {flux_annuel:,.0f} € (incluant revente)")
                else:
                    flux_annuel = -effort_epargne_annuel
                    flux_detail.append(f"Année {row['Année']}: {flux_annuel:,.0f} € (effort d'épargne)")
        
        for detail in flux_detail:
            st.markdown(f"- {detail}")

with col2:
    # Affichage du tableau d'amortissement dans la colonne 2
    
    # Configuration de l'affichage du tableau avec couleurs
    def color_negative_red(val):
        if isinstance(val, str):
            return ''
        color = 'red' if val < 0 else 'black'
        return f'color: {color}'
    
    # Affichage du tableau avec style
    styled_df = df_amortissement.style.applymap(color_negative_red, subset=['Bilan foncier', 'Impact fiscal', 'Effort d\'épargne annuel', 'Effort d\'épargne mensuel'])
    
    st.dataframe(styled_df, use_container_width=True, height=600)
    
    # Graphiques de synthèse
    st.markdown("### 📊 **Graphiques de synthèse**")
    
    # Graphique de l'évolution de l'effort d'épargne
    fig_effort = px.line(
        df_amortissement, 
        x='Année', 
        y='Effort d\'épargne mensuel',
        title="Évolution de l'effort d'épargne mensuel",
        labels={'Effort d\'épargne mensuel': 'Effort d\'épargne (€)'}
    )
    fig_effort.add_hline(y=0, line_dash="dash", line_color="red")
    st.plotly_chart(fig_effort, use_container_width=True)
    
    # Graphique de la rentabilité locative
    rentabilite_values = [float(x.rstrip('%')) for x in df_amortissement['Rentabilité locative']]
    fig_rentabilite = px.line(
        x=df_amortissement['Année'],
        y=rentabilite_values,
        title="Évolution de la rentabilité locative",
        labels={'x': 'Année', 'y': 'Rentabilité (%)'}
    )
    st.plotly_chart(fig_rentabilite, use_container_width=True)

# Section de résumé en bas
if 'df_amortissement' in locals():
    st.markdown("---")
    st.markdown("### 📋 **Résumé de l'investissement**")

    col_resume1, col_resume2, col_resume3, col_resume4 = st.columns(4)

    with col_resume1:
        st.metric("**Montant investi**", f"{montant:,.0f} €")
        st.metric("**Apport personnel**", "500 €")

    with col_resume2:
        dividende_annuel = dividende_net / 100 * montant
        st.metric("**Dividende annuel brut**", f"{dividende_annuel:,.0f} €")
        st.metric("**Mensualité avec assurance**", f"{mensualite_avec_assurance:,.0f} €")

    with col_resume3:
        premier_effort = df_amortissement.iloc[0]['Effort d\'épargne mensuel']
        st.metric("**Effort d'épargne initial**", f"{premier_effort:,.0f} € / mois")
        rentabilite_values = [float(x.rstrip('%')) for x in df_amortissement['Rentabilité locative']]
        rentabilite_initiale = rentabilite_values[0]
        st.metric("**Rentabilité locative initiale**", f"{rentabilite_initiale:.2f}%")

    with col_resume4:
        # Calcul du point d'équilibre (effort d'épargne = 0)
        efforts_mensuels = [row['Effort d\'épargne mensuel'] for row in data]
        point_equilibre = "Non atteint"
        for i, effort in enumerate(efforts_mensuels):
            if effort <= 0:
                point_equilibre = f"Année {i+1}"
                break
        
        st.metric("**Point d'équilibre**", point_equilibre)
        st.metric("**Durée du prêt**", f"{duree_emprunt} ans")