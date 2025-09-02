import pandas as pd
from datetime import date
import uuid
import streamlit as st
from datetime import date
# --- Fonctions de calcul de prêt ---

def calculate_monthly_payment(principal, annual_rate_pct, duration_months):
    """Calcule la mensualité d'un prêt."""
    if duration_months == 0 or annual_rate_pct is None or principal == 0:
        return 0.0
    
    monthly_rate = (annual_rate_pct / 100) / 12
    total_months = duration_months

    if monthly_rate == 0:
        return principal / total_months if total_months > 0 else 0

    payment = principal * (monthly_rate * (1 + monthly_rate)**total_months) / ((1 + monthly_rate)**total_months - 1)
    return payment

def calculate_crd(principal, annual_rate_pct, duration_months, start_date, on_date=None):
    """Calcule le Capital Restant Dû (CRD) à une date donnée."""
    if not all([principal > 0, annual_rate_pct is not None, duration_months > 0, start_date]):
        return principal

    if on_date is None:
        on_date = date.today()
        
    if start_date > on_date:
        return principal

    # On ne compte que les mois pleins écoulés
    months_passed = (on_date.year - start_date.year) * 12 + (on_date.month - start_date.month)
    total_months = duration_months
    
    if months_passed >= total_months:
        return 0.0

    monthly_payment = calculate_monthly_payment(principal, annual_rate_pct, duration_months)
    monthly_rate = (annual_rate_pct / 100) / 12
    remaining_months = total_months - months_passed
    
    if monthly_rate == 0:
        return max(0, principal - (months_passed * monthly_payment))

    crd = monthly_payment * (1 - (1 + monthly_rate)**-remaining_months) / monthly_rate
    return max(0, crd)

def calculate_loan_annual_breakdown(loan, year=None):
    """
    Calcule la répartition annuelle du capital et des intérêts pour un prêt donné.

    Args:
        loan (dict): Dictionnaire contenant les informations du prêt.
                     Doit contenir 'montant_initial', 'taux_annuel', 'duree_mois', 'date_debut'.
        year (int, optional): L'année pour laquelle faire le calcul. 
                              Par défaut, l'année actuelle.

    Returns:
        dict: Un dictionnaire avec 'capital', 'interest', et 'total_paid' pour l'année.
    """
    if not loan:
        return {'capital': 0, 'interest': 0, 'total_paid': 0}

    if year is None:
        year = date.today().year

    # Extraire les détails du prêt
    principal = loan.get('montant_initial', 0)
    annual_rate_pct = loan.get('taux_annuel')
    duration_months = loan.get('duree_mois', 0)
    start_date = loan.get('date_debut')

    if not all([principal > 0, annual_rate_pct is not None, duration_months > 0, start_date]):
        return {'capital': 0, 'interest': 0, 'total_paid': 0}

    # --- 1. Calcul du capital remboursé (méthode la plus fiable) ---
    # On prend la fin de l'année N-1 et la fin de l'année N pour capturer tous les paiements de l'année N
    date_debut_annee = date(year - 1, 12, 31)
    date_fin_annee = date(year, 12, 31)

    crd_debut_annee = calculate_crd(principal, annual_rate_pct, duration_months, start_date, on_date=date_debut_annee)
    crd_fin_annee = calculate_crd(principal, annual_rate_pct, duration_months, start_date, on_date=date_fin_annee)
    capital_rembourse = crd_debut_annee - crd_fin_annee

    # --- 2. Calcul du total payé (nombre de mensualités) ---
    mensualite = calculate_monthly_payment(principal, annual_rate_pct, duration_months)
    total_duration_months = duration_months
    
    def get_months_passed(current_date):
        if start_date > current_date: return 0
        return (current_date.year - start_date.year) * 12 + (current_date.month - start_date.month)

    months_passed_start = min(get_months_passed(date_debut_annee), total_duration_months)
    months_passed_end = min(get_months_passed(date_fin_annee), total_duration_months)

    nombre_paiements_annee = months_passed_end - months_passed_start
    total_paye_annee = nombre_paiements_annee * mensualite

    # --- 3. Calcul des intérêts par déduction ---
    interets_payes = total_paye_annee - capital_rembourse

    return {'capital': max(0, capital_rembourse), 'interest': max(0, interets_payes), 'total_paid': max(0, total_paye_annee)}

