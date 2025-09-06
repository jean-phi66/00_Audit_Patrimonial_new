#!/usr/bin/env python3
"""
Test complet de cohérence avec les vraies fonctions du projet
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import date
import pandas as pd

# Essayer d'importer les vraies fonctions
try:
    from core.projection_logic import generate_financial_projection, generate_gantt_data
    print("✅ Importation des fonctions réussie")
except Exception as e:
    print(f"❌ Erreur d'importation : {e}")
    sys.exit(1)

def test_real_functions():
    """Test avec les vraies fonctions du projet."""
    
    print("=== TEST AVEC LES VRAIES FONCTIONS ===")
    
    # Données d'exemple pour les tests
    parents = [
        {
            'prenom': 'Jean',
            'date_naissance': date(1990, 5, 15)
        }
    ]
    
    enfants = []
    
    settings = {
        'Jean': {
            'retraite': 64,
            'debut_etudes': 18,
            'duree_etudes': 5
        }
    }
    
    income_settings = {
        'Jean': {
            'revenu_actuel': 90000,
            'pension_annuelle': 55000
        }
    }
    
    try:
        # Test du Gantt
        print("\n=== TEST DU GANTT ===")
        gantt_data = generate_gantt_data(parents, enfants, settings, 40)  # 40 ans de projection
        
        # Filtrer pour Jean seulement
        jean_data = [item for item in gantt_data if item['Task'] == 'Jean']
        
        for item in jean_data:
            print(f"{item['Resource']}: {item['Start']} à {item['Finish']}")
            
        # Test de la projection des revenus
        print("\n=== TEST DE LA PROJECTION DES REVENUS ===")
        df_projection = generate_financial_projection(parents, enfants, {}, settings, 35)  # 2025 à 2060
        
        # Filtrer les années autour de la retraite
        annee_retraite = 1990 + 64  # 2054
        df_filtered = df_projection[
            (df_projection['Année'] >= annee_retraite - 2) & 
            (df_projection['Année'] <= annee_retraite + 2)
        ]
        
        print(f"Projection autour de l'année de retraite ({annee_retraite}) :")
        for _, row in df_filtered.iterrows():
            status = row.get('Statut Jean', 'N/A')
            revenu = row.get('Revenu Jean', 0)
            print(f"  {row['Année']}: {status}, {revenu:,}€")
            
        # Analyse de cohérence
        print(f"\n=== ANALYSE DE COHÉRENCE ===")
        
        # Vérifier le Gantt
        actif_periods = [item for item in jean_data if item['Resource'] == 'Actif']
        retraite_periods = [item for item in jean_data if item['Resource'] == 'Retraite']
        
        if actif_periods:
            fin_actif = actif_periods[0]['Finish'][:4]  # Extraire l'année
            print(f"Gantt - Fin de période active : {fin_actif}")
            
        if retraite_periods:
            debut_retraite = retraite_periods[0]['Start'][:4]  # Extraire l'année
            print(f"Gantt - Début de période retraite : {debut_retraite}")
            
        # Vérifier la transition dans les revenus
        transition_found = False
        for _, row in df_filtered.iterrows():
            if row.get('Statut Jean') == 'Retraite':
                print(f"Projection - Première année de retraite : {row['Année']}")
                transition_found = True
                break
                
        if not transition_found:
            print("❌ Aucune transition vers la retraite trouvée dans les données de projection")
            
    except Exception as e:
        print(f"❌ Erreur lors des tests : {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_real_functions()
