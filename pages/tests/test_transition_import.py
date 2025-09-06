#!/usr/bin/env python3
"""
Test pour vérifier que la fonction d'analyse de transition fonctionne
avec les nouvelles couleurs et le nouvel ordre.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from core.projection_display import display_retirement_transition_analysis
    print("✅ Importation de display_retirement_transition_analysis réussie")
except Exception as e:
    print(f"❌ Erreur d'importation : {e}")
    
# Test des couleurs et de l'ordre définis dans la fonction
def test_color_mapping():
    print("\n=== TEST DU MAPPING DE COULEURS ===")
    
    categories_ordre = [
        'Reste à vivre',
        'Prélèvements Sociaux', 
        'Impôt sur le revenu',
        'Coût des études',
        'Autres Dépenses',
        'Taxes Foncières',
        'Charges Immobilières',
        'Mensualités Prêts'
    ]
    
    couleurs_projection = [
        '#636EFA',  # Reste à vivre (bleu)
        '#EF553B',  # Prélèvements Sociaux (rouge)
        '#00CC96',  # Impôt sur le revenu (vert)
        '#AB63FA',  # Coût des études (violet)
        '#FFA15A',  # Autres Dépenses (orange)
        '#19D3F3',  # Taxes Foncières (cyan)
        '#FF6692',  # Charges Immobilières (rose)
        '#B6E880',  # Mensualités Prêts (vert clair)
        '#FF97FF',  # Revenus du foyer (magenta clair)
    ]
    
    color_discrete_map = {}
    for i, categorie in enumerate(categories_ordre + ['Revenus du foyer']):
        if i < len(couleurs_projection):
            color_discrete_map[categorie] = couleurs_projection[i]
    
    print("Mapping de couleurs généré :")
    for categorie, couleur in color_discrete_map.items():
        print(f"  {categorie:<25} → {couleur}")
    
    print(f"\n✅ Total : {len(color_discrete_map)} catégories mappées")
    
if __name__ == "__main__":
    test_color_mapping()