# --- Fonctions de gestion des données du patrimoine ---

def get_patrimoine_df(actifs, passifs):
    """
    Crée un DataFrame consolidé du patrimoine avec les valeurs brutes et nettes.
    """
    if not actifs:
        return pd.DataFrame()

    # Crée un dictionnaire qui mappe l'ID de chaque actif à sa dette totale (CRD)
    dette_par_actif = {}
    for p in passifs:
        asset_id = p.get('actif_associe_id')
        if asset_id:
            crd = p.get('crd_calcule', 0)
            dette_par_actif[asset_id] = dette_par_actif.get(asset_id, 0) + crd

    # Construit le DataFrame
    data = []
    for a in actifs:
        asset_id = a.get('id')
        valeur_brute = a.get('valeur', 0.0)
        dette_associee = dette_par_actif.get(asset_id, 0.0)
        valeur_nette = valeur_brute - dette_associee
        data.append({
            'Libellé': a.get('libelle') or 'Actif sans nom',
            'Type': a.get('type', 'Indéfini'),
            'Valeur Brute': valeur_brute,
            'Passif': dette_associee,
            'Valeur Nette': valeur_nette
        })

    return pd.DataFrame(data)

def add_item(category):
    """Ajoute un élément à la liste des actifs ou passifs."""
    if category == 'actifs':
        st.session_state.actifs.append({
            'id': str(uuid.uuid4()),
            'libelle': '', 
            'type': 'Immobilier de jouissance', 
            'valeur': 0.0
        })
    elif category == 'passifs':
        st.session_state.passifs.append({
            'libelle': '', 
            'montant_initial': 100000.0,
            'taux_annuel': 1.5,
            'duree_mois': 240,
            'date_debut': date.today(),
            'actif_associe_id': None
        })

def remove_item(category, index):
    """Supprime un élément d'une liste à un index donné."""
    if category == 'actifs':
        asset_to_remove_id = st.session_state.actifs[index].get('id')
        st.session_state.actifs.pop(index)
        if asset_to_remove_id:
            for passif in st.session_state.passifs:
                if passif.get('actif_associe_id') == asset_to_remove_id:
                    passif['actif_associe_id'] = None
    elif category == 'passifs':
        st.session_state.passifs.pop(index)
    st.rerun()

# --- Fonctions d'analyse immobilière ---

def find_associated_loans(asset_id, passifs):
    """Trouve tous les prêts associés à un ID d'actif."""
    if not asset_id:
        return []
    return [p for p in passifs if p.get('actif_associe_id') == asset_id]

def calculate_lmnp_amortissement_annuel(asset):
    """
    Calcule l'amortissement annuel potentiel pour un bien en location meublée.
    Les durées sont des standards couramment admis.
    """
    DUREE_AMORTISSEMENT_IMMEUBLE = 30  # ans
    DUREE_AMORTISSEMENT_TRAVAUX = 15   # ans
    DUREE_AMORTISSEMENT_MEUBLES = 7    # ans

    valeur_totale = asset.get('valeur', 0)
    valeur_foncier = asset.get('part_amortissable_foncier', 0)
    valeur_travaux = asset.get('part_travaux', 0)
    valeur_meubles = asset.get('part_meubles', 0)

    # La base amortissable de l'immeuble est la valeur totale moins les autres parts.
    base_immeuble = max(0, valeur_totale - valeur_foncier - valeur_travaux - valeur_meubles)

    amortissement_immeuble = base_immeuble / DUREE_AMORTISSEMENT_IMMEUBLE if DUREE_AMORTISSEMENT_IMMEUBLE > 0 else 0
    amortissement_travaux = valeur_travaux / DUREE_AMORTISSEMENT_TRAVAUX if DUREE_AMORTISSEMENT_TRAVAUX > 0 else 0
    amortissement_meubles = valeur_meubles / DUREE_AMORTISSEMENT_MEUBLES if DUREE_AMORTISSEMENT_MEUBLES > 0 else 0

    total = amortissement_immeuble + amortissement_travaux + amortissement_meubles

    return {
        'immeuble': amortissement_immeuble,
        'travaux': amortissement_travaux,
        'meubles': amortissement_meubles,
        'total': total
    }


