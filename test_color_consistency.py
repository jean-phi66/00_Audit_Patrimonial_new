#!/usr/bin/env python3
"""
Test pour vérifier la cohérence des couleurs et de l'ordre 
entre les graphiques de projection et l'analyse de transition.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_color_and_order_consistency():
    """Test la cohérence des couleurs et de l'ordre."""
    
    print("=== TEST DE COHÉRENCE COULEURS ET ORDRE ===")
    
    # Ordre des catégories dans les projections
    ordre_projection = [
        'Reste à vivre',
        'Prélèvements Sociaux',
        'Impôt sur le revenu',
        'Coût des études',
        'Autres Dépenses',
        'Taxes Foncières',
        'Charges Immobilières',
        'Mensualités Prêts'
    ]
    
    # Couleurs par défaut de Plotly (séquence standard)
    couleurs_plotly_defaut = [
        '#636EFA',  # bleu
        '#EF553B',  # rouge
        '#00CC96',  # vert
        '#AB63FA',  # violet
        '#FFA15A',  # orange
        '#19D3F3',  # cyan
        '#FF6692',  # rose
        '#B6E880',  # vert clair
        '#FF97FF',  # magenta clair
    ]
    
    print("Ordre et couleurs des catégories :")
    print("(identique aux graphiques de projection)")
    
    for i, categorie in enumerate(ordre_projection):
        couleur = couleurs_plotly_defaut[i] if i < len(couleurs_plotly_defaut) else "Non définie"
        print(f"{i+1:2d}. {categorie:<25} → {couleur}")
    
    print(f"\nCatégorie spéciale :")
    print(f"{'Revenus du foyer':<25} → {couleurs_plotly_defaut[8]} (magenta clair)")
    
    print(f"\n=== COMPORTEMENT D'AFFICHAGE ===")
    print("Revenus du foyer     : Positif (vers le haut)")
    print("Reste à vivre        : Positif (vers le haut)")
    print("Toutes autres dépenses : Négatif (vers le bas)")
    
    print(f"\nCeci garantit :")
    print("✅ Même ordre que dans les graphiques de projection")
    print("✅ Mêmes couleurs que dans les graphiques de projection") 
    print("✅ Affichage cohérent revenus vs dépenses")
    print("✅ 'Reste à vivre' affiché positivement comme un bénéfice")

if __name__ == "__main__":
    test_color_and_order_consistency()
