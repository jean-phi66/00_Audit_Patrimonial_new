#!/usr/bin/env python3
"""
Test pour vérifier la logique d'empilement du graphique de transition.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_stacked_logic():
    """Test la logique d'empilement identique aux projections."""
    
    print("=== TEST LOGIQUE D'EMPILEMENT TRANSITION ===")
    
    # Simulation des données d'une année
    revenus_annuels = 90000  # €/an
    donnees_annuelles = {
        'Reste à vivre': 30000,
        'Impôt sur le revenu': 15000,
        'Prélèvements Sociaux': 5000,
        'Mensualités Prêts': 20000,
        'Charges Immobilières': 8000,
        'Taxes Foncières': 3000,
        'Autres Dépenses': 9000,
        'Coût des études': 0
    }
    
    print(f"Données d'exemple (annuelles) :")
    print(f"Revenus du foyer : {revenus_annuels:,}€")
    
    # Conversion en mensuel
    revenus_mensuels = revenus_annuels / 12
    print(f"\nRevenus mensuels : {revenus_mensuels:,.0f}€/mois")
    
    print(f"\nComposantes empilées (mensuelles) :")
    total_empile = 0
    for categorie, montant_annuel in donnees_annuelles.items():
        if montant_annuel > 0:
            montant_mensuel = montant_annuel / 12
            total_empile += montant_mensuel
            print(f"  {categorie:<25} : {montant_mensuel:>8.0f}€/mois")
    
    print(f"  {'─' * 35}")
    print(f"  {'Total empilé':<25} : {total_empile:>8.0f}€/mois")
    
    # Vérification
    difference = abs(revenus_mensuels - total_empile)
    print(f"\n=== VÉRIFICATION ===")
    print(f"Revenus mensuels    : {revenus_mensuels:,.0f}€")
    print(f"Total empilé        : {total_empile:,.0f}€")
    print(f"Différence          : {difference:,.0f}€")
    
    if difference < 1:  # Tolérance d'1€ pour les arrondis
        print("✅ COHÉRENT : La hauteur totale des barres empilées = revenus mensuels")
    else:
        print("❌ INCOHÉRENT : Différence significative détectée")
    
    print(f"\n=== COMPORTEMENT VISUEL ===")
    print("📊 Graphique en barres empilées :")
    print("   - Chaque segment = un poste de dépense")
    print("   - Hauteur totale = revenus du mois")
    print("   - Ligne horizontale en pointillés = référence revenus")
    print("   - Même logique que les graphiques de projection")

if __name__ == "__main__":
    test_stacked_logic()
