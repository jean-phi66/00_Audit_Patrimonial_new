#!/usr/bin/env python3
"""
Test avec les vraies données pour vérifier l'incohérence rapportée.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import date

def test_with_real_data():
    """Test avec les données que vous utilisez dans votre simulateur."""
    
    print("=== Test avec vos données réelles ===")
    print("Merci de me confirmer :")
    print("1. Date de naissance du parent")
    print("2. Âge de départ à la retraite configuré")
    print("3. Année affichée dans la projection comme 'année de départ'")
    print("4. Années affichées dans l'analyse comparative")
    
    # Exemple avec différentes dates de naissance pour illustrer
    exemples = [
        {"nom": "Exemple 1", "naissance": date(1990, 1, 1), "age_retraite": 64},
        {"nom": "Exemple 2", "naissance": date(1990, 6, 15), "age_retraite": 64},
        {"nom": "Exemple 3", "naissance": date(1990, 12, 31), "age_retraite": 64},
    ]
    
    for exemple in exemples:
        print(f"\n{exemple['nom']} - Né le {exemple['naissance']}")
        annee_retraite = exemple['naissance'].year + exemple['age_retraite']
        print(f"  Année de retraite calculée : {annee_retraite}")
        print(f"  Comparaison : {annee_retraite-1} (activité) vs {annee_retraite} (retraite)")
        
        # Test de cohérence avec la logique de projection
        for annee_test in [annee_retraite-1, annee_retraite, annee_retraite+1]:
            age_en_annee = annee_test - exemple['naissance'].year
            status = "Actif" if age_en_annee < exemple['age_retraite'] else "Retraite"
            print(f"    Année {annee_test}: âge {age_en_annee}, statut {status}")

if __name__ == "__main__":
    test_with_real_data()
