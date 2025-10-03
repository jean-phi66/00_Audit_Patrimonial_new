"""
Module des composants d'interface utilisateur pour le simulateur d'investissement
Contient toutes les fonctions d'affichage des tableaux, graphiques et éléments UI
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, Any
from core.optim_calculations import calculer_donnees_tableau_actifs
from core.optim_simulation_financiere import formater_resultat_optimisation, creer_donnees_graphique_waterfall


def afficher_sidebar_parametres():
    """
    Affiche la sidebar avec les paramètres de simulation.
    
    Returns:
        Dictionnaire avec les valeurs des paramètres saisis
    """
    # Initialisation des valeurs par défaut dans session_state si nécessaire
    if 'optim_sidebar_params' not in st.session_state:
        st.session_state.optim_sidebar_params = {
            'effort_max': 1000.0,
            'mensualite_max': 600.0,
            'capital_initial_max': 50000.0,
            'plafond_per_annuel': st.session_state.optim_params.get('plafond_per_annuel', 27840.0)
        }
    
    with st.sidebar:
        st.header("🔧 Paramètres de simulation")
        
        # Paramètres de contraintes
        st.subheader("Contraintes d'optimisation")
        
        #col1, col2 = st.columns(2)
        #with col1:
        effort_max = st.number_input(
            "Épargne max",
            min_value=0.0,
            value=st.session_state.optim_sidebar_params['effort_max'],
            step=50.0,
            help="€/mois",
            key="optim_effort_max_input"
        )
    
        #with col2:
        mensualite_max = st.number_input(
            "Crédit SCPI max",
            min_value=0.0,
            value=st.session_state.optim_sidebar_params['mensualite_max'],
            step=50.0,
            help="€/mois",
            key="optim_mensualite_max_input"
        )
    
        capital_initial_max = st.number_input(
            "Capital initial max (€)",
            min_value=0.0,
            value=st.session_state.optim_sidebar_params['capital_initial_max'],
            step=1000.0,
            key="optim_capital_initial_max_input"
        )
                
        plafond_per_annuel = st.number_input(
            "Plafond PER annuel (€)",
            min_value=0.0,
            value=st.session_state.optim_sidebar_params['plafond_per_annuel'],
            step=100.0,
            key="optim_plafond_per_annuel_input"
        )
        
        # Sauvegarde des valeurs dans session_state
        st.session_state.optim_sidebar_params.update({
            'effort_max': effort_max,
            'mensualite_max': mensualite_max,
            'capital_initial_max': capital_initial_max,
            'plafond_per_annuel': plafond_per_annuel
        })
    
    return {
        'effort_max': effort_max,
        'mensualite_max': mensualite_max,
        'capital_initial_max': capital_initial_max,
        'plafond_per_annuel': plafond_per_annuel
    }


def afficher_variables_optimisation():
    """
    Affiche l'interface des variables d'optimisation.
    
    Returns:
        Dictionnaire avec l'état des variables d'optimisation
    """
    st.header("🎯 Variables d'optimisation")
    st.markdown("Configurez les paramètres à optimiser. Cochez pour activer l'optimisation, décochez pour fixer une valeur.")
    
    # Sélection des actifs à utiliser
    st.subheader("📈 Sélection des actifs")
    
    # Options d'actifs disponibles
    actifs_disponibles = {
        'Assurance Vie': {'emoji': '💰', 'nom': 'Assurance Vie'},
        'PER': {'emoji': '🏛️', 'nom': 'PER'},
        'SCPI': {'emoji': '🏢', 'nom': 'SCPI'}
    }
    
    # Multiselect pour choisir les actifs
    actifs_selectionnes = st.multiselect(
        "Choisissez les actifs à inclure dans l'optimisation :",
        options=list(actifs_disponibles.keys()),
        default=['Assurance Vie', 'PER', 'SCPI'],
        format_func=lambda x: f"{actifs_disponibles[x]['emoji']} {actifs_disponibles[x]['nom']}"
    )
    
    if not actifs_selectionnes:
        st.warning("⚠️ Veuillez sélectionner au moins un actif pour l'optimisation.")
        return {}
    
    st.markdown("---")
    
    # CSS pour limiter la largeur du tableau d'optimisation
    st.markdown("""
    <style>
    .optimization-table {
        max-width: 75%;
        margin: 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    variables_info = {}
    
    # Configuration complète des actifs
    tous_actifs_config = {
        'Assurance Vie': {
            'nom': 'Assurance Vie',
            'emoji': '💰',
            'capital_key': 'capital_av',
            'versement_key': 'versement_av',
            'capital_default': True,
            'versement_default': True
        },
        'PER': {
            'nom': 'PER',
            'emoji': '🏛️',
            'capital_key': 'capital_per',
            'versement_key': 'versement_per',
            'capital_default': False,
            'versement_default': True
        },
        'SCPI': {
            'nom': 'SCPI',
            'emoji': '🏢',
            'capital_key': 'capital_scpi',
            'versement_key': 'versement_scpi',
            'capital_default': True,
            'versement_default': False
        }
    }
    
    # Filtrage des actifs selon la sélection
    actifs_config = [tous_actifs_config[actif] for actif in actifs_selectionnes]
    
    # En-têtes du tableau optimisés
    col_actif, col_capital, col_versement = st.columns([0.8, 2.0, 2.0])
    
    with col_actif:
        st.markdown("**Actif**")
    with col_capital:
        st.markdown("**Capital Initial**")
    with col_versement:
        st.markdown("**Versements Mensuels**")
    
    # Affichage pour chaque actif
    for actif in actifs_config:
        col_actif, col_capital, col_versement = st.columns([0.8, 2.0, 2.0])
        
        with col_actif:
                st.markdown(f"**{actif['emoji']} {actif['nom']}**")
        
        with col_capital:
            # Layout horizontal : checkbox + valeur sur la même ligne
            col_check_cap, col_val_cap, col_dummy_cap = st.columns([1, 3, 2])
            
            with col_check_cap:
                activer_capital = st.checkbox(
                    "Opt.",
                    key=f"activer_{actif['capital_key']}",
                    value=st.session_state.optim_activer_vars.get(actif['capital_key'], actif['capital_default'])
                )
            
            with col_val_cap:
                if activer_capital:
                    capital_value = st.session_state.optim_current_values[actif['capital_key']]
                    st.markdown(f"**{capital_value:,.0f} €**")
                else:
                    # Colonne plus étroite pour l'input
                    col_input = st.columns([1, 1])[0]
                    with col_input:
                        capital_value = st.number_input(
                            f"€",
                            min_value=0.0,
                            value=st.session_state.optim_current_values[actif['capital_key']],
                            step=1000.0,
                            key=f"{actif['capital_key']}_fixe",
                            label_visibility="collapsed",
                            format="%.0f"
                        )
                        st.session_state.optim_current_values[actif['capital_key']] = capital_value
            
            variables_info[actif['capital_key']] = {'activer': activer_capital, 'valeur': capital_value}
        
        with col_versement:
            # Layout horizontal : checkbox + valeur sur la même ligne
            col_check_vers, col_val_vers, col_dummy_vers = st.columns([1, 3, 2])
            
            with col_check_vers:
                activer_versement = st.checkbox(
                    "Opt.",
                    key=f"activer_{actif['versement_key']}",
                    value=st.session_state.optim_activer_vars.get(actif['versement_key'], actif['versement_default'])
                )
            
            with col_val_vers:
                if activer_versement:
                    versement_value = st.session_state.optim_current_values[actif['versement_key']]
                    st.markdown(f"**{versement_value:,.0f} €**")
                else:
                    # Colonne plus étroite pour l'input
                    col_input = st.columns([1, 1])[0]
                    with col_input:
                        versement_value = st.number_input(
                            f"€",
                            min_value=0.0,
                            value=st.session_state.optim_current_values[actif['versement_key']],
                            step=50.0,
                            key=f"{actif['versement_key']}_fixe",
                            label_visibility="collapsed",
                            format="%.0f"
                        )
                        st.session_state.optim_current_values[actif['versement_key']] = versement_value
            
            variables_info[actif['versement_key']] = {'activer': activer_versement, 'valeur': versement_value}
    
    # Section crédit SCPI (seulement si SCPI sélectionnée)
    if 'SCPI' in actifs_selectionnes:
        col_label, col_credit, col_empty = st.columns([0.8, 2.0, 2.0])
        
        with col_label:
            st.markdown("**🏦 Crédit SCPI**")
        
        with col_credit:
            # Layout horizontal : checkbox + valeur sur la même ligne
            col_check_credit, col_val_credit = st.columns([1, 3])
            
            with col_check_credit:
                activer_credit_scpi = st.checkbox(
                    "Opt.",
                    key="activer_credit_scpi_montant",
                    value=st.session_state.optim_activer_vars.get('credit_scpi_montant', True)
                )
            
            with col_val_credit:
                if activer_credit_scpi:
                    credit_scpi_montant = st.session_state.optim_current_values['credit_scpi_montant']
                    st.markdown(f"**{credit_scpi_montant:,.0f} €**")
                else:
                    # Colonne plus étroite pour l'input
                    col_input = st.columns([1, 1])[0]
                    with col_input:
                        credit_scpi_montant = st.number_input(
                            "€",
                            min_value=0.0,
                            value=st.session_state.optim_current_values['credit_scpi_montant'],
                            step=5000.0,
                            key="credit_scpi_montant_fixe",
                            label_visibility="collapsed",
                            format="%.0f"
                        )
                        st.session_state.optim_current_values['credit_scpi_montant'] = credit_scpi_montant
        
        variables_info['credit_scpi_montant'] = {'activer': activer_credit_scpi, 'valeur': credit_scpi_montant}
    else:
        # Si SCPI n'est pas sélectionnée, désactiver le crédit SCPI
        variables_info['credit_scpi_montant'] = {'activer': False, 'valeur': 0.0}
    
    return variables_info


def afficher_metriques_principales(resultat_optimisation: Dict[str, Any]):
    """
    Affiche les métriques principales des résultats d'optimisation.
    
    Args:
        resultat_optimisation: Résultats de l'optimisation
    """
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="💰 Solde final optimal",
            value=f"{resultat_optimisation['solde_final_opt']:,.2f} €"
        )
    
    with col2:
        st.metric(
            label="💸 Effort d'épargne maximal",
            value=f"{resultat_optimisation['max_effort_opt']:.2f} €/mois"
        )
    
    with col3:
        statut_color = "🟢" if resultat_optimisation['success'] else "🔴"
        contraintes_color = "🟢" if resultat_optimisation['contraintes_satisfaites'] else "🟠"
        st.write(f"**Statut:** {statut_color} {'Réussi' if resultat_optimisation['success'] else 'Échec'}")
        st.write(f"**Contraintes:** {contraintes_color} {'OK' if resultat_optimisation['contraintes_satisfaites'] else 'Attention'}")


