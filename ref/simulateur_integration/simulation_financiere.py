"""
Module de simulation financière pour l'optimisation d'investissements
Contient les fonctions de base pour l'interface Streamlit

Fonctions disponibles :
- calculer_simulation_mensuelle : Simulation complète des investissements
- calculer_effort_epargne_mensuel : Calcul de l'effort d'épargne
- simulation_resume : Version résumée de la simulation
- maximiser_solde_final_avec_contrainte : Fonction d'optimisation
- Fonctions utilitaires diverses
"""

import pandas as pd
import numpy as np
from scipy.optimize import minimize


# ===== FONCTIONS DE CONVERSION =====

def convertir_pourcentage_vers_decimal(pourcentage_input):
    """Convertit un pourcentage saisi (ex: 30) en décimal (ex: 0.30)"""
    return pourcentage_input / 100


def convertir_annees_vers_mois(annees):
    """Convertit des années en mois"""
    return int(annees * 12)


def formater_decimal_vers_pourcentage(decimal):
    """Formate un décimal en pourcentage pour l'affichage"""
    return decimal * 100


# ===== FONCTION PRINCIPALE DE SIMULATION =====

def calculer_simulation_mensuelle(
    capital_av, capital_per, capital_scpi, versement_av, versement_per, versement_scpi,
    taux_av, taux_per, taux_distribution_scpi, taux_appreciation_scpi, frais_entree_av, frais_entree_per, frais_entree_scpi,
    tmi, plafond_per_annuel, duree_annees, 
    credit_scpi_montant=0, credit_scpi_duree=0, credit_scpi_taux=0, credit_scpi_assurance=0,
    scpi_europeenne_ratio=0.0
):
    """
    Calcule la simulation d'investissement sur assurance-vie, PER et SCPI
    Renvoie les valeurs mensuelles (non cumulées) pour chaque mois.
    Ajoute en sortie l'économie d'impôts du PER.
    Ajoute en sortie la fiscalité payée sur le mois (impots - réduction).
    Ajoute en sortie les soldes des supports (AV, PER, SCPI).
    Ajoute en sortie le CRD du prêt SCPI (capital restant dû).
    scpi_europeenne_ratio : proportion du capital SCPI investi en SCPI européennes (sans prélèvements sociaux)
    """
    duree_mois = int(duree_annees * 12)
    mensualite_credit_scpi = 0
    capital_scpi_total_initial = capital_scpi

    if credit_scpi_montant > 0 and credit_scpi_duree > 0:
        taux_mensuel_credit = (credit_scpi_taux + credit_scpi_assurance) / 12
        nb_mois_credit = convertir_annees_vers_mois(credit_scpi_duree)
        if taux_mensuel_credit > 0:
            mensualite_credit_scpi = credit_scpi_montant * (taux_mensuel_credit * (1 + taux_mensuel_credit)**nb_mois_credit) / ((1 + taux_mensuel_credit)**nb_mois_credit - 1)
        else:
            mensualite_credit_scpi = credit_scpi_montant / nb_mois_credit
        capital_scpi_total_initial = capital_scpi + credit_scpi_montant

    solde_av = capital_av * (1 - frais_entree_av)
    solde_per = capital_per * (1 - frais_entree_per)
    solde_scpi = capital_scpi_total_initial * (1 - frais_entree_scpi)

    capital_restant_credit_scpi = credit_scpi_montant
    mois_restants_credit = convertir_annees_vers_mois(credit_scpi_duree) if credit_scpi_duree > 0 else 0

    taux_mensuel_av = (1 + taux_av) ** (1/12) - 1
    taux_mensuel_per = (1 + taux_per) ** (1/12) - 1
    taux_mensuel_distribution_scpi = (1 + taux_distribution_scpi) ** (1/12) - 1
    taux_mensuel_appreciation_scpi = (1 + taux_appreciation_scpi) ** (1/12) - 1

    mois = []
    versement_av_mensuel = []
    versement_per_mensuel = []
    versement_scpi_mensuel = []
    economie_impot_per_mensuelle = []
    interets_credit_scpi_mensuel = []
    mensualite_credit_scpi_mensuel = []
    revenu_scpi_brut_mensuel = []
    impot_scpi_mensuel = []
    fiscalite_payee_mensuelle = []
    solde_av_mensuel = []
    solde_per_mensuel = []
    solde_scpi_mensuel = []
    crd_pret_scpi_mensuel = []  # Ajout du CRD du prêt

    versements_per_annee_courante = capital_per
    annee_courante = 0

    # Nouveau : capital brut SCPI pour calcul des revenus (sans enlever les frais d'entrée)
    capital_scpi_brut = capital_scpi_total_initial

    for mois_i in range(duree_mois):
        interets_credit_scpi_mois = 0
        mensualite_credit_mois = 0

        if mois_restants_credit > 0 and capital_restant_credit_scpi > 0:
            taux_mensuel_credit_seul = credit_scpi_taux / 12
            interets_credit_scpi_mois = capital_restant_credit_scpi * taux_mensuel_credit_seul
            capital_rembourse_mois = mensualite_credit_scpi - interets_credit_scpi_mois - (credit_scpi_montant * credit_scpi_assurance / 12)
            capital_restant_credit_scpi = max(0, capital_restant_credit_scpi - capital_rembourse_mois)
            mois_restants_credit -= 1
            mensualite_credit_mois = mensualite_credit_scpi

        revenus_scpi_bruts_mensuels = 0
        impot_scpi_mois = 0
        # Utiliser le capital brut pour le calcul des revenus (sans enlever les frais d'entrée)
        if capital_scpi_brut > 0:
            revenus_scpi_bruts_mensuels = capital_scpi_brut * taux_mensuel_distribution_scpi
            base_imposable_scpi = max(0, revenus_scpi_bruts_mensuels - interets_credit_scpi_mois)
            # Calcul du taux d'imposition SCPI en tenant compte du ratio européen
            taux_imposition_scpi = tmi + (1 - scpi_europeenne_ratio) * 0.172
            impot_scpi_mois = base_imposable_scpi * taux_imposition_scpi

        economie_impot_per_mois = 0
        nouvelle_annee = (mois_i > 0 and mois_i % 12 == 0)
        if nouvelle_annee:
            annee_courante += 1
            versements_per_annee_courante = 0

        versement_av_net = 0
        versement_scpi_net = 0
        versement_per_net = 0

        if mois_i < duree_mois:
            if versement_av > 0:
                versement_av_net = versement_av * (1 - frais_entree_av)
                solde_av += versement_av_net
            if versement_scpi > 0:
                versement_scpi_net = versement_scpi# * (1 - frais_entree_scpi) on ne paye les frais d'entrée des SCPI qu'à la revente
                solde_scpi += versement_scpi_net
                # Ajouter le versement brut au capital brut SCPI (sans enlever les frais d'entrée)
                capital_scpi_brut += versement_scpi
            if versement_per > 0:
                versement_per_net = versement_per * (1 - frais_entree_per)
                solde_per += versement_per_net
                versements_per_annee_courante += versement_per
                versement_deductible = min(versement_per, max(0, plafond_per_annuel - (versements_per_annee_courante - versement_per)))
                economie_impot_per_mois = versement_deductible * tmi

            solde_av *= (1 + taux_mensuel_av)
            solde_per *= (1 + taux_mensuel_per)
            solde_scpi *= (1 + taux_mensuel_appreciation_scpi)
            # Appréciation du capital brut SCPI (sans enlever les frais d'entrée)
            #capital_scpi_brut *= (1 + taux_mensuel_appreciation_scpi)

        fiscalite_payee = impot_scpi_mois - economie_impot_per_mois

        mois.append(mois_i + 1)  # Mois de 1 à 180 au lieu de 0 à 179
        versement_av_mensuel.append(versement_av)
        versement_per_mensuel.append(versement_per)
        versement_scpi_mensuel.append(versement_scpi)
        economie_impot_per_mensuelle.append(economie_impot_per_mois)
        interets_credit_scpi_mensuel.append(interets_credit_scpi_mois)
        mensualite_credit_scpi_mensuel.append(mensualite_credit_mois)
        revenu_scpi_brut_mensuel.append(revenus_scpi_bruts_mensuels)
        impot_scpi_mensuel.append(impot_scpi_mois)
        fiscalite_payee_mensuelle.append(fiscalite_payee)
        solde_av_mensuel.append(solde_av)
        solde_per_mensuel.append(solde_per)
        solde_scpi_mensuel.append(solde_scpi)
        crd_pret_scpi_mensuel.append(capital_restant_credit_scpi)  # Ajout du CRD à chaque mois

    return {
        'mois': mois,
        'versement_av_mensuel': versement_av_mensuel,
        'versement_per_mensuel': versement_per_mensuel,
        'versement_scpi_mensuel': versement_scpi_mensuel,
        'economie_impot_per_mensuelle': economie_impot_per_mensuelle,
        'interets_credit_scpi_mensuel': interets_credit_scpi_mensuel,
        'mensualite_credit_scpi_mensuel': mensualite_credit_scpi_mensuel,
        'revenu_scpi_brut_mensuel': revenu_scpi_brut_mensuel,
        'impot_scpi_mensuel': impot_scpi_mensuel,
        'fiscalite_payee_mensuelle': fiscalite_payee_mensuelle,
        'solde_av_mensuel': solde_av_mensuel,
        'solde_per_mensuel': solde_per_mensuel,
        'solde_scpi_mensuel': solde_scpi_mensuel,
        'crd_pret_scpi_mensuel': crd_pret_scpi_mensuel  # Ajout en sortie
    }


