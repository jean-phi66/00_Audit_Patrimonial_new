#!/usr/bin/env python3
"""
Script pour générer les graphiques de l'audit patrimonial à partir d'un fichier JSON.

Ce script prend en entrée un fichier JSON généré par la fonctionnalité de sauvegarde
de l'application Streamlit et génère automatiquement les graphiques des pages :
- "Description du patrimoine" 
- "Flux : revenus et dépenses"

Les graphiques générés sont identiques à ceux affichés dans l'interface utilisateur.

Usage:
    python generate_charts.py patrimoine_data.json

Output:
    - Dossier 'charts_output/' contenant tous les graphiques au format PNG et HTML
"""

import argparse
import json
import os
import sys
from datetime import date, datetime
from pathlib import Path

# Ajouter le répertoire du projet au chemin Python
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Imports des modules du projet
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Import des fonctions spécifiques au projet
from core.charts import (
    create_patrimoine_brut_treemap,
    create_patrimoine_net_treemap, 
    create_patrimoine_net_donut,
    create_patrimoine_ideal_donut,
    create_patrimoine_brut_stacked_bar,
    create_patrimoine_net_stacked_bar,
    create_flux_treemap_mensuel,
    create_flux_treemap_annuel
)
from core.patrimoine_logic import get_patrimoine_df
from core.patrimoine_display import create_patrimoine_comparison_chart, INSEE_PATRIMOINE_DECILES_2021, INSEE_PATRIMOINE_BRUT_DECILES_2021


def json_decoder_hook(obj):
    """Décodeur JSON personnalisé pour reconstruire les objets date."""
    if '_type' in obj:
        if obj['_type'] == 'date':
            return datetime.fromisoformat(obj['value']).date()
        elif obj['_type'] == 'MarginalRateTaxScale':
            # Pour les objets OpenFisca non sérialisables, on retourne None
            return None
    return obj


def load_data_from_json(json_file_path):
    """Charge les données depuis un fichier JSON."""
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f, object_hook=json_decoder_hook)
        return data
    except Exception as e:
        print(f"Erreur lors du chargement du fichier JSON : {e}")
        sys.exit(1)


def create_output_directory(output_dir="charts_output"):
    """Crée le répertoire de sortie s'il n'existe pas."""
    Path(output_dir).mkdir(exist_ok=True)
    return output_dir


def save_chart(fig, filename, output_dir, save_png=True, save_html=True):
    """Sauvegarde un graphique en PNG et/ou HTML."""
    if fig is None:
        print(f"⚠️  Graphique {filename} est vide, non sauvegardé.")
        return
    
    base_path = os.path.join(output_dir, filename)
    
    if save_png:
        try:
            fig.write_image(f"{base_path}.png", width=1200, height=800, scale=2)
            print(f"✅ Graphique sauvegardé : {base_path}.png")
        except Exception as e:
            print(f"❌ Erreur sauvegarde PNG {filename}: {e}")
    
    if save_html:
        try:
            fig.write_html(f"{base_path}.html")
            print(f"✅ Graphique sauvegardé : {base_path}.html")
        except Exception as e:
            print(f"❌ Erreur sauvegarde HTML {filename}: {e}")


def generate_patrimoine_charts(data, output_dir, save_png=True, save_html=True):
    """Génère tous les graphiques de la page 'Description du patrimoine'."""
    print("\n📊 Génération des graphiques du patrimoine...")
    
    # Récupération des données
    actifs = data.get('actifs', [])
    passifs = data.get('passifs', [])
    
    if not actifs and not passifs:
        print("⚠️  Aucune donnée de patrimoine trouvée.")
        return
    
    # Création du DataFrame patrimoine
    df_patrimoine = get_patrimoine_df(actifs, passifs)
    
    if df_patrimoine.empty:
        print("⚠️  DataFrame patrimoine vide.")
        return
    
    print(f"📋 DataFrame patrimoine créé avec {len(df_patrimoine)} entrées")
    
    # 1. Treemap du patrimoine brut
    fig_brut_treemap = create_patrimoine_brut_treemap(df_patrimoine)
    save_chart(fig_brut_treemap, "patrimoine_brut_treemap", output_dir, save_png, save_html)
    
    # 2. Treemap du patrimoine net
    fig_net_treemap = create_patrimoine_net_treemap(df_patrimoine)
    save_chart(fig_net_treemap, "patrimoine_net_treemap", output_dir, save_png, save_html)
    
    # 3. Donut chart patrimoine net
    fig_net_donut = create_patrimoine_net_donut(df_patrimoine)
    save_chart(fig_net_donut, "patrimoine_net_donut", output_dir, save_png, save_html)
    
    # 4. Donut chart répartition idéale
    fig_ideal_donut = create_patrimoine_ideal_donut()
    save_chart(fig_ideal_donut, "patrimoine_ideal_donut", output_dir, save_png, save_html)
    
    # 5. Barres empilées patrimoine brut
    fig_brut_bar = create_patrimoine_brut_stacked_bar(df_patrimoine)
    save_chart(fig_brut_bar, "patrimoine_brut_stacked_bar", output_dir, save_png, save_html)
    
    # 6. Barres empilées patrimoine net
    fig_net_bar = create_patrimoine_net_stacked_bar(df_patrimoine)
    save_chart(fig_net_bar, "patrimoine_net_stacked_bar", output_dir, save_png, save_html)
    
    # 7. Graphiques de comparaison INSEE
    total_actifs = sum(a.get('valeur', 0.0) for a in actifs)
    total_passifs = sum(p.get('crd_calcule', 0.0) for p in passifs)
    patrimoine_net = total_actifs - total_passifs
    
    if total_actifs > 0:
        fig_brut_comparison = create_patrimoine_comparison_chart(
            total_actifs, 
            INSEE_PATRIMOINE_BRUT_DECILES_2021,
            "Positionnement patrimoine brut",
            "255, 140, 0"
        )
        save_chart(fig_brut_comparison, "patrimoine_brut_comparison_insee", output_dir, save_png, save_html)
    
    if patrimoine_net > 0:
        fig_net_comparison = create_patrimoine_comparison_chart(
            patrimoine_net,
            INSEE_PATRIMOINE_DECILES_2021, 
            "Positionnement patrimoine net",
            "34, 139, 34"
        )
        save_chart(fig_net_comparison, "patrimoine_net_comparison_insee", output_dir, save_png, save_html)


