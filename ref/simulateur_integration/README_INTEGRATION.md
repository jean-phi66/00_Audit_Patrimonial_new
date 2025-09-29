# Simulateur d'Investissement Financier - Module d'Intégration

Ce dossier contient tous les fichiers nécessaires pour intégrer le simulateur d'investissement financier dans une autre application Streamlit.

## Fichiers inclus

### Modules principaux
- `app.py` : Application Streamlit principale (peut servir de référence)
- `config.py` : Configuration et gestion du session state
- `simulation_financiere.py` : Moteur de calcul et d'optimisation
- `calculations.py` : Fonctions de calcul des données
- `ui_components.py` : Composants d'interface utilisateur Streamlit

### Configuration
- `requirements.txt` : Dépendances Python nécessaires
- `__init__.py` : Fichier pour faire du dossier un module Python

## Installation

1. Installez les dépendances :
```bash
pip install -r requirements.txt
```

## Intégration dans votre application

### Option 1 : Intégration complète comme page

```python
import streamlit as st
import sys
import os

# Ajouter le chemin du simulateur
sys.path.append('chemin/vers/simulateur_integration')

# Importer l'app complète
from app import *  # Charge toute l'application

# Ou créer une page dédiée
def page_simulateur():
    # Le contenu de app.py sera exécuté ici
    pass
```

### Option 2 : Intégration modulaire

```python
import streamlit as st
import sys
sys.path.append('chemin/vers/simulateur_integration')

from simulation_financiere import maximiser_solde_final_avec_contrainte
from config import initialiser_session_state, preparer_parametres_optimisation
from ui_components import (
    afficher_sidebar_parametres,
    afficher_metriques_principales,
    afficher_graphique_waterfall
)

def ma_fonction_simulateur():
    # Initialiser le session state
    initialiser_session_state()
    
    # Afficher les composants souhaités
    parametres = afficher_sidebar_parametres()
    
    # Utiliser les fonctions de calcul
    if st.button("Optimiser"):
        resultat = maximiser_solde_final_avec_contrainte(parametres)
        afficher_metriques_principales(resultat)
```

### Option 3 : Utilisation des composants individuels

Vous pouvez importer et utiliser n'importe quel composant individuellement :

```python
from ui_components import afficher_graphique_waterfall, afficher_tableau_resultats_actifs
from simulation_financiere import calculer_simulation_mensuelle
from calculations import calculer_donnees_tableau_actifs

# Utiliser les fonctions selon vos besoins
```

## Structure des fonctions principales

### Configuration (config.py)
- `initialiser_session_state()` : Initialise les variables de session
- `preparer_parametres_optimisation()` : Prépare les paramètres pour l'optimisation

### Simulation (simulation_financiere.py)
- `maximiser_solde_final_avec_contrainte()` : Fonction principale d'optimisation
- `calculer_simulation_mensuelle()` : Calcule la simulation détaillée
- `formater_resultat_optimisation()` : Formate les résultats

### Interface (ui_components.py)
- `afficher_sidebar_parametres()` : Sidebar avec les paramètres
- `afficher_metriques_principales()` : Affichage des métriques clés
- `afficher_graphique_waterfall()` : Graphique waterfall
- `afficher_tableau_resultats_actifs()` : Tableau des résultats par actif

## Exemple d'intégration complète

```python
import streamlit as st
import sys
sys.path.append('chemin/vers/simulateur_integration')

def page_simulateur_investissement():
    st.header("Simulateur d'Investissement")
    
    # Import des modules
    from config import initialiser_session_state
    from ui_components import afficher_sidebar_parametres, afficher_metriques_principales
    from simulation_financiere import maximiser_solde_final_avec_contrainte
    
    # Initialisation
    initialiser_session_state()
    
    # Interface
    parametres = afficher_sidebar_parametres()
    
    if st.button("Lancer la simulation"):
        with st.spinner("Optimisation en cours..."):
            resultat = maximiser_solde_final_avec_contrainte(**parametres)
            afficher_metriques_principales(resultat)

# Dans votre app principale
if __name__ == "__main__":
    page_simulateur_investissement()
```

## Notes importantes

- Assurez-vous que le chemin vers le dossier `simulateur_integration` est correctement ajouté à `sys.path`
- Toutes les dépendances listées dans `requirements.txt` doivent être installées
- Le simulateur utilise le session state de Streamlit, assurez-vous qu'il n'y a pas de conflits avec vos variables
- Les composants UI sont conçus pour être modulaires et réutilisables

## Support

Pour toute question sur l'intégration, référez-vous aux fichiers sources qui contiennent une documentation détaillée des fonctions.