# ===== FONCTIONS D'ANALYSE =====

def calculer_effort_epargne_mensuel(df):
    """
    Calcule l'effort d'épargne mensuel à partir du DataFrame df_res.
    Renvoie un DataFrame avec les colonnes 'mois' et 'effort_epargne_mensuel'.
    """
    effort = (
        df['versement_per_mensuel']
        + df['versement_av_mensuel']
        + df['versement_scpi_mensuel']
        - df['economie_impot_per_mensuelle']
        + df['impot_scpi_mensuel']
        + df['mensualite_credit_scpi_mensuel']
        - df['revenu_scpi_brut_mensuel']
    )
    return pd.DataFrame({'mois': df['mois'], 'effort_epargne_mensuel': effort})


def somme_colonnes_solde_par_mois(df):
    """Renvoie un DataFrame avec la somme des colonnes 'solde' pour chaque mois."""
    solde_cols = [col for col in df.columns if col.startswith('solde')]
    return pd.DataFrame({'mois': df['mois'], 'somme_solde': df[solde_cols].sum(axis=1)})


def get_somme_solde_pour_mois(df_somme, mois):
    """
    Renvoie la valeur de 'somme_solde' pour un mois donné dans le DataFrame df_somme.
    """
    row = df_somme[df_somme['mois'] == mois]
    if not row.empty:
        return row.iloc[0]['somme_solde']
    else:
        return None


