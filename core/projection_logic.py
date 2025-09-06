import pandas as pd
from datetime import date
import streamlit as st
from core.patrimoine_logic import calculate_loan_annual_breakdown, find_associated_loans, calculate_crd, calculate_lmnp_amortissement_annuel

try:
    from utils.openfisca_utils import analyser_fiscalite_foyer
    OPENFISCA_UTILITY_AVAILABLE = True
except ImportError as e:
    OPENFISCA_UTILITY_AVAILABLE = False

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
        
        # La période active se termine l'année précédant la retraite
        finish_actif = min(annee_retraite - 1, annee_fin_projection)

        if today.year <= finish_actif:
            gantt_data.append(dict(
                Task=prenom,
                Start=f"{today.year}-01-01",
                Finish=f"{finish_actif}-12-31",
                Resource="Actif"
            ))

        # La retraite commence l'année de transition (cohérent avec la logique des revenus)
        start_retraite = annee_retraite
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

def generate_financial_projection(parents, enfants, passifs, settings, projection_duration):
    """Génère les données de projection financière année par année."""
    projection_data = []
    today = date.today()

    # Récupérer les paramètres de revenus pour chaque parent
    income_settings = {}
    for p in parents:
        prenom = p['prenom']
        income_settings[prenom] = {
            'revenu_actuel': settings[prenom].get('revenu_actuel', 0),
            'pension_annuelle': settings[prenom].get('pension_annuelle', 25000)
        }

    actifs_productifs = [a for a in st.session_state.get('actifs', []) if a.get('type') == 'Immobilier productif']

    for i in range(projection_duration + 1):
        annee = today.year + i
        current_date_in_year = date(annee, 1, 1)
        year_data = {'Année': annee}
        
        revenus_annuels_parents = {}
        
        # --- Traitement des parents ---
        for parent in parents:
            prenom = parent['prenom']
            dob = parent['date_naissance']
            # Calcul simplifié de l'âge pour cohérence avec le Gantt
            age = annee - dob.year
            year_data[f'Âge {prenom}'] = age
            
            age_retraite = settings[prenom]['retraite']
            
            if age < age_retraite:
                status_parent = "Actif"
                revenu = income_settings[prenom]['revenu_actuel']
            else:
                status_parent = "Retraite"
                revenu = income_settings[prenom]['pension_annuelle']
            
            year_data[f'Statut {prenom}'] = status_parent
            revenus_annuels_parents[prenom] = revenu
            year_data[f'Revenu {prenom}'] = revenu

        # --- Calculs pour le foyer ---
        total_revenus_foyer = sum(revenus_annuels_parents.values())
        year_data['Revenus bruts du foyer'] = total_revenus_foyer
        
        # --- Déterminer les enfants à charge pour l'année en cours ---
        enfants_a_charge_annee = []
        total_cout_etudes_annee = 0
        for enfant in enfants:
            prenom_enfant = enfant.get('prenom')
            dob_enfant = enfant.get('date_naissance')
            if not prenom_enfant or not dob_enfant:
                continue

            # 1. Récupérer les paramètres pour l'enfant
            settings_enfant = settings.get(prenom_enfant, {})
            age_debut_etudes = settings_enfant.get('debut_etudes', 18)
            duree_etudes = settings_enfant.get('duree_etudes', 5)
            cout_etudes_annuel = settings_enfant.get('cout_etudes_annuel', 0)

            # 2. Calcul de l'âge et du statut de l'enfant pour l'année en cours
            age_enfant = calculate_age(dob_enfant, current_date_in_year)
            
            if age_enfant < age_debut_etudes:
                status = "Scolarisé"
            elif age_enfant <= age_debut_etudes + duree_etudes:
                status = "Études"
            else:
                status = "Actif"
            
            year_data[f'Âge {prenom_enfant}'] = age_enfant
            year_data[f'Statut {prenom_enfant}'] = status

            # 3. Déterminer si l'enfant est à charge et ajouter les coûts associés
            if status != "Actif":
                enfants_a_charge_annee.append(enfant)
            
            if status == "Études":
                total_cout_etudes_annee += cout_etudes_annuel

        year_data['Coût des études'] = total_cout_etudes_annee

        # --- Flux financiers (revenus et dépenses) ---
        # 1. Calcul dynamique des mensualités de prêts pour l'année en cours
        total_paiements_prets_annee = 0
        for pret in passifs:
            breakdown = calculate_loan_annual_breakdown(pret, year=annee)
            total_paiements_prets_annee += breakdown.get('total_paid', 0)
        year_data['Mensualités Prêts'] = total_paiements_prets_annee

        # 2. Calcul des autres dépenses (qui sont supposées constantes pour l'instant)
        all_depenses = st.session_state.get('depenses', [])
        charges_immo = sum(d.get('montant', 0) * 12 for d in all_depenses if d.get('categorie') == 'Logement' and 'source_id' in d)
        # Exclure l'IR automatique des projections car il est recalculé avec OpenFisca
        taxes_foncieres = sum(d.get('montant', 0) * 12 for d in all_depenses if d.get('categorie') == 'Impôts et taxes' and 'source_id' in d and d.get('source_id') != 'fiscal_auto')
        autres_depenses = sum(d.get('montant', 0) * 12 for d in all_depenses if 'source_id' not in d)
        
        year_data['Charges Immobilières'] = charges_immo
        year_data['Taxes Foncières'] = taxes_foncieres
        year_data['Autres Dépenses'] = autres_depenses
        total_depenses = total_paiements_prets_annee + charges_immo + taxes_foncieres + autres_depenses + total_cout_etudes_annee

        # 3. Calcul des revenus annexes
        all_revenus = st.session_state.get('revenus', [])
        year_data['Loyers perçus'] = sum(r.get('montant', 0) * 12 for r in all_revenus if r.get('type') == 'Patrimoine')
        year_data['Autres revenus'] = sum(r.get('montant', 0) * 12 for r in all_revenus if r.get('type') == 'Autre')

        # --- Calcul de l'impôt ---
        # 1. Calcul des revenus fonciers et LMNP ---
        total_loyers_bruts_annee = 0
        total_charges_deductibles_annee = 0
        total_reduction_pinel_annee = 0
        total_revenu_lmnp_annee = 0

        for asset in actifs_productifs:
            loyers_annuels = asset.get('loyers_mensuels', 0) * 12
            charges_annuelles = asset.get('charges', 0) * 12
            taxe_fonciere = asset.get('taxe_fonciere', 0)
            loans = find_associated_loans(asset.get('id'), passifs)
            interets_emprunt = sum(calculate_loan_annual_breakdown(l, year=annee).get('interest', 0) for l in loans)
            charges_deductibles_asset = charges_annuelles + taxe_fonciere + interets_emprunt

            # --- Traitement LMNP avec amortissement réel ---
            if asset.get('mode_exploitation') == 'Location Meublée':
                # Utilisation de l'amortissement réel (dotation annuelle)
                amortissement = calculate_lmnp_amortissement_annuel(asset)
                amortissement_annuel = amortissement.get('total', 0)
                revenu_lmnp = loyers_annuels - charges_annuelles - taxe_fonciere - interets_emprunt - amortissement_annuel
                total_revenu_lmnp_annee += max(0, revenu_lmnp)
                continue  # Ne pas inclure dans les revenus fonciers classiques

            # Traitement classique (revenus fonciers)
            total_loyers_bruts_annee += loyers_annuels
            total_charges_deductibles_annee += charges_deductibles_asset

            # Calcul de la réduction d'impôt Pinel pour l'année
            if asset.get('dispositif_fiscal') == 'Pinel':
                annee_debut = asset.get('annee_debut_dispositif')
                duree = asset.get('duree_dispositif')
                if annee_debut and duree and (annee_debut <= annee < annee_debut + duree):
                    base_calcul = min(asset.get('valeur', 0), 300000)
                    annees_ecoulees = annee - annee_debut
                    taux_reduction_annuel = 0.02 if 0 <= annees_ecoulees < 9 else (0.01 if 9 <= annees_ecoulees < 12 and duree == 12 else 0)
                    total_reduction_pinel_annee += base_calcul * taux_reduction_annuel

        # Ajout du revenu foncier net calculé pour vérification dans le tableau
        revenu_foncier_net_calcule = max(0, total_loyers_bruts_annee - total_charges_deductibles_annee)
        year_data['Revenu Foncier Net'] = revenu_foncier_net_calcule
        year_data['Revenu LMNP'] = total_revenu_lmnp_annee

        # Calcul des prélèvements sociaux sur les revenus fonciers
        prelevements_sociaux = revenu_foncier_net_calcule * 0.172
        year_data['Prélèvements Sociaux'] = prelevements_sociaux

        # 2. Appel à OpenFisca avec tous les revenus
        if OPENFISCA_UTILITY_AVAILABLE:
            est_parent_isole = len(parents) == 1
            # Utilisation de la nouvelle fonction d'analyse complète
            # Retirer le paramètre revenu_lmnp si la fonction ne le supporte pas
            resultats_fiscaux = analyser_fiscalite_foyer(
                annee=annee,
                parents=parents,
                enfants=enfants_a_charge_annee,
                revenus_annuels=revenus_annuels_parents,
                revenu_foncier_net=revenu_foncier_net_calcule,
                est_parent_isole=est_parent_isole
            )
            impot_brut = resultats_fiscaux.get('ir_net', 0)
            impot = max(0, impot_brut - total_reduction_pinel_annee)
        else:
            # Fallback si OpenFisca n'est pas disponible
            total_revenus_imposables = total_revenus_foyer + revenu_foncier_net_calcule + total_revenu_lmnp_annee
            impot_brut = total_revenus_imposables * 0.15
            impot = max(0, impot_brut - total_reduction_pinel_annee)

        year_data['Impôt sur le revenu'] = impot

        # --- Finalisation des calculs financiers ---
        # Le "Reste à vivre" est maintenant calculé après déduction de toutes les charges, de l'impôt et des prélèvements sociaux.
        year_data['Revenus du foyer'] = total_revenus_foyer + year_data['Loyers perçus'] + year_data['Autres revenus']
        year_data['Reste à vivre'] = year_data['Revenus du foyer'] - total_depenses - impot - prelevements_sociaux

        # --- Calcul du CRD pour chaque prêt ---
        for pret in passifs:
            pret_id = pret['id']
            crd_fin_annee = calculate_crd(
                principal=pret.get('montant_initial', 0),
                annual_rate_pct=pret.get('taux_annuel'),
                duration_months=pret.get('duree_mois', 0),
                start_date=pret.get('date_debut'),
                on_date=date(annee, 12, 31)
            )
            year_data[f"CRD_{pret_id}"] = crd_fin_annee

        projection_data.append(year_data)
        
    df = pd.DataFrame(projection_data)

    # Définir l'ordre des colonnes principales pour l'affichage
    main_columns = ['Année']
    for parent in parents:
        main_columns.extend([f'Âge {parent["prenom"]}', f'Statut {parent["prenom"]}', f'Revenu {parent["prenom"]}'])
    for enfant in enfants:
        main_columns.extend([f'Âge {enfant["prenom"]}', f'Statut {enfant["prenom"]}'])
    main_columns.extend([
        'Revenus bruts du foyer', 'Loyers perçus', 'Revenu Foncier Net', 'Autres revenus', 'Revenus du foyer',
        'Mensualités Prêts', 'Charges Immobilières', 'Taxes Foncières', 'Autres Dépenses', 'Coût des études',
        'Impôt sur le revenu', 'Prélèvements Sociaux', 'Reste à vivre'
    ])

    # S'assurer que les colonnes principales existent
    for col in main_columns:
        if col not in df.columns:
            df[col] = 0

    # Récupérer les autres colonnes (comme les CRD) qui ne sont pas dans les colonnes principales
    other_columns = [col for col in df.columns if col not in main_columns]

    # Combiner les listes pour le nouvel ordre final et réordonner le DataFrame
    df = df[main_columns + other_columns]
    return df