def afficher_messages_contraintes(resultat_optimisation: Dict[str, Any]):
    """
    Affiche les messages de contraintes s'il y en a.
    
    Args:
        resultat_optimisation: Résultats de l'optimisation
    """
    if resultat_optimisation['messages_contraintes']:
        st.warning("⚠️ **Messages de contraintes:**")
        for message in resultat_optimisation['messages_contraintes']:
            st.write(f"• {message}")


def afficher_tableau_resultats_actifs(resultat_optimisation: Dict[str, Any], params: Dict[str, Any]):
    """
    Affiche le tableau des résultats par actif.
    
    Args:
        resultat_optimisation: Résultats de l'optimisation
        params: Paramètres de simulation
    """
    st.subheader("📋 Résumé des résultats par actif")
    
    # Calcul de toutes les données nécessaires
    donnees = calculer_donnees_tableau_actifs(resultat_optimisation, params)
    
    # Création du DataFrame
    df_resultats_actifs = pd.DataFrame({
        'Actif': ['Assurance Vie', 'PER', 'SCPI'],
        'Capital initial (€)': [
            f"{donnees['capital_av']:,.0f}",
            f"{donnees['capital_per']:,.0f}",
            f"{donnees['capital_scpi']:,.0f}"
        ],
        'Versement mensuel (€)': [
            f"{donnees['versement_av']:,.0f}",
            f"{donnees['versement_per']:,.0f}",
            f"{donnees['versement_scpi']:,.0f}"
        ],
        'Mensualité crédit (€)': [
            "0",
            "0",
            f"{donnees['mensualite_credit_scpi']:,.0f}" if donnees['credit_scpi_montant'] > 0 else "0"
        ],
        'Loyer mensuel net (€)': [
            f"{donnees['loyer_av']:,.0f}",
            f"{donnees['loyer_per']:,.0f}",
            f"{donnees['loyer_scpi']:,.0f}"
        ],
        'Impact fiscal mensuel (€)': [
            f"{donnees['impact_fiscal_av']:,.0f}" if donnees['impact_fiscal_av'] == 0 else f"{donnees['impact_fiscal_av']:+,.0f}",
            f"{donnees['impact_fiscal_per']:+,.0f}" if donnees['impact_fiscal_per'] != 0 else "0",
            f"{donnees['impact_fiscal_scpi']:+,.0f}" if donnees['impact_fiscal_scpi'] != 0 else "0"
        ],
        'Effort d\'épargne mensuel (€)': [
            f"{donnees['effort_epargne_av']:,.0f}",
            f"{donnees['effort_epargne_per']:,.0f}",
            f"{donnees['effort_epargne_scpi']:,.0f}"
        ]
    })
    
    st.dataframe(df_resultats_actifs, use_container_width=True)
    
    # Légende
    st.markdown("""
    **💡 Lecture du tableau :**
    - **Mensualité crédit** : Remboursement mensuel du crédit (capital + intérêts + assurance)
    - **Impact fiscal** : Valeur négative (-) = Économie d'impôts | Valeur positive (+) = Impôts à payer | 0 = Neutre
    - **Effort d'épargne** : Flux de trésorerie net mensuel (sortie d'argent réelle)
    """)
    
    return donnees