def extraire_max_colonne(df, colonne):
    """
    Extrait la valeur maximale d'une colonne d'un DataFrame.
    """
    return df[colonne].max()


# ===== FONCTION DE SIMULATION RÉSUMÉE =====

def simulation_resume(
    capital_av, capital_per, capital_scpi,
    versement_av, versement_per, versement_scpi,
    credit_scpi_montant,
    params
):
    """
    Exécute la simulation et retourne :
    - le solde total au dernier mois (CRD soustrait)
    - le maximum de l'effort d'épargne mensuel

    params : dict contenant les autres paramètres nécessaires
    """
    res = calculer_simulation_mensuelle(
        capital_av, capital_per, capital_scpi,
        versement_av, versement_per, versement_scpi,
        params['taux_av'], params['taux_per'], params['taux_distribution_scpi'], params['taux_appreciation_scpi'],
        params['frais_entree_av'], params['frais_entree_per'], params['frais_entree_scpi'],
        params['tmi'], params['plafond_per_annuel'], params['duree_annees'],
        credit_scpi_montant, params['credit_scpi_duree'], params['credit_scpi_taux'], params['credit_scpi_assurance'],
        params.get('scpi_europeenne_ratio', 0.0)
    )
    df_res = pd.DataFrame.from_dict(res)
    df_somme = somme_colonnes_solde_par_mois(df_res)
    mois_final = int(params['duree_annees'] * 12)  # Dernier mois disponible (maintenant 180)
    solde_final = get_somme_solde_pour_mois(df_somme, mois_final)
    crd_final = df_res.loc[df_res['mois'] == mois_final, 'crd_pret_scpi_mensuel'].values[0]
    solde_final_net = solde_final - crd_final
    effort_epargne_mensuel = calculer_effort_epargne_mensuel(df_res)
    df_res = df_res.merge(effort_epargne_mensuel, on='mois')
    max_effort = extraire_max_colonne(effort_epargne_mensuel, 'effort_epargne_mensuel')
    return solde_final_net, max_effort, df_res, effort_epargne_mensuel


