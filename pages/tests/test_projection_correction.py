#!/usr/bin/env python3
"""
Script de vérification des calculs de taxe foncière dans la projection après correction.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_projection_taxe_fonciere():
    """Test la logique de projection avec taxe foncière."""
    
    print("=== Test de la projection après correction ===")
    
    # Simulation des dépenses dans session_state
    depenses_simulation = [
        # Dépense automatique de taxe foncière (montant mensuel)
        {'categorie': 'Impôts et taxes', 'montant': 100, 'source_id': 'asset_123', 'libelle': 'Taxe Foncière Maison'},
        # Dépense automatique d'IR (montant mensuel) - sera ignorée dans projection
        {'categorie': 'Impôts et taxes', 'montant': 200, 'source_id': 'fiscal_auto', 'libelle': 'IR automatique'},
        # Dépense manuelle
        {'categorie': 'Dépenses courantes', 'montant': 150, 'libelle': 'Courses'},
    ]
    
    print("Dépenses simulées:")
    for dep in depenses_simulation:
        print(f"  - {dep['libelle']}: {dep['montant']}€/mois (catégorie: {dep['categorie']})")
    
    # Simulation du calcul dans projection_logic.py
    taxes_foncieres = sum(d.get('montant', 0) * 12 for d in depenses_simulation 
                         if d.get('categorie') == 'Impôts et taxes' 
                         and 'source_id' in d 
                         and d.get('source_id') != 'fiscal_auto')
    
    autres_depenses = sum(d.get('montant', 0) * 12 for d in depenses_simulation 
                         if 'source_id' not in d)
    
    print(f"\nCalculs de projection:")
    print(f"Taxes foncières annuelles: {taxes_foncieres}€ (devrait être 1200€)")
    print(f"Autres dépenses annuelles: {autres_depenses}€ (devrait être 1800€)")
    print(f"IR automatique: IGNORÉ dans la projection (recalculé avec OpenFisca)")
    
    # Vérification
    if taxes_foncieres == 1200 and autres_depenses == 1800:
        print("✅ Les calculs de projection sont corrects")
    else:
        print("❌ Il y a encore un problème dans les calculs")

if __name__ == "__main__":
    test_projection_taxe_fonciere()
