#!/usr/bin/env python3
"""
Script de démonstration pour tester le calcul automatique de l'impôt sur le revenu 
dans la page Flux.

Ce script simule un foyer avec des revenus et montre comment l'IR est calculé.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from datetime import date
from core.fiscal_logic import calculate_monthly_income_tax, calculate_simple_income_tax_monthly

def test_ir_calculation():
    """Test le calcul de l'impôt sur le revenu mensuel."""
    
    # Simulation d'un foyer dans session_state
    st.session_state.parents = [
        {'prenom': 'Jean', 'date_naissance': date(1980, 5, 15)},
        {'prenom': 'Marie', 'date_naissance': date(1982, 3, 20)}
    ]
    
    st.session_state.enfants = [
        {'prenom': 'Lucas', 'date_naissance': date(2010, 9, 12)},
        {'prenom': 'Emma', 'date_naissance': date(2012, 7, 8)}
    ]
    
    st.session_state.revenus = [
        {'type': 'Salaire', 'libelle': 'Salaire Jean', 'montant': 4000},
        {'type': 'Salaire', 'libelle': 'Salaire Marie', 'montant': 3500},
    ]
    
    st.session_state.actifs = []
    st.session_state.passifs = []
    
    # Test du calcul
    print("=== Test du calcul de l'IR ===")
    print(f"Revenus Jean: 4000€/mois (48000€/an)")
    print(f"Revenus Marie: 3500€/mois (42000€/an)")
    print(f"Total revenus: 7500€/mois (90000€/an)")
    print(f"Composition familiale: 2 parents + 2 enfants")
    
    try:
        ir_mensuel = calculate_monthly_income_tax()
        print(f"IR mensuel calculé: {ir_mensuel}€")
        print(f"IR annuel estimé: {ir_mensuel * 12}€")
    except Exception as e:
        print(f"Erreur lors du calcul avec OpenFisca: {e}")
        print("Utilisation du calcul simplifié...")
        ir_mensuel_simple = calculate_simple_income_tax_monthly()
        print(f"IR mensuel (calcul simplifié): {ir_mensuel_simple}€")
        print(f"IR annuel estimé (calcul simplifié): {ir_mensuel_simple * 12}€")

if __name__ == "__main__":
    test_ir_calculation()