# ===== FONCTION D'OPTIMISATION =====

def maximiser_solde_final_avec_contrainte(
    params,
    effort_max,
    activer_vars=None,
    mensualite_max=1000,
    capital_initial_max=10000000,
    valeurs_defaut=None
):
    """
    Optimise le solde final sous contrainte d'effort d'épargne, de mensualité et de capital initial.
    activer_vars : liste de booléens (longueur 7) pour activer/désactiver chaque variable d'optimisation :
        [capital_av, capital_per, capital_scpi, versement_av, versement_per, versement_scpi, credit_scpi_montant]
    valeurs_defaut : liste de valeurs à utiliser si la variable n'est pas activée
    """
    if activer_vars is None:
        activer_vars = [True] * 7

    if valeurs_defaut is None:
        valeurs_defaut = [
            params.get('capital_av', 0.0),
            params.get('capital_per', 0.0),
            params.get('capital_scpi', 0.0),
            params.get('versement_av', 0.0),
            params.get('versement_per', 0.0),
            params.get('versement_scpi', 0.0),
            params.get('credit_scpi_montant', 0.0)
        ]

    # Définir les bornes selon activation
    bounds = []
    x0 = []
    for i, active in enumerate(activer_vars):
        if active:
            if i == 3 or i == 5:  # versement_av ou versement_scpi
                bounds.append((0, 10000))
            elif i == 4:  # versement_per
                bounds.append((0, params['plafond_per_annuel']/12))
            elif i == 6:  # credit_scpi_montant
                bounds.append((0, 1E7))
            else:
                bounds.append((0, capital_initial_max))
            x0.append(0)
        else:
            bounds.append((valeurs_defaut[i], valeurs_defaut[i]))
            x0.append(valeurs_defaut[i])

    def objectif(x):
        x_full = [x[i] if activer_vars[i] else valeurs_defaut[i] for i in range(7)]
        capital_av_test, capital_per_test, capital_scpi_test, versement_av_test, versement_per_test, versement_scpi_test, credit_scpi_montant_test = x_full
        solde_final, _, _, _ = simulation_resume(
            capital_av_test, capital_per_test, capital_scpi_test,
            versement_av_test, versement_per_test, versement_scpi_test,
            credit_scpi_montant_test,
            params
        )
        return -solde_final

    def contrainte_effort(x):
        x_full = [x[i] if activer_vars[i] else valeurs_defaut[i] for i in range(7)]
        capital_av_test, capital_per_test, capital_scpi_test, versement_av_test, versement_per_test, versement_scpi_test, credit_scpi_montant_test = x_full
        _, max_effort, _, _ = simulation_resume(
            capital_av_test, capital_per_test, capital_scpi_test,
            versement_av_test, versement_per_test, versement_scpi_test,
            credit_scpi_montant_test,
            params
        )
        return effort_max - max_effort

    def contrainte_mensualite(x):
        x_full = [x[i] if activer_vars[i] else valeurs_defaut[i] for i in range(7)]
        capital_av_test, capital_per_test, capital_scpi_test, versement_av_test, versement_per_test, versement_scpi_test, credit_scpi_montant_test = x_full
        _, _, df_res_local, _ = simulation_resume(
            capital_av_test, capital_per_test, capital_scpi_test,
            versement_av_test, versement_per_test, versement_scpi_test,
            credit_scpi_montant_test,
            params
        )
        mensualite = df_res_local['mensualite_credit_scpi_mensuel'].max()
        return mensualite_max - mensualite

    def contrainte_capital_initial(x):
        x_full = [x[i] if activer_vars[i] else valeurs_defaut[i] for i in range(7)]
        capital_av_test, capital_per_test, capital_scpi_test, _, _, _, _ = x_full
        total = capital_av_test + capital_per_test + capital_scpi_test
        return capital_initial_max - total

    constraints = [
        {'type': 'ineq', 'fun': contrainte_effort},
        {'type': 'ineq', 'fun': contrainte_mensualite},
        {'type': 'ineq', 'fun': contrainte_capital_initial}
    ]

    res_opt = minimize(objectif, x0, bounds=bounds, constraints=constraints, method='SLSQP')
    
    x_opt = [res_opt.x[i] if activer_vars[i] else valeurs_defaut[i] for i in range(7)]
    x_opt = [res_opt.x[i] for i in range(7)]

    capital_av_opt, capital_per_opt, capital_scpi_opt, versement_av_opt, versement_per_opt, versement_scpi_opt, credit_scpi_montant_opt = x_opt
    solde_final_opt, max_effort_opt, df_res_optimal, _ = simulation_resume(
        capital_av_opt, capital_per_opt, capital_scpi_opt,
        versement_av_opt, versement_per_opt, versement_scpi_opt,
        credit_scpi_montant_opt,
        params
    )
    
    # Vérification des contraintes après optimisation
    contraintes_satisfaites = True
    messages_contraintes = []
    
    # Effort d'épargne mensuel maximal
    if max_effort_opt > effort_max and not np.isclose(max_effort_opt, effort_max, rtol=1e-4, atol=1e-2):
        messages_contraintes.append(f"Attention : contrainte d'effort d'épargne non respectée ({max_effort_opt:.2f} > {effort_max})")
        contraintes_satisfaites = False
    
    # Mensualité crédit SCPI maximale
    mensualite_opt = df_res_optimal['mensualite_credit_scpi_mensuel'].max()
    if mensualite_opt > mensualite_max and not np.isclose(mensualite_opt, mensualite_max, rtol=1e-4, atol=1e-2):
        messages_contraintes.append(f"Attention : contrainte de mensualité crédit SCPI non respectée ({mensualite_opt:.2f} > {mensualite_max})")
        contraintes_satisfaites = False
    
    # Capital initial maximal
    capital_initial_opt = capital_av_opt + capital_per_opt + capital_scpi_opt
    if capital_initial_opt > capital_initial_max and not np.isclose(capital_initial_opt, capital_initial_max, rtol=1e-4, atol=1e-2):
        messages_contraintes.append(f"Attention : contrainte de capital initial non respectée ({capital_initial_opt:.2f} > {capital_initial_max})")
        contraintes_satisfaites = False
    
    return {
        'capital_av_opt': capital_av_opt,
        'capital_per_opt': capital_per_opt,
        'capital_scpi_opt': capital_scpi_opt,
        'versement_av_opt': versement_av_opt,
        'versement_per_opt': versement_per_opt,
        'versement_scpi_opt': versement_scpi_opt,
        'credit_scpi_montant_opt': credit_scpi_montant_opt,
        'solde_final_opt': solde_final_opt,
        'max_effort_opt': max_effort_opt,
        'success': res_opt.success,
        'contraintes_satisfaites': contraintes_satisfaites,
        'messages_contraintes': messages_contraintes,
        'df_res_optimal': df_res_optimal
    }