def generate_flux_charts(data, output_dir, save_png=True, save_html=True):
    """Génère tous les graphiques de la page 'Flux : revenus et dépenses'."""
    print("\n💸 Génération des graphiques des flux...")
    
    # Récupération des données
    revenus = data.get('revenus', [])
    depenses = data.get('depenses', [])
    
    if not revenus and not depenses:
        print("⚠️  Aucune donnée de flux trouvée.")
        return
    
    # Calcul des totaux
    total_revenus = sum(r.get('montant', 0.0) for r in revenus)
    total_depenses = sum(d.get('montant', 0.0) for d in depenses)
    capacite_epargne = total_revenus - total_depenses
    
    print(f"💰 Total revenus: {total_revenus:,.2f} €")
    print(f"💸 Total dépenses: {total_depenses:,.2f} €")
    print(f"💎 Capacité d'épargne: {capacite_epargne:,.2f} €")
    
    if total_revenus > 0:
        # Préparation des données pour le treemap (même logique que dans flux_display.py)
        df_depenses = pd.DataFrame(depenses)
        data_treemap = []
        
        if not df_depenses.empty and df_depenses['montant'].sum() > 0:
            # Regrouper les dépenses par catégorie
            depenses_par_cat = df_depenses.groupby('categorie')['montant'].sum().reset_index()
            depenses_par_cat.rename(columns={'categorie': 'label'}, inplace=True)
            data_treemap = depenses_par_cat.to_dict('records')
        
        # Ajouter le reste à vivre s'il est positif
        if capacite_epargne > 0:
            data_treemap.append({'label': 'Reste à vivre', 'montant': capacite_epargne})
        
        # Utilisation des fonctions réutilisables du module charts
        if data_treemap:
            # 1. Treemap Mensuel
            fig_mensuel = create_flux_treemap_mensuel(data_treemap, total_revenus)
            save_chart(fig_mensuel, "flux_treemap_mensuel", output_dir, save_png, save_html)
            
            # 2. Treemap Annuel  
            fig_annuel = create_flux_treemap_annuel(data_treemap, total_revenus)
            save_chart(fig_annuel, "flux_treemap_annuel", output_dir, save_png, save_html)
        else:
            print("⚠️  Aucune donnée de flux à afficher.")
    else:
        print("⚠️  Aucun revenu trouvé.")


def main():
    """Fonction principale du script."""
    parser = argparse.ArgumentParser(
        description="Génère les graphiques de l'audit patrimonial à partir d'un fichier JSON"
    )
    parser.add_argument(
        "json_file", 
        help="Chemin vers le fichier JSON contenant les données"
    )
    parser.add_argument(
        "--output", "-o",
        default="charts_output",
        help="Répertoire de sortie pour les graphiques (défaut: charts_output)"
    )
    parser.add_argument(
        "--no-png",
        action="store_true",
        help="Ne pas sauvegarder en format PNG"
    )
    parser.add_argument(
        "--no-html", 
        action="store_true",
        help="Ne pas sauvegarder en format HTML"
    )
    
    args = parser.parse_args()
    
    # Vérifications
    if not os.path.exists(args.json_file):
        print(f"❌ Fichier {args.json_file} introuvable.")
        sys.exit(1)
    
    # Configuration formats de sortie
    save_png = not args.no_png
    save_html = not args.no_html
    
    if not save_png and not save_html:
        print("❌ Au moins un format de sortie doit être sélectionné.")
        sys.exit(1)
    
    print(f"🚀 Début de la génération des graphiques...")
    print(f"📁 Fichier source: {args.json_file}")
    print(f"📁 Répertoire de sortie: {args.output}")
    print(f"🖼️  Formats: {'PNG ' if save_png else ''}{'HTML' if save_html else ''}")
    
    # Chargement des données
    data = load_data_from_json(args.json_file)
    print(f"✅ Données chargées avec succès")
    
    # Création du répertoire de sortie
    output_dir = create_output_directory(args.output)
    
    # Génération des graphiques
    try:
        # Graphiques du patrimoine
        generate_patrimoine_charts(data, output_dir, save_png, save_html)
        
        # Graphiques des flux
        generate_flux_charts(data, output_dir, save_png, save_html)
        
        print(f"\n🎉 Génération terminée avec succès !")
        print(f"📁 Tous les graphiques sont disponibles dans : {os.path.abspath(output_dir)}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()