def afficher_details_complementaires(donnees: Dict[str, Any], params: Dict[str, Any]):
    """
    Affiche les détails complémentaires pour SCPI et PER.
    
    Args:
        donnees: Données calculées par calculer_donnees_tableau_actifs
        params: Paramètres de simulation
    """
    # Détails SCPI à crédit
    if donnees['credit_scpi_montant'] > 0:
        st.write(f"**💡 SCPI à crédit :** {donnees['credit_scpi_montant']:,.0f} € - Mensualité : {donnees['mensualite_credit_scpi']:,.0f} €/mois")
    
    # Détails PER
    if donnees['versement_per'] > 0:
        economie_annuelle_per = donnees['economie_impots_per'] * 12
        st.write(f"**💡 PER :** Économie fiscale {economie_annuelle_per:,.0f} €/an (TMI {params['tmi']*100:.0f}%)")
    
    # Impact fiscal total
    if donnees['impact_fiscal_total'] != 0:
        st.write(f"**📊 Impact fiscal :** {donnees['impact_fiscal_total']:+,.0f} €/mois ({donnees['impact_fiscal_total'] * 12:+,.0f} €/an)")
    else:
        st.write("**📊 Impact fiscal :** neutre")


def afficher_graphique_waterfall(resultat_optimisation: Dict[str, Any]):
    """
    Affiche le graphique waterfall de décomposition de l'effort d'épargne.
    
    Args:
        resultat_optimisation: Résultats de l'optimisation
    """
    st.subheader("📊 Décomposition de l'effort d'épargne mensuel")
    donnees_waterfall = creer_donnees_graphique_waterfall(resultat_optimisation)
    
    fig_waterfall = go.Figure(data=[go.Waterfall(
        x=donnees_waterfall['labels'],
        y=donnees_waterfall['values'],
        text=donnees_waterfall['text'],
        measure=donnees_waterfall['measure'],
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        increasing={"marker": {"color": "lightgreen"}},
        decreasing={"marker": {"color": "lightcoral"}},
        totals={"marker": {"color": "lightblue"}}
    )])
    
    fig_waterfall.update_layout(
        title="Décomposition de l'effort d'épargne mensuel maximal",
        xaxis_title="Composantes",
        yaxis_title="Montant (€)",
        showlegend=False,
        height=500,
        xaxis={'tickangle': -45}
    )
    
    st.plotly_chart(fig_waterfall, use_container_width=True)
    
    # Explication du graphique waterfall
    with st.expander("ℹ️ Comment lire ce graphique", expanded=False):
        st.markdown("""
        **Le graphique waterfall montre comment se compose l'effort d'épargne mensuel :**
        
        - 🔴 **Barres rouges (négatives)** : Sorties de trésorerie
          - Versements mensuels (AV, PER, SCPI)
          - Impôts sur les revenus SCPI  
          - Mensualité du crédit SCPI
          
        - 🟢 **Barres vertes (positives)** : Entrées de trésorerie
          - Économies d'impôt grâce au PER
          - Revenus bruts des SCPI
          
        - 🔵 **Barre bleue finale** : Effort d'épargne net total
        
        L'objectif de l'optimisation est de maximiser le patrimoine final tout en respectant 
        la contrainte d'effort d'épargne mensuel que vous avez fixée.
        """)


