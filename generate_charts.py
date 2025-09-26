#!/usr/bin/env python3
"""
Script pour générer les graphiques de l'audit patrimonial à partir d'un fichier JSON.

Ce script prend en entrée un fichier JSON généré p    print(f"📋 DataFrame patrimoine créé avec {len(df_patrimoine)} entrées")
    
    # 0. Tableau récapitulatif
    print("📊 Génération du tableau récapitulatif...")
    fig_table = create_patrimoine_summary_table_image(actifs, passifs)
    save_matplotlib_chart(fig_table, "patrimoine_tableau_recapitulatif", output_dir, save_png)
    
    # 1. Treemap patrimoine brutla fonctionnalité de sauvegarde
de l'application Streamlit et génère automatiquement les graphiques des pages :
- "Description du patrimoine" 
- "Flux : revenus et dépenses"
- "Focus Immobilier"

Les graphiques générés sont identiques à ceux affichés dans l'interface utilisateur.

Usage:
    python generate_charts.py patrimoine_data.json
    python generate_charts.py patrimoine_data.json --tmi 41 --projection-years 15
    python generate_charts.py patrimoine_data.json --output my_charts --html

Options:
    --tmi: Taux Marginal d'Imposition (0, 11, 30, 41, 45) - défaut: 30
    --projection-years: Durée de projection en années - défaut: 10
    --output: Répertoire de sortie - défaut: charts_output
    --html: Générer aussi les fichiers HTML (PNG générés par défaut)

Output:
    - Dossier spécifié contenant tous les graphiques au format PNG et/ou HTML
    - Graphiques du patrimoine: treemap, donut, barres empilées, comparaison INSEE
    - Graphiques des flux: treemap mensuel et annuel
    - Graphiques immobiliers: waterfall cash-flow, projections, amortissement LMNP
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
import numpy as np
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt

# Import des fonctions spécifiques au projet
from core.charts import (
    create_patrimoine_brut_treemap,
    create_patrimoine_net_treemap, 
    create_patrimoine_net_donut,
    create_patrimoine_ideal_donut,
    create_patrimoine_brut_stacked_bar,
    create_patrimoine_net_stacked_bar,
    create_patrimoine_brut_composite,
    create_patrimoine_net_composite,
    create_flux_treemap_mensuel,
    create_flux_treemap_annuel
)
from core.patrimoine_logic import (
    get_patrimoine_df,
    find_associated_loans,
    calculate_loan_annual_breakdown
)
from core.patrimoine_display import create_patrimoine_comparison_chart, INSEE_PATRIMOINE_DECILES_2021, INSEE_PATRIMOINE_BRUT_DECILES_2021, create_patrimoine_summary_table_image

# Import des fonctions Focus Immobilier
from core.immobilier_charts import (
    calculate_property_metrics,
    create_waterfall_fig,
    generate_projection_data,
    create_cash_flow_projection_fig,
    create_leverage_projection_fig,
    create_amortissement_projection_fig,
    create_non_productive_waterfall_fig
)

# Import des fonctions Focus Endettement 
from core.endettement_charts import (
    generate_endettement_charts,
    calculate_endettement_metrics
)

# Import des fonctions Focus Endettement 
from core.endettement_charts import (
    generate_endettement_charts,
    calculate_endettement_metrics
)

# Trick to avoid export of plotly images as Black & White 
import plotly.io as pio
pio.templates.default = "plotly"

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
    """Crée le répertoire de sortie et les sous-répertoires s'ils n'existent pas."""
    Path(output_dir).mkdir(exist_ok=True)
    
    # Créer les sous-répertoires
    subdirs = ['patrimoine', 'flux', 'immo', 'endettement']
    for subdir in subdirs:
        Path(output_dir, subdir).mkdir(exist_ok=True)
    
    return output_dir


def save_matplotlib_chart(fig, filename, output_dir, save_png=True, subdir=None):
    """Sauvegarde une figure matplotlib en PNG."""
    if fig is None:
        print(f"⚠️  Graphique {filename} est vide, non sauvegardé.")
        return
    
    if save_png:
        try:
            if subdir:
                base_path = os.path.join(output_dir, subdir, f"{filename}.png")
            else:
                base_path = os.path.join(output_dir, f"{filename}.png")
            fig.savefig(base_path, dpi=200, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            print(f"✅ Graphique sauvegardé : {base_path}")
            # Fermer la figure pour libérer la mémoire
            plt.close(fig)
        except Exception as e:
            print(f"❌ Erreur sauvegarde matplotlib {filename}: {e}")
            plt.close(fig)


def save_chart(fig, filename, output_dir, save_png=True, save_html=True, subdir=None, width=1200, height=800, scale=2):
    """Sauvegarde un graphique en PNG et/ou HTML."""
    if fig is None:
        print(f"⚠️  Graphique {filename} est vide, non sauvegardé.")
        return
    
    if subdir:
        base_path = os.path.join(output_dir, subdir, filename)
    else:
        base_path = os.path.join(output_dir, filename)
    
    if save_png:
        try:
            # Utiliser les paramètres fournis
            if height is not None:
                fig.write_image(f"{base_path}.png", width=width, height=height, scale=scale)
            else:
                # Respecter la hauteur définie dans le layout
                fig.write_image(f"{base_path}.png", width=width, scale=scale)
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
    
    # 0. Tableau récapitulatif
    print("📊 Génération du tableau récapitulatif...")
    fig_table = create_patrimoine_summary_table_image(actifs, passifs)
    save_matplotlib_chart(fig_table, "patrimoine_tableau_recapitulatif", output_dir, save_png, subdir="patrimoine")
    
    # 1. Treemap du patrimoine brut
    fig_brut_treemap = create_patrimoine_brut_treemap(df_patrimoine)
    save_chart(fig_brut_treemap, "patrimoine_brut_treemap", output_dir, save_png, save_html, subdir="patrimoine")
    
    # 2. Treemap du patrimoine net
    fig_net_treemap = create_patrimoine_net_treemap(df_patrimoine)
    save_chart(fig_net_treemap, "patrimoine_net_treemap", output_dir, save_png, save_html, subdir="patrimoine")
    
    # 3. Donut chart patrimoine net
    fig_net_donut = create_patrimoine_net_donut(df_patrimoine)
    save_chart(fig_net_donut, "patrimoine_net_donut", output_dir, save_png, save_html, subdir="patrimoine")
    
    # 4. Donut chart répartition idéale
    fig_ideal_donut = create_patrimoine_ideal_donut()
    save_chart(fig_ideal_donut, "patrimoine_ideal_donut", output_dir, save_png, save_html, subdir="patrimoine")
    
    # 5. Barres empilées patrimoine brut
    fig_brut_bar = create_patrimoine_brut_stacked_bar(df_patrimoine)
    save_chart(fig_brut_bar, "patrimoine_brut_stacked_bar", 
               output_dir, save_png, save_html, subdir="patrimoine",
               height=200, scale=1)
    
    # 6. Barres empilées patrimoine net
    fig_net_bar = create_patrimoine_net_stacked_bar(df_patrimoine)
    save_chart(fig_net_bar, "patrimoine_net_stacked_bar", 
               output_dir, save_png, save_html, subdir="patrimoine",
               height=200, scale=1)
    
    # 7. Images composites treemap + barres empilées
    fig_brut_composite = create_patrimoine_brut_composite(df_patrimoine)
    save_chart(fig_brut_composite, "patrimoine_brut_composite", output_dir, save_png, save_html, subdir="patrimoine")
    
    fig_net_composite = create_patrimoine_net_composite(df_patrimoine)
    save_chart(fig_net_composite, "patrimoine_net_composite", output_dir, save_png, save_html, subdir="patrimoine")
    
    # 8. Graphiques de comparaison INSEE
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
        save_chart(fig_brut_comparison, "patrimoine_brut_comparison_insee", 
                   output_dir, save_png, save_html, subdir="patrimoine",
                   height=200, scale=1)
    
    if patrimoine_net > 0:
        fig_net_comparison = create_patrimoine_comparison_chart(
            patrimoine_net,
            INSEE_PATRIMOINE_DECILES_2021, 
            "Positionnement patrimoine net",
            "34, 139, 34"
        )
        save_chart(fig_net_comparison, "patrimoine_net_comparison_insee", 
                   output_dir, save_png, save_html, subdir="patrimoine",
                   height=200, scale=1)


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
            save_chart(fig_mensuel, "flux_treemap_mensuel", output_dir, save_png, save_html, subdir="flux")
            
            # 2. Treemap Annuel  
            fig_annuel = create_flux_treemap_annuel(data_treemap, total_revenus)
            save_chart(fig_annuel, "flux_treemap_annuel", output_dir, save_png, save_html, subdir="flux")
        else:
            print("⚠️  Aucune donnée de flux à afficher.")
    else:
        print("⚠️  Aucun revenu trouvé.")


def generate_focus_immobilier_charts(data, output_dir, tmi=30, projection_duration=10, save_png=True, save_html=True):
    """Génère tous les graphiques de la page 'Focus Immobilier'.
    
    Args:
        data: Données chargées depuis le fichier JSON
        output_dir: Répertoire de sortie pour les graphiques
        tmi: Taux Marginal d'Imposition en % (défaut: 30)
        projection_duration: Durée de projection en années (défaut: 10)
        save_png: Sauvegarder en format PNG
        save_html: Sauvegarder en format HTML
    """
    print("\n🏠 Génération des graphiques Focus Immobilier...")
    
    # Récupération des données
    actifs = data.get('actifs', [])
    passifs = data.get('passifs', [])
    
    # Filtrer les biens immobiliers
    productive_assets = [a for a in actifs if a.get('type') == "Immobilier productif"]
    non_productive_assets = [a for a in actifs if a.get('type') == "Immobilier de jouissance"]
    
    if not productive_assets and not non_productive_assets:
        print("⚠️  Aucun bien immobilier trouvé.")
        return
    
    # Paramètres par défaut (peuvent être ajustés via les paramètres de la fonction)
    social_tax = 17.2
    year_of_analysis = date.today().year
    
    print(f"📋 Trouvé {len(productive_assets)} biens productifs et {len(non_productive_assets)} biens de jouissance")
    
    # --- Graphiques pour les biens productifs ---
    for i, asset in enumerate(productive_assets):
        asset_name = asset.get('libelle', f'Bien_productif_{i+1}')
        print(f"📊 Génération des graphiques pour : {asset_name}")
        
        # Vérifier que les données nécessaires sont présentes
        if asset.get('loyers_mensuels') is None:
            print(f"⚠️  Données de loyers manquantes pour {asset_name}")
            continue
            
        # Calculer les métriques
        try:
            metrics = calculate_property_metrics(asset, passifs, tmi, social_tax, year_of_analysis)
            
            # 1. Graphique en cascade cash-flow
            is_lmnp = asset.get('mode_exploitation') == 'Location Meublée'
            fig_waterfall = create_waterfall_fig(metrics, year_of_analysis, is_lmnp=is_lmnp)
            filename = f"immobilier_{i+1}_{asset_name.replace(' ', '_')}_waterfall_{year_of_analysis}"
            save_chart(fig_waterfall, filename, output_dir, save_png, save_html, subdir="immo")
            
            # 2. Graphiques de projection
            loans = find_associated_loans(asset.get('id'), passifs)
            df_projection = generate_projection_data(asset, loans, tmi, social_tax, projection_duration)
            
            if not df_projection.empty:
                # 2a. Projection cash-flow
                fig_cash_flow = create_cash_flow_projection_fig(df_projection)
                filename = f"immobilier_{i+1}_{asset_name.replace(' ', '_')}_cash_flow_projection"
                save_chart(fig_cash_flow, filename, output_dir, save_png, save_html, subdir="immo")
                
                # 2b. Projection effet de levier
                fig_leverage = create_leverage_projection_fig(df_projection)
                filename = f"immobilier_{i+1}_{asset_name.replace(' ', '_')}_leverage_projection"
                save_chart(fig_leverage, filename, output_dir, save_png, save_html, subdir="immo")
                
                # 2c. Projection amortissement (seulement pour LMNP)
                if is_lmnp:
                    fig_amortissement = create_amortissement_projection_fig(df_projection)
                    filename = f"immobilier_{i+1}_{asset_name.replace(' ', '_')}_amortissement_projection"
                    save_chart(fig_amortissement, filename, output_dir, save_png, save_html, subdir="immo")
            
        except Exception as e:
            print(f"❌ Erreur lors de la génération des graphiques pour {asset_name}: {e}")
    
    # --- Graphiques pour les biens de jouissance ---
    for i, asset in enumerate(non_productive_assets):
        asset_name = asset.get('libelle', f'Bien_jouissance_{i+1}')
        print(f"📊 Génération du graphique pour : {asset_name}")
        
        try:
            # Graphique en cascade pour le coût de possession
            fig_non_productive = create_non_productive_waterfall_fig(asset, passifs, year_of_analysis)
            filename = f"immobilier_jouissance_{i+1}_{asset_name.replace(' ', '_')}_waterfall_{year_of_analysis}"
            save_chart(fig_non_productive, filename, output_dir, save_png, save_html, subdir="immo")
            
        except Exception as e:
            print(f"❌ Erreur lors de la génération du graphique pour {asset_name}: {e}")
    
    print(f"✅ Génération des graphiques Focus Immobilier terminée")


def generate_focus_endettement_charts(data, output_dir, max_debt_ratio=35, save_png=True, save_html=True):
    """Génère tous les graphiques de la page 'Focus Endettement'."""
    print("\n🏦 Génération des graphiques Focus Endettement...")
    
    # Récupération des données
    revenus = data.get('revenus', [])
    passifs = data.get('passifs', [])
    
    if not revenus and not passifs:
        print("⚠️  Aucune donnée de revenus ou passifs trouvée pour l'endettement.")
        return
    
    print(f"📋 Trouvé {len(revenus)} revenus et {len(passifs)} passifs")
    
    try:
        # Génération des graphiques d'endettement
        charts = generate_endettement_charts(revenus, passifs, max_debt_ratio)
        
        # Sauvegarde de la jauge d'endettement
        if charts['gauge_chart']:
            filename = f"endettement_jauge_taux_{max_debt_ratio}pct"
            save_chart(charts['gauge_chart'], filename, output_dir, save_png, save_html, subdir="endettement")
        
        # Sauvegarde du graphique de répartition
        if charts['breakdown_chart']:
            filename = f"endettement_repartition_prets_{max_debt_ratio}pct"
            save_chart(charts['breakdown_chart'], filename, output_dir, save_png, save_html, subdir="endettement", height=200, scale=1)
        
        # Afficher quelques métriques de résumé
        metrics = charts['metrics']
        print(f"💰 Revenus pondérés: {metrics['weighted_income']:,.2f} €/mois")
        print(f"💳 Charges de prêts: {metrics['current_debt']:,.2f} €/mois")
        print(f"📊 Taux d'endettement: {metrics['current_debt_ratio_pct']:.2f}%")
        print(f"🎯 Capacité restante: {metrics['remaining_capacity']:,.2f} €/mois")
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération des graphiques d'endettement: {e}")
    
    print("✅ Génération des graphiques Focus Endettement terminée")


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
        "--html",
        action="store_true",
        help="Générer aussi en format HTML (PNG généré par défaut)"
    )
    parser.add_argument(
        "--tmi",
        type=int,
        choices=[0, 11, 30, 41, 45],
        default=30,
        help="Taux Marginal d'Imposition en pourcentage (défaut: 30)"
    )
    parser.add_argument(
        "--projection-years",
        type=int,
        default=10,
        help="Durée de projection en années pour les graphiques immobiliers (défaut: 10)"
    )
    parser.add_argument(
        "--max-debt-ratio",
        type=int,
        choices=[35, 40],
        default=35,
        help="Taux d'endettement maximum en pourcentage pour les graphiques d'endettement (défaut: 35)"
    )
    
    args = parser.parse_args()
    
    # Vérifications
    if not os.path.exists(args.json_file):
        print(f"❌ Fichier {args.json_file} introuvable.")
        sys.exit(1)
    
    # Configuration formats de sortie
    save_png = True  # PNG toujours généré par défaut
    save_html = args.html  # HTML optionnel
    
    # Plus besoin de vérification car PNG est toujours généré
    
    print(f"🚀 Début de la génération des graphiques...")
    print(f"📁 Fichier source: {args.json_file}")
    print(f"📁 Répertoire de sortie: {args.output}")
    print(f"🖼️  Formats: PNG{'+ HTML' if save_html else ''}")
    print(f"🏦 TMI: {args.tmi}%")
    print(f"📅 Projection: {args.projection_years} ans")
    print(f"💳 Taux d'endettement max: {args.max_debt_ratio}%")
    
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
        
        # Graphiques Focus Immobilier
        generate_focus_immobilier_charts(data, output_dir, args.tmi, args.projection_years, save_png, save_html)
        
        # Graphiques Focus Endettement
        generate_focus_endettement_charts(data, output_dir, args.max_debt_ratio, save_png, save_html)
        
        print(f"\n🎉 Génération terminée avec succès !")
        print(f"📁 Tous les graphiques sont disponibles dans : {os.path.abspath(output_dir)}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()