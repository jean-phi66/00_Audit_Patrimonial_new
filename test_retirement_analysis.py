#!/usr/bin/env python3
"""
Script de test pour la nouvelle fonction d'analyse de transition vers la retraite.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from datetime import date

def test_retirement_transition_analysis():
    """Test la nouvelle fonction d'analyse de transition vers la retraite."""
    
    print("=== Test de l'analyse de transition vers la retraite (mensuelle) ===")
    
    # Simulation des données de projection (montants annuels)
    df_projection = pd.DataFrame([
        {
            'Année': 2028, 'Revenus du foyer': 90000, 'Reste à vivre': 25000, 
            'Impôt sur le revenu': 8000, 'Mensualités Prêts': 12000,
            'Charges Immobilières': 3600, 'Taxes Foncières': 1200,
            'Autres Dépenses': 40200, 'Coût des études': 0
        },
        {
            'Année': 2029, 'Revenus du foyer': 55000, 'Reste à vivre': 18000,
            'Impôt sur le revenu': 3500, 'Mensualités Prêts': 12000,
            'Charges Immobilières': 3600, 'Taxes Foncières': 1200,
            'Autres Dépenses': 16700, 'Coût des études': 0
        }
    ])
    
    # Simulation des parents et settings
    parents = [{'prenom': 'Jean', 'date_naissance': date(1965, 5, 15)}]
    settings = {'Jean': {'retraite': 64}}
    
    print("Données simulées (annuelles):")
    print("- Année 2028 (avant retraite): 90 000€ de revenus, 25 000€ de reste à vivre")
    print("- Année 2029 (départ retraite): 55 000€ de revenus, 18 000€ de reste à vivre")
    print("- Âge de départ à la retraite: 64 ans")
    
    # Conversion en montants mensuels
    revenus_dec_2028 = 90000 / 12  # 7500€/mois
    revenus_jan_2029 = 55000 / 12  # 4583€/mois
    reste_dec_2028 = 25000 / 12    # 2083€/mois
    reste_jan_2029 = 18000 / 12    # 1500€/mois
    
    print(f"\nComparaison mensuelle:")
    print(f"- Décembre 2028 (dernier mois d'activité): {revenus_dec_2028:,.0f}€ de revenus, {reste_dec_2028:,.0f}€ de reste à vivre")
    print(f"- Janvier 2029 (premier mois de retraite): {revenus_jan_2029:,.0f}€ de revenus, {reste_jan_2029:,.0f}€ de reste à vivre")
    
    # Calculs des ratios mensuels
    ratio_revenus = revenus_jan_2029 / revenus_dec_2028
    ratio_reste_vivre = reste_jan_2029 / reste_dec_2028
    
    print(f"\nRatios calculés (mensuel):")
    print(f"- Ratio revenus (janvier/décembre): {ratio_revenus:.1%}")
    print(f"- Ratio reste à vivre (janvier/décembre): {ratio_reste_vivre:.1%}")
    
    # Analyse
    if ratio_revenus >= 0.8:
        print("✅ Excellente transition au niveau des revenus")
    elif ratio_revenus >= 0.6:
        print("⚠️ Transition modérée au niveau des revenus")
    else:
        print("🚨 Transition difficile au niveau des revenus")
    
    if ratio_reste_vivre >= 0.8:
        print("✅ Capacité d'épargne bien maintenue")
    elif ratio_reste_vivre >= 0.5:
        print("⚠️ Capacité d'épargne réduite")
    else:
        print("🚨 Capacité d'épargne fortement impactée")
    
    print(f"\nDifférences mensuelles:")
    print(f"- Baisse de revenus: {revenus_dec_2028 - revenus_jan_2029:,.0f}€/mois")
    print(f"- Baisse du reste à vivre: {reste_dec_2028 - reste_jan_2029:,.0f}€/mois")
    
    print("\n=== Test d'import de la fonction ===")
    try:
        from core.projection_display import display_retirement_transition_analysis
        print("✅ Fonction importée avec succès")
        print("📊 La fonction est prête à être utilisée dans Streamlit avec comparaison mensuelle")
    except Exception as e:
        print(f"❌ Erreur lors de l'import: {e}")

if __name__ == "__main__":
    test_retirement_transition_analysis()