def calculate_gross_yield(asset):
    """Calcule la rentabilité brute en %."""
    loyers_annuels = asset.get('loyers_mensuels', 0) * 12
    valeur_achat = asset.get('valeur', 0)
    if not valeur_achat: return 0.0
    return (loyers_annuels / valeur_achat) * 100

def calculate_net_yield_charges(asset):
    """Calcule la rentabilité nette de charges en %."""
    loyers_annuels = asset.get('loyers_mensuels', 0) * 12
    charges_annuelles = asset.get('charges', 0) * 12
    taxe_fonciere = asset.get('taxe_fonciere', 0)
    valeur_achat = asset.get('valeur', 0)
    if not valeur_achat: return 0.0
    
    revenu_net_charges = loyers_annuels - charges_annuelles - taxe_fonciere
    return (revenu_net_charges / valeur_achat) * 100

def calculate_property_tax(asset, loans, tmi_pct, social_tax_pct, year=None, amortissement_annuel_utilise=0.0):
    """Calcule l'impôt total (IR + PS) sur les revenus fonciers au régime réel."""
    if year is None:
        year = date.today().year

    loyers_annuels = asset.get('loyers_mensuels', 0) * 12
    charges_annuelles = asset.get('charges', 0) * 12
    taxe_fonciere = asset.get('taxe_fonciere', 0)
    
    # Agréger les intérêts de tous les prêts associés
    interets_emprunt = sum(calculate_loan_annual_breakdown(l, year=year).get('interest', 0) for l in loans)

    charges_deductibles = charges_annuelles + taxe_fonciere + interets_emprunt

    # --- Spécificité Scellier Intermédiaire : abattement de 30% sur les loyers ---
    is_scellier_inter = asset.get('dispositif_fiscal', '') == 'Scellier Intermediaire'
    abattement_scellier_inter = 0.0
    loyers_abattus = loyers_annuels

    if is_scellier_inter:
        annee_debut = asset.get('annee_debut_dispositif')
        duree = asset.get('duree_dispositif')
        if annee_debut and duree and (annee_debut <= year < annee_debut + duree):
            abattement_scellier_inter = 0.3
            loyers_abattus = loyers_annuels * (1 - abattement_scellier_inter)
        else:
            abattement_scellier_inter = 0.0
            loyers_abattus = loyers_annuels

    revenu_foncier_imposable = max(0, loyers_abattus - charges_deductibles - amortissement_annuel_utilise)
    
    impot_sur_revenu = revenu_foncier_imposable * (tmi_pct / 100)
    prelevements_sociaux = revenu_foncier_imposable * (social_tax_pct / 100)

    # --- Calcul de la réduction d'impôt (Pinel & Scellier) ---
    reduction_pinel = 0
    reduction_scellier = 0
    # Pinel
    if asset.get('dispositif_fiscal') == 'Pinel':
        annee_debut = asset.get('annee_debut_dispositif')
        duree = asset.get('duree_dispositif')
        
        if annee_debut and duree and (annee_debut <= year < annee_debut + duree):
            # Le calcul de la réduction se base sur la valeur d'achat, plafonnée à 300 000 €
            base_calcul = min(asset.get('valeur', 0), 300000)
            
            # Taux annuel : 2% les 9 premières années, 1% de la 10e à la 12e
            annees_ecoulees = year - annee_debut
            if 0 <= annees_ecoulees < 9:
                taux_reduction_annuel = 0.02
            elif 9 <= annees_ecoulees < 12 and duree == 12:
                taux_reduction_annuel = 0.01
            else:
                taux_reduction_annuel = 0 # Ne devrait pas arriver dans la condition de l'année
            
            reduction_pinel = base_calcul * taux_reduction_annuel

    # Scellier (classique et intermédiaire)
    if asset.get('dispositif_fiscal', '').startswith('Scellier'):
        annee_debut = asset.get('annee_debut_dispositif')
        duree = asset.get('duree_dispositif')
        scellier_type = asset.get('dispositif_fiscal')  # 'Scellier' ou 'Scellier Intermediaire'
        print(f"[DEBUG Scellier] Année: {year}, annee_debut: {annee_debut}, duree: {duree}, type: {scellier_type}")
        if annee_debut and duree and (annee_debut <= year < annee_debut + duree):
            base_calcul = min(asset.get('valeur', 0), 300000)
            annees_ecoulees = year - annee_debut
            print(f"[DEBUG Scellier] base_calcul: {base_calcul}, annees_ecoulees: {annees_ecoulees}")
            # Barèmes principaux (hors DOM, hors BBC, hors majorations spécifiques)
            if scellier_type == 'Scellier':
                if annee_debut in [2009, 2010]:
                    taux_total = 0.25
                elif annee_debut == 2011:
                    taux_total = 0.20
                elif annee_debut == 2012:
                    taux_total = 0.13
                else:
                    taux_total = 0
                print(f"[DEBUG Scellier] taux_total (classique): {taux_total}")
                # 9 premières années
                if duree >= 9 and annees_ecoulees < 9:
                    reduction_scellier = base_calcul * taux_total / 9
                    print(f"[DEBUG Scellier] reduction_scellier (classique, 0-9): {reduction_scellier}")
                # Années 10 à 15 (prorogation possible)
                elif duree >= 15 and 9 <= annees_ecoulees < 15:
                    # 2%/an de la base sur 6 ans supplémentaires (soit 12% au total)
                    reduction_scellier = base_calcul * 0.02
                    print(f"[DEBUG Scellier] reduction_scellier (classique, 10-15): {reduction_scellier}")
            elif scellier_type == 'Scellier Intermediaire':
                if annee_debut in [2009, 2010]:
                    taux_total = 0.27
                elif annee_debut == 2011:
                    taux_total = 0.23
                elif annee_debut == 2012:
                    taux_total = 0.17
                else:
                    taux_total = 0
                print(f"[DEBUG Scellier] taux_total (intermediaire): {taux_total}")
                # 9 premières années
                if duree >= 9 and annees_ecoulees < 9:
                    reduction_scellier = base_calcul * taux_total / 9
                    print(f"[DEBUG Scellier] reduction_scellier (intermediaire, 0-9): {reduction_scellier}")
                # Années 10 à 15 (prorogation possible)
                elif duree >= 15 and 9 <= annees_ecoulees < 15:
                    # 2%/an de la base sur 6 ans supplémentaires (soit 12% au total)
                    reduction_scellier = base_calcul * 0.02
                    print(f"[DEBUG Scellier] reduction_scellier (intermediaire, 10-15): {reduction_scellier}")
            # Pas de prorogation prise en compte ici (uniquement 9 ou 15 ans)
        else:
            print("[DEBUG Scellier] Conditions non remplies pour réduction Scellier")

    total_impot = impot_sur_revenu + prelevements_sociaux - reduction_pinel - reduction_scellier
    print(f"[DEBUG Scellier] total_impot: {total_impot}, reduction_pinel: {reduction_pinel}, reduction_scellier: {reduction_scellier}")

    return {
        'total': total_impot,
        'ir': impot_sur_revenu,
        'ps': prelevements_sociaux,
        'reduction_pinel': reduction_pinel,
        'reduction_scellier': reduction_scellier
    }

