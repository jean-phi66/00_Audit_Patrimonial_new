#!/usr/bin/env python3
"""
Test pour identifier l'année exacte de transition vers la retraite
dans la projection vs dans l'analyse comparative.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import date

def test_retirement_year_logic():
    """Test la logique de calcul de l'année de retraite."""
    
    print("=== Test de l'année de départ à la retraite ===")
    
    # Données d'exemple
    date_naissance = date(1990, 5, 15)  # Né en mai 1990
    age_retraite = 64
    
    print(f"Date de naissance : {date_naissance}")
    print(f"Âge de départ à la retraite : {age_retraite} ans")
    
    # Calcul standard
    annee_retraite = date_naissance.year + age_retraite
    print(f"\nCalcul : {date_naissance.year} + {age_retraite} = {annee_retraite}")
    
    # Logique de la projection des revenus
    print(f"\n=== Logique de projection des revenus ===")
    for annee in range(2052, 2057):
        # Simuler la date courante dans l'année
        current_date_in_year = date(annee, 7, 1)  # 1er juillet de l'année
        
        # Calculer l'âge au 1er juillet de cette année
        age = annee - date_naissance.year
        if current_date_in_year.replace(year=date_naissance.year) < date_naissance:
            age -= 1
            
        # Déterminer le statut
        if age < age_retraite:
            status = "Actif"
        else:
            status = "Retraite"
            
        print(f"Année {annee}: âge = {age}, statut = {status}")
    
    print(f"\n=== Analyse ===")
    print(f"Selon cette logique :")
    print(f"- En {annee_retraite-1} : âge = {age_retraite-1}, statut = Actif")
    print(f"- En {annee_retraite} : âge = {age_retraite}, statut = Retraite")
    print(f"\nDonc l'année de transition est bien {annee_retraite}")
    print(f"Et notre comparaison doit être :")
    print(f"- Année d'activité : {annee_retraite-1}")
    print(f"- Année de retraite : {annee_retraite}")

if __name__ == "__main__":
    test_retirement_year_logic()
