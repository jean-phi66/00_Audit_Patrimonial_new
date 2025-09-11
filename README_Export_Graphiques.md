# Export Automatique des Graphiques 📊

Cette fonctionnalité permet d'exporter automatiquement tous les graphiques de l'application d'audit patrimonial en fichiers PNG avec des noms cohérents.

## 🎯 Fonctionnalités

### Deux modes d'export disponibles :

1. **Analyse statique** (recommandé)
   - Analyse le code source pour identifier les types de graphiques
   - Génère des exemples représentatifs sans exécuter les pages
   - Plus rapide et plus sûr
   - Idéal pour générer des modèles de graphiques

2. **Simulation complète** (avancé)
   - Exécute chaque page pour capturer les vrais graphiques
   - Plus précis mais plus lent
   - Peut échouer si les pages dépendent de données manquantes

## 🚀 Utilisation

### Via l'interface Streamlit

1. Lancez l'application : `python3 -m streamlit run app.py`
2. Naviguez vers "Outils" → "Export Graphiques"
3. Choisissez votre mode d'export
4. Configurez le répertoire de destination
5. Cliquez sur "Démarrer l'Export"

### Via script de test

```bash
python3 test_chart_export.py
```

## 📁 Structure des fichiers exportés

Les graphiques sont sauvegardés avec le pattern de nommage suivant :
```
{nom_page}_{titre_graphique}_{timestamp}_{compteur}.png
```

Exemples :
- `patrimoine_treemap_20250911_053438.png`
- `3_Focus_Immobilier_evolution_valeur_bien_20250911_053445_1.png`
- `projection_flux_futurs_20250911_053450_2.png`

## 🔧 Dépendances requises

- `streamlit` : Interface utilisateur
- `plotly` : Création des graphiques
- `kaleido` : Export des graphiques Plotly en PNG
- `pandas` : Manipulation des données
- `pathlib` : Gestion des chemins de fichiers

Pour installer les dépendances :
```bash
pip install -r requirements.txt
```

## 📊 Types de graphiques supportés

L'analyseur détecte automatiquement :
- Treemaps (`px.treemap`, `go.Treemap`)
- Graphiques en barres (`px.bar`, `go.Bar`)
- Graphiques linéaires (`px.line`, `go.Scatter`)
- Graphiques en secteurs (`px.pie`, `go.Pie`)
- Graphiques en cascade (`go.Waterfall`)
- Graphiques de dispersion (`px.scatter`)

## 🎨 Graphiques d'exemple générés

En mode analyse statique, les graphiques suivants sont automatiquement générés :

1. **Répartition du Patrimoine** (Treemap)
   - Visualise la répartition par type d'actifs
   - Format : Treemap hiérarchique

2. **Projection du Patrimoine** (Ligne)
   - Évolution projetée sur 20 ans
   - Format : Graphique linéaire avec marqueurs

3. **Flux Annuels** (Barres)
   - Revenus et dépenses par catégorie
   - Format : Graphique en barres colorées

4. **Évolution Immobilière** (Multi-lignes)
   - Valeur du bien vs capital restant dû
   - Format : Graphique multi-séries

5. **Répartition des Actifs** (Secteurs)
   - Distribution des types d'investissements
   - Format : Graphique en secteurs

## ⚙️ Configuration

### Options d'export personnalisables :

- **Répertoire de destination** : Où sauvegarder les fichiers
- **Largeur des images** : 600-2400 px (défaut: 1200px)
- **Hauteur des images** : 400-1600 px (défaut: 800px)
- **Facteur d'échelle** : 1-4x (défaut: 2x pour haute résolution)
- **Include timestamp** : Ajouter date/heure dans les noms

## 🐛 Dépannage

### Erreur "No module named 'kaleido'"
```bash
pip install kaleido
```

### Erreur "Permission denied"
- Vérifiez les permissions du répertoire de destination
- Changez le répertoire d'export vers un dossier accessible

### Graphiques vides ou erreurs d'exécution
- Utilisez le mode "Analyse statique" qui est plus stable
- Vérifiez que toutes les dépendances sont installées

### Fichiers non générés
- Vérifiez l'espace disque disponible
- Consultez les logs d'erreur dans l'interface

## 📋 Rapport d'export

Chaque export génère automatiquement :
- Un rapport détaillé en format Markdown
- Statistiques de réussite/échec par page
- Liste des fichiers générés avec leurs tailles
- Timestamp de l'export

## 🔍 Architecture technique

### Modules principaux :

- `core/chart_exporter.py` : Exporteur complet avec simulation
- `core/simple_chart_exporter.py` : Exporteur simplifié statique
- `pages/11_Export_Graphiques.py` : Interface utilisateur Streamlit

### Flux de traitement :

1. **Analyse** : Scan des fichiers Python pour détecter les patterns
2. **Génération** : Création ou capture des graphiques
3. **Export** : Sauvegarde en PNG avec nommage cohérent
4. **Rapport** : Génération du rapport de résultats

## 📈 Exemples d'utilisation

### Export rapide pour présentation
```python
from core.simple_chart_exporter import SimpleChartExporter

exporter = SimpleChartExporter("presentation/charts")
results = exporter.export_sample_charts()
```

### Analyse des patterns sans export
```python
exporter = SimpleChartExporter()
patterns = exporter.get_all_chart_patterns()
print(f"Pages avec graphiques: {len(patterns)}")
```

## 🤝 Contribution

Pour ajouter de nouveaux types de graphiques :
1. Ajoutez les patterns de détection dans `get_chart_functions_from_file()`
2. Créez des exemples dans `create_sample_charts()`
3. Testez avec `test_chart_export.py`

## 📝 Licence et Support

Cette fonctionnalité fait partie de l'application d'audit patrimonial.
Pour toute question ou amélioration, consultez la documentation du projet principal.