# ===== FONCTIONS UTILITAIRES POUR STREAMLIT =====

def creer_parametres_defaut():
    """
    Crée un dictionnaire avec les paramètres par défaut pour la simulation.
    """
    return {
        'taux_av': 0.04,
        'taux_per': 0.045,
        'taux_distribution_scpi': 0.05,
        'taux_appreciation_scpi': 0.0075,
        'frais_entree_av': 0.048,
        'frais_entree_per': 0.045,
        'frais_entree_scpi': 0.10,
        'tmi': 0.30,
        'plafond_per_annuel': 4500.0,
        'duree_annees': 15.0,
        'credit_scpi_duree': 15.0,
        'credit_scpi_taux': 0.04,
        'credit_scpi_assurance': 0.003,
        'scpi_europeenne_ratio': 0.50
    }


def formater_resultat_optimisation(resultat):
    """
    Formate les résultats de l'optimisation pour l'affichage dans Streamlit.
    """
    return {
        'Capital AV optimal': f"{resultat['capital_av_opt']:,.2f} €",
        'Capital PER optimal': f"{resultat['capital_per_opt']:,.2f} €",
        'Capital SCPI optimal': f"{resultat['capital_scpi_opt']:,.2f} €",
        'Versement AV optimal': f"{resultat['versement_av_opt']:,.2f} €/mois",
        'Versement PER optimal': f"{resultat['versement_per_opt']:,.2f} €/mois",
        'Versement SCPI optimal': f"{resultat['versement_scpi_opt']:,.2f} €/mois",
        'Montant crédit SCPI optimal': f"{resultat['credit_scpi_montant_opt']:,.2f} €",
        'Solde final optimal': f"{resultat['solde_final_opt']:,.2f} €",
        'Effort d\'épargne mensuel maximal': f"{resultat['max_effort_opt']:,.2f} €"
    }