def afficher_detail_complet_parametres(resultat_optimisation: Dict[str, Any]):
    """
    Affiche le détail complet des paramètres optimaux dans un expander.
    
    Args:
        resultat_optimisation: Résultats de l'optimisation
    """
    with st.expander("📊 Détail complet des paramètres optimaux", expanded=False):
        resultats_formates = formater_resultat_optimisation(resultat_optimisation)
        df_resultats_complet = pd.DataFrame([
            {"Paramètre": k, "Valeur optimale": v} 
            for k, v in resultats_formates.items()
        ])
        st.dataframe(df_resultats_complet, use_container_width=True)


def afficher_simulation_detaillee(resultat_optimisation: Dict[str, Any]):
    """
    Affiche les résultats détaillés de la simulation pour les paramètres optimaux.
    
    Args:
        resultat_optimisation: Résultats de l'optimisation contenant les paramètres optimaux
    """
    if 'x' not in resultat_optimisation:
        st.error("❌ Aucun résultat d'optimisation disponible")
        return
    
    with st.expander("📈 Simulation détaillée avec paramètres optimaux", expanded=False):
        # Import de la fonction de simulation
        from core.optim_simulation_financiere import calculer_simulation_mensuelle
        
        # Récupération des paramètres optimaux
        x_optimal = resultat_optimisation['x']
        
        # Construction des paramètres pour la simulation
        capital_av = x_optimal[0] if len(x_optimal) > 0 else 0
        capital_per = x_optimal[1] if len(x_optimal) > 1 else 0
        capital_scpi = x_optimal[2] if len(x_optimal) > 2 else 0
        versement_av = x_optimal[3] if len(x_optimal) > 3 else 0
        versement_per = x_optimal[4] if len(x_optimal) > 4 else 0
        versement_scpi = x_optimal[5] if len(x_optimal) > 5 else 0
        credit_scpi_montant = x_optimal[6] if len(x_optimal) > 6 else 0
        
        # Paramètres du session state
        params = st.session_state.optim_params
        
        try:
            # Exécution de la simulation
            resultats_simulation = calculer_simulation_mensuelle(
                capital_av=capital_av,
                capital_per=capital_per,
                capital_scpi=capital_scpi,
                versement_av=versement_av,
                versement_per=versement_per,
                versement_scpi=versement_scpi,
                taux_av=params.get('taux_av', 0.04),
                taux_per=params.get('taux_per', 0.05),
                taux_distribution_scpi=params.get('taux_distribution_scpi', 0.045),
                taux_appreciation_scpi=params.get('taux_appreciation_scpi', 0.02),
                frais_entree_av=params.get('frais_entree_av', 0.03),
                frais_entree_per=params.get('frais_entree_per', 0.025),
                frais_entree_scpi=params.get('frais_entree_scpi', 0.10),
                tmi=params.get('tmi', 0.30),
                plafond_per_annuel=params.get('plafond_per_annuel', 35000),
                duree_annees=params.get('duree_annees', 20),
                credit_scpi_montant=credit_scpi_montant,
                credit_scpi_duree=params.get('credit_scpi_duree', 15),
                credit_scpi_taux=params.get('credit_scpi_taux', 0.035),
                credit_scpi_assurance=params.get('credit_scpi_assurance', 0.003),
                scpi_europeenne_ratio=params.get('scpi_europeenne_ratio', 0.0)
            )
            
            # Conversion en DataFrame
            df_simulation = pd.DataFrame(resultats_simulation)
            
            # Formatage des colonnes monétaires
            colonnes_monetaires = [
                'versement_av', 'versement_per', 'versement_scpi',
                'solde_av', 'solde_per', 'solde_scpi', 'solde_total',
                'revenus_av', 'revenus_per', 'revenus_scpi',
                'economie_impots_per', 'fiscalite_payee',
                'mensualite_credit_scpi', 'capital_restant_du'
            ]
            
            # Information sur la simulation
            st.markdown("### 📊 Informations générales")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Durée", f"{len(df_simulation)} mois")
            with col2:
                st.metric("Solde final total", f"{df_simulation['solde_total'].iloc[-1]:,.0f} €")
            with col3:
                effort_total = df_simulation['effort_epargne'].sum()
                st.metric("Effort total", f"{effort_total:,.0f} €")
            with col4:
                performance = df_simulation['solde_total'].iloc[-1] / effort_total if effort_total > 0 else 0
                st.metric("Multiple", f"{performance:.2f}x")
            
            # Choix de l'affichage
            mode_affichage = st.radio(
                "Mode d'affichage :",
                ["📅 Données mensuelles", "🗓️ Données annuelles", "🎯 Résumé final"],
                horizontal=True
            )
            
            if mode_affichage == "📅 Données mensuelles":
                # Affichage mensuel complet
                st.markdown("### 📅 Évolution mensuelle complète")
                
                # Formatage du DataFrame pour l'affichage
                df_affichage = df_simulation.copy()
                
                # Formatage des colonnes monétaires
                for col in colonnes_monetaires:
                    if col in df_affichage.columns:
                        df_affichage[col] = df_affichage[col].apply(lambda x: f"{x:,.0f} €")
                
                # Renommage des colonnes pour un affichage plus clair
                colonnes_renommees = {
                    'mois': 'Mois',
                    'versement_av': 'Versement AV',
                    'versement_per': 'Versement PER',
                    'versement_scpi': 'Versement SCPI',
                    'solde_av': 'Solde AV',
                    'solde_per': 'Solde PER',
                    'solde_scpi': 'Solde SCPI',
                    'solde_total': 'Solde Total',
                    'effort_epargne': 'Effort Épargne',
                    'economie_impots_per': 'Économie Impôts PER',
                    'fiscalite_payee': 'Fiscalité Payée',
                    'mensualite_credit_scpi': 'Mensualité Crédit',
                    'capital_restant_du': 'Capital Restant Dû'
                }
                
                df_affichage = df_affichage.rename(columns=colonnes_renommees)
                
                st.dataframe(df_affichage, use_container_width=True, height=400)
                
            elif mode_affichage == "🗓️ Données annuelles":
                # Agrégation annuelle
                st.markdown("### 🗓️ Évolution annuelle")
                
                # Création du DataFrame annuel
                df_simulation['annee'] = ((df_simulation['mois'] - 1) // 12) + 1
                
                df_annuel = df_simulation.groupby('annee').agg({
                    'versement_av': 'sum',
                    'versement_per': 'sum', 
                    'versement_scpi': 'sum',
                    'solde_av': 'last',
                    'solde_per': 'last',
                    'solde_scpi': 'last',
                    'solde_total': 'last',
                    'effort_epargne': 'sum',
                    'economie_impots_per': 'sum',
                    'fiscalite_payee': 'sum'
                }).reset_index()
                
                # Formatage pour l'affichage
                df_annuel_affichage = df_annuel.copy()
                for col in ['versement_av', 'versement_per', 'versement_scpi', 'solde_av', 
                           'solde_per', 'solde_scpi', 'solde_total', 'effort_epargne',
                           'economie_impots_per', 'fiscalite_payee']:
                    if col in df_annuel_affichage.columns:
                        df_annuel_affichage[col] = df_annuel_affichage[col].apply(lambda x: f"{x:,.0f} €")
                
                # Renommage des colonnes
                colonnes_renommees_annuel = {
                    'annee': 'Année',
                    'versement_av': 'Versements AV',
                    'versement_per': 'Versements PER',
                    'versement_scpi': 'Versements SCPI',
                    'solde_av': 'Solde AV fin',
                    'solde_per': 'Solde PER fin',
                    'solde_scpi': 'Solde SCPI fin',
                    'solde_total': 'Solde Total fin',
                    'effort_epargne': 'Effort Annuel',
                    'economie_impots_per': 'Économie Impôts',
                    'fiscalite_payee': 'Fiscalité Payée'
                }
                
                df_annuel_affichage = df_annuel_affichage.rename(columns=colonnes_renommees_annuel)
                
                st.dataframe(df_annuel_affichage, use_container_width=True)
                
            else:  # Résumé final
                st.markdown("### 🎯 Résumé des résultats finaux")
                
                # Calculs de synthèse
                solde_final_av = df_simulation['solde_av'].iloc[-1]
                solde_final_per = df_simulation['solde_per'].iloc[-1]
                solde_final_scpi = df_simulation['solde_scpi'].iloc[-1]
                solde_final_total = df_simulation['solde_total'].iloc[-1]
                
                effort_total = df_simulation['effort_epargne'].sum()
                economie_impots_total = df_simulation['economie_impots_per'].sum()
                fiscalite_total = df_simulation['fiscalite_payee'].sum()
                
                # Affichage en colonnes
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**💰 Soldes finaux :**")
                    st.write(f"• Assurance Vie : {solde_final_av:,.0f} €")
                    st.write(f"• PER : {solde_final_per:,.0f} €")
                    st.write(f"• SCPI : {solde_final_scpi:,.0f} €")
                    st.write(f"• **Total : {solde_final_total:,.0f} €**")
                
                with col2:
                    st.markdown("**📊 Synthèse financière :**")
                    st.write(f"• Effort d'épargne total : {effort_total:,.0f} €")
                    st.write(f"• Économie d'impôts PER : {economie_impots_total:,.0f} €")
                    st.write(f"• Fiscalité payée : {fiscalite_total:,.0f} €")
                    gain_net = solde_final_total - effort_total
                    st.write(f"• **Gain net : {gain_net:,.0f} €**")
        
        except Exception as e:
            st.error(f"❌ Erreur lors de la simulation : {str(e)}")


def afficher_parametres_avances():
    """
    Affiche l'interface des paramètres avancés de simulation.
    
    Returns:
        Dict: Paramètres mis à jour
    """
    with st.expander("⚙️ Paramètres avancés de simulation", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📅 Durées")
            duree_annees = st.number_input(
                "Durée de simulation (années)",
                min_value=1.0,
                max_value=50.0,
                value=st.session_state.optim_params.get('duree_annees', 20.0),
                step=1.0
            )
            
            credit_scpi_duree = st.number_input(
                "Durée crédit SCPI (années)",
                min_value=1.0,
                max_value=30.0,
                value=st.session_state.optim_params.get('credit_scpi_duree', 15.0),
                step=1.0
            )
            
            st.subheader("📈 Taux de rendement (%)")
            taux_av = st.number_input(
                "Taux AV annuel",
                min_value=0.0,
                max_value=20.0,
                value=st.session_state.optim_params.get('taux_av', 0.04) * 100,
                step=0.1,
                format="%.2f"
            ) / 100
            
            taux_per = st.number_input(
                "Taux PER annuel",
                min_value=0.0,
                max_value=20.0,
                value=st.session_state.optim_params.get('taux_per', 0.05) * 100,
                step=0.1,
                format="%.2f"
            ) / 100
            
            taux_distribution_scpi = st.number_input(
                "Taux distribution SCPI annuel",
                min_value=0.0,
                max_value=15.0,
                value=st.session_state.optim_params.get('taux_distribution_scpi', 0.045) * 100,
                step=0.1,
                format="%.2f"
            ) / 100
            
            taux_appreciation_scpi = st.number_input(
                "Taux appréciation SCPI annuel",
                min_value=0.0,
                max_value=10.0,
                value=st.session_state.optim_params.get('taux_appreciation_scpi', 0.02) * 100,
                step=0.1,
                format="%.2f"
            ) / 100
        
        with col2:
            st.subheader("💰 Frais d'entrée (%)")
            frais_entree_av = st.number_input(
                "Frais d'entrée AV",
                min_value=0.0,
                max_value=10.0,
                value=st.session_state.optim_params.get('frais_entree_av', 0.03) * 100,
                step=0.1,
                format="%.2f"
            ) / 100
            
            frais_entree_per = st.number_input(
                "Frais d'entrée PER",
                min_value=0.0,
                max_value=10.0,
                value=st.session_state.optim_params.get('frais_entree_per', 0.025) * 100,
                step=0.1,
                format="%.2f"
            ) / 100
            
            frais_entree_scpi = st.number_input(
                "Frais d'entrée SCPI",
                min_value=0.0,
                max_value=20.0,
                value=st.session_state.optim_params.get('frais_entree_scpi', 0.10) * 100,
                step=0.1,
                format="%.2f"
            ) / 100
            
            st.subheader("🏦 Crédit SCPI (%)")
            credit_scpi_taux = st.number_input(
                "Taux crédit SCPI annuel",
                min_value=0.0,
                max_value=10.0,
                value=st.session_state.optim_params.get('credit_scpi_taux', 0.035) * 100,
                step=0.1,
                format="%.2f"
            ) / 100
            
            credit_scpi_assurance = st.number_input(
                "Assurance crédit SCPI annuelle",
                min_value=0.0,
                max_value=2.0,
                value=st.session_state.optim_params.get('credit_scpi_assurance', 0.003) * 100,
                step=0.1,
                format="%.2f"
            ) / 100
            
            st.subheader("📊 Fiscalité (%)")
            tmi = st.number_input(
                "Tranche marginale d'imposition",
                min_value=0.0,
                max_value=50.0,
                value=st.session_state.optim_params.get('tmi', 0.30) * 100,
                step=1.0,
                format="%.1f"
            ) / 100
            
            plafond_per_annuel = st.number_input(
                "Plafond PER annuel (€)",
                min_value=0.0,
                max_value=100000.0,
                value=st.session_state.optim_params.get('plafond_per_annuel', 35000.0),
                step=1000.0
            )
            
            scpi_europeenne_ratio = st.number_input(
                "Ratio SCPI européennes (sans PS)",
                min_value=0.0,
                max_value=100.0,
                value=st.session_state.optim_params.get('scpi_europeenne_ratio', 0.0) * 100,
                step=5.0,
                format="%.1f"
            ) / 100
        
        # Mise à jour des paramètres dans le session state
        parametres_mis_a_jour = {
            'duree_annees': duree_annees,
            'credit_scpi_duree': credit_scpi_duree,
            'taux_av': taux_av,
            'taux_per': taux_per,
            'taux_distribution_scpi': taux_distribution_scpi,
            'taux_appreciation_scpi': taux_appreciation_scpi,
            'frais_entree_av': frais_entree_av,
            'frais_entree_per': frais_entree_per,
            'frais_entree_scpi': frais_entree_scpi,
            'credit_scpi_taux': credit_scpi_taux,
            'credit_scpi_assurance': credit_scpi_assurance,
            'tmi': tmi,
            'plafond_per_annuel': plafond_per_annuel,
            'scpi_europeenne_ratio': scpi_europeenne_ratio
        }
        
        st.session_state.optim_params.update(parametres_mis_a_jour)
        
        return parametres_mis_a_jour