def calculate_net_yield_tax(asset, total_annual_tax):
    """Calcule la rentabilité nette de fiscalité en %."""
    loyers_annuels = asset.get('loyers_mensuels', 0) * 12
    charges_annuelles = asset.get('charges', 0) * 12
    taxe_fonciere = asset.get('taxe_fonciere', 0)
    valeur_achat = asset.get('valeur', 0)
    if not valeur_achat: return 0.0

    revenu_final = loyers_annuels - charges_annuelles - taxe_fonciere - total_annual_tax
    return (revenu_final / valeur_achat) * 100

def calculate_savings_effort(asset, loans, total_annual_tax, year=None):
    """Calcule le cash-flow mensuel (effort d'épargne) pour une année donnée."""
    if year is None:
        year = date.today().year
        
    loyers_mensuels = asset.get('loyers_mensuels', 0)
    charges_mensuelles = asset.get('charges', 0)
    taxe_fonciere_mensuelle = asset.get('taxe_fonciere', 0) / 12

    # Agréger les mensualités de tous les prêts pour l'année donnée
    paiements_annuels_prets = sum(calculate_loan_annual_breakdown(l, year=year).get('total_paid', 0) for l in loans)
    mensualites_prets = paiements_annuels_prets / 12

    cash_flow = loyers_mensuels - charges_mensuelles - taxe_fonciere_mensuelle - mensualites_prets - (total_annual_tax / 12)
    return cash_flow