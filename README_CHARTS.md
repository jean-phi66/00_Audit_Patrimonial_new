# Générateur de Graphiques - Audit Patrimonial

Ce script Python permet de générer automatiquement tous les graphiques des pages "Description du patrimoine" et "Flux : revenus et dépenses" à partir d'un fichier JSON d'export de l'application Streamlit.

## 📋 Fonctionnalités

Le script génère les graphiques suivants :

### 📊 Graphiques du Patrimoine
- **Treemap du patrimoine brut** : Répartition hiérarchique des actifs par valeur brute
- **Treemap du patrimoine net** : Répartition hiérarchique des actifs par valeur nette
- **Donut chart patrimoine net** : Répartition circulaire par type d'actif
- **Donut chart répartition idéale** : Référence théorique de répartition patrimoniale
- **Barres empilées patrimoine brut** : Répartition Immobilier/Financier/Autres (valeur brute)
- **Barres empilées patrimoine net** : Répartition Immobilier/Financier/Autres (valeur nette)
- **Comparaisons INSEE** : Positionnement vs déciles INSEE pour patrimoine brut et net

### 💸 Graphiques des Flux
- **Treemap mensuel** : Répartition des revenus mensuels (dépenses + reste à vivre)
- **Treemap annuel** : Répartition des revenus annualisés

## 🚀 Installation et Utilisation

### Prérequis
```bash
pip install pandas plotly kaleido
```

### Utilisation de base
```bash
# Génération des graphiques (PNG + HTML)
python generate_charts.py patrimoine_data.json

# Personnaliser le répertoire de sortie
python generate_charts.py patrimoine_data.json --output mon_dossier

# Générer seulement les PNG
python generate_charts.py patrimoine_data.json --no-html

# Générer seulement les HTML
python generate_charts.py patrimoine_data.json --no-png
```

### Options disponibles
- `--output, -o` : Répertoire de sortie (défaut: `charts_output`)
- `--no-png` : Ne pas générer les fichiers PNG
- `--no-html` : Ne pas générer les fichiers HTML interactifs

## 📁 Fichier JSON d'entrée

Le fichier JSON doit être généré via la page "Sauvegarde et chargement" de l'application Streamlit. Il contient toutes les données structurées du patrimoine :

```json
{
  "parents": [...],
  "enfants": [...],
  "actifs": [...],
  "passifs": [...],
  "revenus": [...],
  "depenses": [...]
}
```

## 📂 Structure de sortie

```
charts_output/
├── patrimoine_brut_treemap.png
├── patrimoine_brut_treemap.html
├── patrimoine_net_treemap.png
├── patrimoine_net_treemap.html
├── patrimoine_net_donut.png
├── patrimoine_net_donut.html
├── patrimoine_ideal_donut.png
├── patrimoine_ideal_donut.html
├── patrimoine_brut_stacked_bar.png
├── patrimoine_brut_stacked_bar.html
├── patrimoine_net_stacked_bar.png
├── patrimoine_net_stacked_bar.html
├── patrimoine_brut_comparison_insee.png
├── patrimoine_brut_comparison_insee.html
├── patrimoine_net_comparison_insee.png
├── patrimoine_net_comparison_insee.html
├── flux_treemap_mensuel.png
├── flux_treemap_mensuel.html
├── flux_treemap_annuel.png
└── flux_treemap_annuel.html
```

## 📊 Formats de sortie

### PNG
- Haute résolution (1200x800, scale=2)
- Idéal pour l'impression et l'intégration dans des documents
- Taille typique : 100-200 KB par graphique

### HTML
- Graphiques interactifs avec zoom, hover, etc.
- Idéal pour la consultation en ligne
- Taille typique : 4-5 MB par graphique

## 🧪 Test avec des données d'exemple

Un fichier `example_data.json` est fourni pour tester le script :

```bash
python generate_charts.py example_data.json
```

## 🔧 Fonctionnement technique

Le script :
1. Charge le fichier JSON avec décodage des dates
2. Recrée les DataFrames de patrimoine avec la même logique que l'application
3. Utilise les fonctions originales de génération de graphiques (`core/charts.py`, `core/patrimoine_display.py`)
4. Sauvegarde chaque graphique en PNG et/ou HTML

## ⚠️ Limitations

- Nécessite que les modules `core/` de l'application soient disponibles
- Les graphiques de comparaison INSEE ne s'affichent que si le patrimoine > 0
- Certains graphiques peuvent être vides si les données correspondantes manquent

## 🐛 Dépannage

### Erreur d'import
```
ModuleNotFoundError: No module named 'core'
```
→ Vérifiez que vous exécutez le script depuis le répertoire racine du projet

### Erreur kaleido
```
ValueError: The kaleido package is required for image export
```  
→ Installez kaleido : `pip install kaleido`

### Graphiques vides
Certains graphiques peuvent être vides si :
- Aucun actif/passif n'est renseigné  
- Toutes les valeurs sont à zéro
- Les données sont malformées

Vérifiez la console pour les messages d'avertissement `⚠️`.

## 📞 Support

En cas de problème, vérifiez :
1. La validité du fichier JSON d'entrée
2. La présence de toutes les dépendances Python
3. L'exécution depuis le bon répertoire
4. La structure des données dans le JSON