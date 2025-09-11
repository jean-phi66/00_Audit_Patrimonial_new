#!/usr/bin/env python3
"""
Script de test pour la fonctionnalité d'export des graphiques.
Ce script teste l'exporteur simplifié sans interface Streamlit.
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from core.simple_chart_exporter import SimpleChartExporter
    print("✅ Import de SimpleChartExporter réussi")
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    sys.exit(1)

def test_chart_export():
    """Test de l'export des graphiques d'exemple."""
    
    print("🔍 Test de l'exporteur de graphiques...")
    
    # Créer le répertoire de test
    test_dir = Path("test_exports")
    exporter = SimpleChartExporter(str(test_dir))
    
    print(f"📁 Répertoire d'export: {test_dir.resolve()}")
    
    # Analyser les patterns de graphiques
    print("\n📊 Analyse des patterns de graphiques...")
    patterns = exporter.get_all_chart_patterns()
    
    if patterns:
        print(f"✅ {len(patterns)} pages avec patterns détectées:")
        for page, page_patterns in patterns.items():
            print(f"   - {page}: {len(page_patterns)} patterns")
    else:
        print("⚠️ Aucun pattern détecté")
    
    # Exporter les graphiques d'exemple
    print("\n🎨 Export des graphiques d'exemple...")
    
    try:
        results = exporter.export_sample_charts()
        
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        print(f"\n📈 Résultats:")
        print(f"   - Graphiques générés: {len(results)}")
        print(f"   - Exports réussis: {len(successful)}")
        print(f"   - Échecs: {len(failed)}")
        
        if successful:
            print("\n✅ Graphiques exportés avec succès:")
            for result in successful:
                file_path = Path(result['path'])
                if file_path.exists():
                    file_size = file_path.stat().st_size / 1024  # KB
                    print(f"   - {result['title']}: {result['file']} ({file_size:.1f} KB)")
                else:
                    print(f"   - {result['title']}: FICHIER MANQUANT!")
        
        if failed:
            print("\n❌ Échecs d'export:")
            for result in failed:
                print(f"   - {result['title']}: {result.get('error', 'Erreur inconnue')}")
        
        # Vérifier les fichiers créés
        if test_dir.exists():
            png_files = list(test_dir.glob("*.png"))
            print(f"\n📁 Fichiers PNG trouvés dans {test_dir}: {len(png_files)}")
            for png_file in png_files:
                file_size = png_file.stat().st_size / 1024  # KB
                print(f"   - {png_file.name} ({file_size:.1f} KB)")
        
        return len(successful) > 0
        
    except Exception as e:
        print(f"❌ Erreur lors de l'export: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dependencies():
    """Test des dépendances requises."""
    
    print("🔧 Vérification des dépendances...")
    
    dependencies = [
        ('pandas', 'pd'),
        ('plotly.express', 'px'),
        ('plotly.graph_objects', 'go'),
        ('pathlib', 'Path'),
        ('kaleido', None)  # Kaleido n'a pas besoin d'être importé directement
    ]
    
    all_ok = True
    
    for dep_name, alias in dependencies:
        try:
            if alias:
                exec(f"import {dep_name} as {alias}")
            else:
                exec(f"import {dep_name}")
            print(f"✅ {dep_name}")
        except ImportError as e:
            print(f"❌ {dep_name}: {e}")
            all_ok = False
    
    return all_ok

def main():
    """Fonction principale de test."""
    
    print("🧪 Test de la fonctionnalité d'export des graphiques")
    print("=" * 60)
    
    # Test des dépendances
    deps_ok = test_dependencies()
    
    if not deps_ok:
        print("\n❌ Certaines dépendances sont manquantes. L'export pourrait échouer.")
        return False
    
    print("\n" + "=" * 60)
    
    # Test de l'export
    export_ok = test_chart_export()
    
    print("\n" + "=" * 60)
    
    if export_ok:
        print("🎉 Test réussi ! La fonctionnalité d'export semble fonctionner.")
        return True
    else:
        print("💥 Test échoué. Vérifiez les erreurs ci-dessus.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
