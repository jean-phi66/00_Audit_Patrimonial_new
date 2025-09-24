#!/usr/bin/env python3
"""
Script de démonstration pour le générateur de graphiques.

Ce script montre différentes utilisations du générateur de graphiques
avec des données d'exemple variées.
"""

import os
import subprocess
import json
from datetime import date

def create_sample_data():
    """Crée des données d'exemple plus complètes pour la démonstration."""
    sample_data = {
        "parents": [
            {
                "prenom": "Alexandre",
                "date_naissance": {"_type": "date", "value": "1975-03-20"}
            },
            {
                "prenom": "Isabelle", 
                "date_naissance": {"_type": "date", "value": "1978-09-15"}
            }
        ],
        "enfants": [
            {
                "prenom": "Thomas",
                "date_naissance": {"_type": "date", "value": "2008-06-12"},
                "garde_alternee": False
            },
            {
                "prenom": "Emma",
                "date_naissance": {"_type": "date", "value": "2011-01-25"},
                "garde_alternee": False
            },
            {
                "prenom": "Lucas",
                "date_naissance": {"_type": "date", "value": "2014-11-08"},
                "garde_alternee": False
            }
        ],
        "actifs": [
            {
                "id": "maison_principale",
                "libelle": "Maison familiale",
                "type": "Immobilier de jouissance",
                "valeur": 450000.0,
                "charges": 300.0,
                "taxe_fonciere": 1800.0,
                "loyer": 0.0
            },
            {
                "id": "appartement_paris",
                "libelle": "Studio Paris 11ème",
                "type": "Immobilier productif", 
                "valeur": 320000.0,
                "charges": 180.0,
                "taxe_fonciere": 1200.0,
                "loyer": 1400.0
            },
            {
                "id": "maison_secondaire",
                "libelle": "Maison secondaire Bretagne",
                "type": "Immobilier de jouissance",
                "valeur": 180000.0,
                "charges": 100.0,
                "taxe_fonciere": 600.0,
                "loyer": 0.0
            },
            {
                "id": "livret_a",
                "libelle": "Livret A",
                "type": "Actifs financiers",
                "valeur": 22950.0,
                "charges": 0.0,
                "taxe_fonciere": 0.0,
                "loyer": 0.0
            },
            {
                "id": "pea_alexandre", 
                "libelle": "PEA Alexandre",
                "type": "Actifs financiers",
                "valeur": 67500.0,
                "charges": 0.0,
                "taxe_fonciere": 0.0,
                "loyer": 0.0
            },
            {
                "id": "pea_isabelle",
                "libelle": "PEA Isabelle",
                "type": "Actifs financiers",
                "valeur": 54200.0,
                "charges": 0.0,
                "taxe_fonciere": 0.0,
                "loyer": 0.0
            },
            {
                "id": "av_alexandre",
                "libelle": "Assurance vie Alexandre",
                "type": "Actifs financiers",
                "valeur": 125000.0,
                "charges": 0.0,
                "taxe_fonciere": 0.0,
                "loyer": 0.0
            },
            {
                "id": "av_isabelle",
                "libelle": "Assurance vie Isabelle", 
                "type": "Actifs financiers",
                "valeur": 89000.0,
                "charges": 0.0,
                "taxe_fonciere": 0.0,
                "loyer": 0.0
            },
            {
                "id": "voiture_1",
                "libelle": "Voiture familiale",
                "type": "Autres actifs",
                "valeur": 18000.0,
                "charges": 0.0,
                "taxe_fonciere": 0.0,
                "loyer": 0.0
            },
            {
                "id": "voiture_2",
                "libelle": "Voiture citadine",
                "type": "Autres actifs", 
                "valeur": 12000.0,
                "charges": 0.0,
                "taxe_fonciere": 0.0,
                "loyer": 0.0
            }
        ],
        "passifs": [
            {
                "id": "pret_maison",
                "libelle": "Prêt maison principale",
                "montant_initial": 360000.0,
                "taux_annuel": 1.3,
                "duree_mois": 300,
                "date_debut": {"_type": "date", "value": "2019-03-01"},
                "crd_calcule": 285000.0
            },
            {
                "id": "pret_paris",
                "libelle": "Prêt studio Paris",
                "montant_initial": 250000.0,
                "taux_annuel": 1.7,
                "duree_mois": 300,
                "date_debut": {"_type": "date", "value": "2021-09-01"},
                "crd_calcule": 210000.0
            }
        ],
        "revenus": [
            {
                "id": "salaire_alexandre",
                "libelle": "Salaire Alexandre",
                "montant": 5800.0,
                "type": "Salaire"
            },
            {
                "id": "salaire_isabelle", 
                "libelle": "Salaire Isabelle",
                "montant": 4200.0,
                "type": "Salaire"
            },
            {
                "id": "loyer_paris",
                "libelle": "Loyer studio Paris",
                "montant": 1400.0,
                "type": "Patrimoine",
                "source_id": "appartement_paris"
            },
            {
                "id": "prime_alexandre",
                "libelle": "Prime trimestrielle Alexandre",
                "montant": 750.0,
                "type": "Autre"
            },
            {
                "id": "dividendes",
                "libelle": "Dividendes actions",
                "montant": 200.0,
                "type": "Patrimoine"
            }
        ],
        "depenses": [
            {
                "id": "mensualite_maison",
                "libelle": "Mensualité prêt maison",
                "montant": 1380.0,
                "categorie": "Logement",
                "source_id": "pret_maison"
            },
            {
                "id": "mensualite_paris",
                "libelle": "Mensualité prêt Paris",
                "montant": 980.0,
                "categorie": "Logement", 
                "source_id": "pret_paris"
            },
            {
                "id": "charges_maison",
                "libelle": "Charges maison",
                "montant": 300.0,
                "categorie": "Logement",
                "source_id": "maison_principale"
            },
            {
                "id": "charges_paris",
                "libelle": "Charges studio Paris",
                "montant": 180.0,
                "categorie": "Logement",
                "source_id": "appartement_paris"
            },
            {
                "id": "charges_bretagne",
                "libelle": "Charges maison Bretagne",
                "montant": 100.0,
                "categorie": "Logement", 
                "source_id": "maison_secondaire"
            },
            {
                "id": "taxe_maison",
                "libelle": "Taxe foncière maison",
                "montant": 150.0,
                "categorie": "Impôts et taxes",
                "source_id": "maison_principale"
            },
            {
                "id": "taxe_paris",
                "libelle": "Taxe foncière Paris",
                "montant": 100.0,
                "categorie": "Impôts et taxes",
                "source_id": "appartement_paris"
            },
            {
                "id": "taxe_bretagne", 
                "libelle": "Taxe foncière Bretagne",
                "montant": 50.0,
                "categorie": "Impôts et taxes",
                "source_id": "maison_secondaire"
            },
            {
                "id": "alimentation",
                "libelle": "Alimentation",
                "montant": 1200.0,
                "categorie": "Dépenses courantes"
            },
            {
                "id": "transport",
                "libelle": "Transport (essence, péage, etc.)",
                "montant": 600.0,
                "categorie": "Transport"
            },
            {
                "id": "assurances",
                "libelle": "Assurances (auto, habitation, etc.)",
                "montant": 350.0,
                "categorie": "Assurances"
            },
            {
                "id": "loisirs",
                "libelle": "Loisirs et sorties",
                "montant": 500.0,
                "categorie": "Loisirs"
            },
            {
                "id": "enfants",
                "libelle": "Frais enfants (école, activités)",
                "montant": 800.0,
                "categorie": "Enfants"
            },
            {
                "id": "sante",
                "libelle": "Santé (mutuelle, médecins)",
                "montant": 200.0,
                "categorie": "Santé"
            },
            {
                "id": "impot_revenu",
                "libelle": "Impôt sur le revenu",
                "montant": 1100.0,
                "categorie": "Impôts et taxes"
            },
            {
                "id": "epargne_pension",
                "libelle": "Épargne retraite (PER)",
                "montant": 400.0,
                "categorie": "Épargne"
            }
        ],
        "projection_settings": {},
        "reorganisation_data": [],
        "epargne_precaution": 0.0,
        "reserve_projet": 0.0,
        "per_input_parameters": {},
        "scpi_credit_parameters": {}
    }
    
    return sample_data

