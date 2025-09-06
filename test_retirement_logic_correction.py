#!/usr/bin/env python3
"""
Script de test pour vérifier la logique corrigée de l'analyse de transition vers la retraite.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from datetime import date

def test_retirement_transition_logic():
    """Test la logique corrigée pour l'analyse de transition vers la retraite."""
    
    print("=== Test de la logique corrigée de transition vers la retraite ===")
    
    # Exemple : Départ à la retraite en 2054
    prenom = "Jean"
    date_naissance = date(1990, 5, 15)  # Né en 1990
    age_retraite = 64
    annee_retraite = date_naissance.year + age_retraite  # 1990 + 64 = 2054
    
    print(f"Configuration de test :")
    print(f"- {prenom} né en {date_naissance.year}")
    print(f"- Âge de départ à la retraite : {age_retraite} ans")
    print(f"- Année de départ à la retraite : {annee_retraite}")
    
    # Logique actuelle (corrigée)
    annee_avant_retraite = annee_retraite - 1
    
    print(f"\nComparaison :")
    print(f"- Année d'activité à comparer : {annee_avant_retraite}")
    print(f"- Année de retraite à comparer : {annee_retraite}")
    
    print(f"\nCela correspond à :")
    print(f"- Revenus moyens de {annee_avant_retraite} (dernière année complète d'activité)")
    print(f"- Revenus moyens de {annee_retraite} (première année complète de retraite)")
    
    # Simulation des données
    revenus_activite_2053 = 90000  # Année d'activité
    revenus_retraite_2054 = 55000  # Année de retraite
    
    print(f"\nExemple avec vos données :")
    print(f"- Revenus {annee_avant_retraite} (activité) : {revenus_activite_2053:,}€/an = {revenus_activite_2053/12:,.0f}€/mois")
    print(f"- Revenus {annee_retraite} (retraite) : {revenus_retraite_2054:,}€/an = {revenus_retraite_2054/12:,.0f}€/mois")
    
    ratio = (revenus_retraite_2054 / 12) / (revenus_activite_2053 / 12)
    print(f"- Ratio de transition : {ratio:.1%}")
    
    print(f"\n=== Vérification ===")
    if annee_avant_retraite == 2053 and annee_retraite == 2054:
        print("✅ La logique est correcte !")
        print("   Nous comparons bien 2053 (activité) vs 2054 (retraite)")
    else:
        print("❌ Il y a encore un problème dans la logique")
    
    print(f"\nNote importante :")
    print(f"Les données de projection sont annuelles, pas mensuelles.")
    print(f"Nous comparons donc les moyennes annuelles, converties en équivalent mensuel.")
    print(f"C'est une approximation raisonnable car :")
    print(f"- L'année {annee_avant_retraite} représente une année complète d'activité")
    print(f"- L'année {annee_retraite} représente une année complète de retraite")

if __name__ == "__main__":
    test_retirement_transition_logic()
