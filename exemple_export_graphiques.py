#!/usr/bin/env python3
"""
Exemple d'utilisation de la fonctionnalité d'export des graphiques.
Ce script montre comment utiliser les exporteurs sans interface Streamlit.
"""

import sys
from pathlib import Path
from datetime import datetime

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent))

from core.simple_chart_exporter import SimpleChartExporter

def export_for_presentation():
    """
    Export des graphiques pour une présentation.
    Génère des graphiques standardisés dans un répertoire spécifique.
    """
    
    print("🎨 Export pour présentation...")
    
    # Créer un répertoire daté
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    export_dir = f"presentation_charts_{timestamp}"
    
    exporter = SimpleChartExporter(export_dir)
    
    # Exporter les graphiques
    results = exporter.export_sample_charts()
    
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    print(f"✅ {len(successful)} graphiques exportés dans {export_dir}/")
    
    if failed:
        print(f"❌ {len(failed)} échecs:")
        for result in failed:
            print(f"   - {result['title']}: {result.get('error', 'Erreur inconnue')}")
    
    return export_dir, successful

def analyze_app_structure():
    """
    Analyse de la structure de l'application pour identifier les graphiques.
    """
    
    print("🔍 Analyse de la structure de l'application...")
    
    exporter = SimpleChartExporter()
    patterns = exporter.get_all_chart_patterns()
    
    print(f"\n📊 Résultats de l'analyse:")
    print(f"   - Pages analysées: {len(patterns) if patterns else 0}")
    
    if patterns:
        total_patterns = sum(len(page_patterns) for page_patterns in patterns.values())
        print(f"   - Patterns de graphiques détectés: {total_patterns}")
        
        print(f"\n📄 Détail par page:")
        for page, page_patterns in patterns.items():
            print(f"   - {page}: {len(page_patterns)} graphiques")
            
            # Grouper par type
            pattern_types = {}
            for pattern in page_patterns:
                pattern_type = pattern['type']
                pattern_types[pattern_type] = pattern_types.get(pattern_type, 0) + 1
            
            for pattern_type, count in pattern_types.items():
                print(f"     * {pattern_type}: {count}")
    else:
        print("   - Aucun pattern détecté")
    
    return patterns

def export_specific_charts():
    """
    Export de graphiques spécifiques avec personnalisation.
    """
    
    print("🎯 Export personnalisé...")
    
    exporter = SimpleChartExporter("custom_exports")
    
    # Créer uniquement les graphiques de patrimoine
    charts = exporter.create_sample_charts()
    
    # Filtrer pour ne garder que certains types
    patrimoine_charts = [
        chart for chart in charts 
        if 'patrimoine' in chart['name'].lower() or 'repartition' in chart['name'].lower()
    ]
    
    print(f"📊 Export de {len(patrimoine_charts)} graphiques patrimoniaux...")
    
    results = []
    for chart in patrimoine_charts:
        try:
            filename = f"{chart['name']}.png"
            filepath = Path("custom_exports") / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Export avec paramètres personnalisés
            chart['fig'].write_image(
                str(filepath),
                width=1600,  # Plus large pour présentation
                height=1000,  # Plus haut
                scale=3      # Haute résolution
            )
            
            results.append({
                'name': chart['name'],
                'title': chart['title'],
                'file': filename,
                'success': True
            })
            
            print(f"✅ {chart['title']} → {filename}")
            
        except Exception as e:
            results.append({
                'name': chart['name'],
                'title': chart['title'],
                'file': filename,
                'success': False,
                'error': str(e)
            })
            
            print(f"❌ Erreur avec {chart['title']}: {e}")
    
    return results

def main():
    """Fonction principale démontrant les différents usages."""
    
    print("🚀 Exemples d'utilisation de l'exporteur de graphiques")
    print("=" * 70)
    
    # 1. Analyse de la structure
    print("\n1️⃣ ANALYSE DE LA STRUCTURE")
    patterns = analyze_app_structure()
    
    # 2. Export standard pour présentation
    print("\n" + "=" * 70)
    print("\n2️⃣ EXPORT POUR PRÉSENTATION")
    export_dir, charts = export_for_presentation()
    
    # 3. Export personnalisé
    print("\n" + "=" * 70)
    print("\n3️⃣ EXPORT PERSONNALISÉ")
    custom_results = export_specific_charts()
    
    # Résumé final
    print("\n" + "=" * 70)
    print("\n📋 RÉSUMÉ FINAL")
    
    if patterns:
        total_detected = sum(len(p) for p in patterns.values())
        print(f"   - Graphiques détectés dans le code: {total_detected}")
    
    print(f"   - Graphiques d'exemple générés: {len(charts)}")
    print(f"   - Graphiques personnalisés: {len(custom_results)}")
    
    print(f"\n📁 Répertoires créés:")
    print(f"   - Présentation: {export_dir}/")
    print(f"   - Personnalisé: custom_exports/")
    print(f"   - Test: test_exports/")
    
    print(f"\n💡 Conseils:")
    print(f"   - Utilisez l'interface Streamlit pour un contrôle total")
    print(f"   - Le mode 'analyse statique' est plus fiable")
    print(f"   - Vérifiez toujours les dépendances avant l'export")
    
    print(f"\n🎉 Démonstration terminée avec succès!")

if __name__ == "__main__":
    main()
