#!/usr/bin/env python3
"""
Test pour comprendre le décalage dans les bar charts de projection
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import date
import pandas as pd

def test_projection_charts_logic():
    """Test la logique des données utilisées dans les bar charts de projection."""
    
    print("=== TEST LOGIQUE DES BAR CHARTS DE PROJECTION ===")
    
    # Paramètres d'exemple
    date_naissance = date(1990, 5, 15)
    age_retraite = 64
    annee_retraite = date_naissance.year + age_retraite
    
    print(f"Configuration :")
    print(f"- Date de naissance : {date_naissance}")
    print(f"- Âge de retraite : {age_retraite}")
    print(f"- Année de retraite calculée : {annee_retraite}")
    
    # Simulation des données de projection (comme dans generate_projection_data)
    print(f"\n=== DONNÉES DE PROJECTION (revenus) ===")
    
    revenus_projection = []
    for annee in range(2052, 2057):
        # Calcul de l'âge (logique simplifiée)
        age = annee - date_naissance.year
        
        # Logique des revenus (projection_logic.py ligne ~143)
        if age < age_retraite:
            status = "Actif"
            revenu = 90000  # Exemple
        else:
            status = "Retraite" 
            revenu = 55000  # Exemple
            
        revenus_projection.append({
            'Année': annee,
            'Âge': age,
            'Statut': status,
            'Revenu': revenu
        })
        
        print(f"Année {annee}: âge {age}, statut {status}, revenu {revenu:,}€")
    
    # Simulation du Gantt (AVANT correction)
    print(f"\n=== GANTT AVANT CORRECTION ===")
    finish_actif_avant = annee_retraite  # Logique d'avant
    start_retraite_avant = annee_retraite + 1
    print(f"Période active : jusqu'à {finish_actif_avant}")
    print(f"Période retraite : à partir de {start_retraite_avant}")
    print(f"❌ Décalage : Les revenus changent en {annee_retraite}, mais le Gantt montre la retraite en {start_retraite_avant}")
    
    # Simulation du Gantt (APRÈS correction)
    print(f"\n=== GANTT APRÈS CORRECTION ===")
    finish_actif_apres = annee_retraite - 1  # Logique corrigée
    start_retraite_apres = annee_retraite
    print(f"Période active : jusqu'à {finish_actif_apres}")
    print(f"Période retraite : à partir de {start_retraite_apres}")
    print(f"✅ Cohérent : Les revenus ET le Gantt changent tous les deux en {annee_retraite}")
    
    # Analyse du problème potentiel
    print(f"\n=== ANALYSE DU DÉCALAGE RAPPORTÉ ===")
    print(f"Si vous voyez encore un décalage, cela pourrait être dû à :")
    print(f"1. Cache/données non rafraîchies dans l'interface")
    print(f"2. Une autre fonction qui utilise l'ancienne logique")
    print(f"3. Les données de test qui ne reflètent pas la nouvelle logique")
    
    # Vérification des données pour l'analyse comparative
    print(f"\n=== DONNÉES POUR L'ANALYSE COMPARATIVE ===")
    annee_avant_retraite = annee_retraite - 1
    
    # Simulation des données filtrées
    df_transition = pd.DataFrame(revenus_projection)
    df_filtered = df_transition[df_transition['Année'].isin([annee_avant_retraite, annee_retraite])]
    
    print(f"Années sélectionnées pour la comparaison : {annee_avant_retraite}, {annee_retraite}")
    print(f"Données filtrées :")
    for _, row in df_filtered.iterrows():
        print(f"  {row['Année']}: {row['Statut']}, {row['Revenu']:,}€")

if __name__ == "__main__":
    test_projection_charts_logic()
