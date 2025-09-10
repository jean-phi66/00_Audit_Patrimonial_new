#!/usr/bin/env python3
"""
Script de vérification des calculs de taxe foncière dans la projection.
Ce script aide à identifier où se situe le problème de multiplication par 12.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_taxe_fonciere_calculation():
    """Test les calculs de taxe foncière."""
    
    print("=== Test des calculs de taxe foncière ===")
    
    # Simulation d'un bien immobilier avec taxe foncière de 1200€/an
    taxe_fonciere_annuelle = 1200
    print(f"Taxe foncière annuelle (saisie): {taxe_fonciere_annuelle}€")
    
    # Étape 1: Conversion en mensuel dans flux_logic.py
    taxe_fonciere_mensuelle = taxe_fonciere_annuelle / 12
    print(f"Taxe foncière mensuelle (flux_logic): {taxe_fonciere_mensuelle}€")
    
    # Étape 2: Reconversion en annuel dans projection_logic.py
    taxe_fonciere_annuelle_recalculee = taxe_fonciere_mensuelle * 12
    print(f"Taxe foncière annuelle (projection_logic): {taxe_fonciere_annuelle_recalculee}€")
    
    # Vérification
    if taxe_fonciere_annuelle == taxe_fonciere_annuelle_recalculee:
        print("✅ Les calculs sont cohérents")
    else:
        print("❌ Il y a une incohérence dans les calculs")
        print(f"Différence: {taxe_fonciere_annuelle_recalculee - taxe_fonciere_annuelle}€")

    print("\n=== Vérification du contexte ===")
    print("1. Dans asset_display.py: Saisie en 'Taxe foncière annuelle (€)'")
    print("2. Dans flux_logic.py: Division par 12 pour le mensuel")
    print("3. Dans projection_logic.py: Multiplication par 12 pour l'annuel")
    print("\nLe problème pourrait être:")
    print("- Une saisie en mensuel au lieu d'annuel")
    print("- Une double comptabilisation quelque part")
    print("- Un affichage incorrect des résultats")

if __name__ == "__main__":
    test_taxe_fonciere_calculation()