def creer_donnees_graphique_waterfall(resultat_optimisation):
    """
    Crée les données pour le graphique waterfall de décomposition de l'effort d'épargne.
    """
    df_res_optimal = resultat_optimisation['df_res_optimal']
    
    waterfall_labels = [
        "Versement PER",
        "Versement AV", 
        "Versement SCPI",
        "Économie impôt PER",
        "Impôt SCPI",
        "Mensualité crédit SCPI",
        "Revenu SCPI brut",
        "Effort max autorisé"
    ]
    
    waterfall_values = [
        -float(resultat_optimisation['versement_per_opt']),
        -float(resultat_optimisation['versement_av_opt']),
        -float(resultat_optimisation['versement_scpi_opt']),
        float(df_res_optimal.loc[0, "economie_impot_per_mensuelle"]),
        -float(df_res_optimal.loc[0, "impot_scpi_mensuel"]),
        -float(df_res_optimal.loc[0, "mensualite_credit_scpi_mensuel"]),
        float(df_res_optimal.loc[0, "revenu_scpi_brut_mensuel"])
    ]
    
    waterfall_values.append(np.sum(waterfall_values))
    
    waterfall_text = [f"{v:.2f} €" for v in waterfall_values]
    waterfall_measure = ["relative"] * 7 + ["total"]
    
    return {
        'labels': waterfall_labels,
        'values': waterfall_values,
        'text': waterfall_text,
        'measure': waterfall_measure
    }


def creer_donnees_graphique_repartition(resultat_optimisation, duree_annees):
    """
    Crée les données pour le graphique de répartition du capital final.
    """
    df_res_optimal = resultat_optimisation['df_res_optimal']
    mois_final = int(duree_annees * 12)  # Dernier mois disponible (maintenant 180)
    
    labels = ['Assurance Vie', 'PER', 'SCPI']
    values = [
        df_res_optimal.loc[df_res_optimal['mois'] == mois_final, 'solde_av_mensuel'].values[0],
        df_res_optimal.loc[df_res_optimal['mois'] == mois_final, 'solde_per_mensuel'].values[0],
        df_res_optimal.loc[df_res_optimal['mois'] == mois_final, 'solde_scpi_mensuel'].values[0]
    ]
    
    return {'labels': labels, 'values': values}
