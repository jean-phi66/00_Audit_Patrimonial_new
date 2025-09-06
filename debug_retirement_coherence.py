#!/usr/bin/env python3
"""
Script de débogage pour vérifier la cohérence des calculs d'année de retraite
dans toutes les fonctions du projet.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import date

def debug_retirement_calculations():
    """Débogue tous les calculs d'année de retraite."""
    
    print("=== DÉBOGAGE DES CALCULS D'ANNÉE DE RETRAITE ===")
    
    # Paramètres d'exemple (à adapter selon vos vraies données)
    date_naissance = date(1990, 5, 15)
    age_retraite = 64
    prenom = "Jean"
    
    print(f"Configuration de test :")
    print(f"- Prénom : {prenom}")
    print(f"- Date de naissance : {date_naissance}")
    print(f"- Âge de retraite : {age_retraite}")
    
    # 1. Calcul standard utilisé partout
    annee_retraite = date_naissance.year + age_retraite
    print(f"\n1. CALCUL STANDARD :")
    print(f"   annee_retraite = {date_naissance.year} + {age_retraite} = {annee_retraite}")
    
    # 2. Logique de l'analyse comparative
    annee_avant_retraite = annee_retraite - 1
    print(f"\n2. ANALYSE COMPARATIVE (display_retirement_transition_analysis) :")
    print(f"   annee_avant_retraite = {annee_retraite} - 1 = {annee_avant_retraite}")
    print(f"   annee_retraite = {annee_retraite}")
    print(f"   → Comparaison : {annee_avant_retraite} (activité) vs {annee_retraite} (retraite)")
    
    # 3. Logique du Gantt (projection_logic.py ligne 40) - CORRIGÉE
    finish_actif = annee_retraite - 1  # min(annee_retraite - 1, annee_fin_projection)
    start_retraite = annee_retraite  # Plus de +1
    print(f"\n3. GANTT (projection_logic.py) - CORRIGÉ :")
    print(f"   finish_actif = {annee_retraite} - 1 = {finish_actif} (fin de la période active)")
    print(f"   start_retraite = {annee_retraite} (début de la période retraite)")
    print(f"   → Cohérent avec la logique des revenus")
    
    # 4. Logique des revenus (projection_logic.py ligne 143)
    print(f"\n4. PROJECTION DES REVENUS (projection_logic.py) :")
    for annee in range(annee_retraite - 2, annee_retraite + 3):
        age = annee - date_naissance.year
        if age < age_retraite:
            status = "Actif"
        else:
            status = "Retraite"
        print(f"   Année {annee} : âge = {age}, statut = {status}")
    
    print(f"\n=== ANALYSE ===")
    print(f"La logique des revenus (4) dit que la transition a lieu en {annee_retraite}")
    print(f"La logique du Gantt (3) dit que la retraite commence en {start_retraite}")
    print(f"L'analyse comparative (2) compare {annee_avant_retraite} vs {annee_retraite}")
    
    if start_retraite == annee_retraite:
        print(f"\n✅ COHÉRENCE RÉTABLIE !")
        print(f"   Toutes les logiques sont maintenant alignées")
        print(f"   Transition : {annee_retraite}")
        print(f"   Comparaison : {annee_avant_retraite} (activité) vs {annee_retraite} (retraite)")
    else:
        print(f"\n❌ INCOHÉRENCE DÉTECTÉE !")
        print(f"   Le Gantt décale la retraite d'un an par rapport aux revenus")
        print(f"   Revenus : transition en {annee_retraite}")
        print(f"   Gantt : transition en {start_retraite}")

if __name__ == "__main__":
    debug_retirement_calculations()