def run_demo():
    """Lance la démonstration complète."""
    print("🚀 Démonstration du générateur de graphiques")
    print("=" * 50)
    
    # 1. Créer les données d'exemple avancées
    print("\n📋 Création des données d'exemple avancées...")
    sample_data = create_sample_data()
    
    # Sauvegarder les données
    demo_file = "demo_data.json"
    with open(demo_file, 'w', encoding='utf-8') as f:
        json.dump(sample_data, f, indent=2, ensure_ascii=False)
    print(f"✅ Données sauvegardées dans {demo_file}")
    
    # Afficher un résumé des données
    print("\n📊 Résumé des données :")
    total_actifs = sum(a['valeur'] for a in sample_data['actifs'])
    total_passifs = sum(p['crd_calcule'] for p in sample_data['passifs'])
    patrimoine_net = total_actifs - total_passifs
    
    total_revenus = sum(r['montant'] for r in sample_data['revenus'])
    total_depenses = sum(d['montant'] for d in sample_data['depenses'])
    capacite_epargne = total_revenus - total_depenses
    
    print(f"   👥 Foyer: {len(sample_data['parents'])} parents, {len(sample_data['enfants'])} enfants")
    print(f"   🏠 Patrimoine: {total_actifs:,.0f} € (actifs) - {total_passifs:,.0f} € (passifs) = {patrimoine_net:,.0f} € (net)")
    print(f"   💰 Flux: {total_revenus:,.0f} € (revenus) - {total_depenses:,.0f} € (dépenses) = {capacite_epargne:,.0f} € (épargne)")
    
    # 2. Test 1: Génération complète (PNG + HTML)
    print(f"\n🎯 Test 1: Génération complète (PNG + HTML)")
    result = subprocess.run([
        'python', 'generate_charts.py', demo_file, '--output', 'demo_complete'
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Génération complète réussie")
        file_count = len([f for f in os.listdir('demo_complete') if f.endswith(('.png', '.html'))])
        print(f"   📁 {file_count} fichiers générés dans demo_complete/")
    else:
        print(f"❌ Erreur: {result.stderr}")
    
    # 3. Test 2: PNG seulement
    print(f"\n🎯 Test 2: PNG seulement")
    result = subprocess.run([
        'python', 'generate_charts.py', demo_file, '--output', 'demo_png', '--no-html'
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Génération PNG réussie")
        png_count = len([f for f in os.listdir('demo_png') if f.endswith('.png')])
        print(f"   🖼️ {png_count} fichiers PNG générés dans demo_png/")
    else:
        print(f"❌ Erreur: {result.stderr}")
    
    # 4. Test 3: HTML seulement  
    print(f"\n🎯 Test 3: HTML seulement")
    result = subprocess.run([
        'python', 'generate_charts.py', demo_file, '--output', 'demo_html', '--no-png'
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Génération HTML réussie")
        html_count = len([f for f in os.listdir('demo_html') if f.endswith('.html')])
        print(f"   🌐 {html_count} fichiers HTML générés dans demo_html/")
    else:
        print(f"❌ Erreur: {result.stderr}")
    
    # 5. Résumé final
    print(f"\n🎉 Démonstration terminée !")
    print(f"📁 Résultats disponibles dans :")
    print(f"   • demo_complete/ : Tous formats (PNG + HTML)")
    print(f"   • demo_png/ : PNG seulement") 
    print(f"   • demo_html/ : HTML seulement")
    print(f"\n📖 Consultez README_CHARTS.md pour plus d'informations")

if __name__ == "__main__":
    run_demo()