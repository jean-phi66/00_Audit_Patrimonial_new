# 🏠 Audit Patrimonial - Application Streamlit

Application web locale pour l'audit et l'analyse patrimoniale développée avec Streamlit.

## �️ Développement et utilisation locale

### Prérequis
- Python 3.12+
- pip

### Installation et lancement

```bash
# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
streamlit run app.py
```

L'application sera accessible sur http://localhost:8501

## 📁 Structure du projet

```
├── app.py                     # Application principale Streamlit
├── requirements.txt           # Dépendances Python
├── core/                     # Modules métier
├── pages/                    # Pages Streamlit
├── assets/                   # Ressources (fonts, etc.)
└── utils/                    # Utilitaires
```

## 📊 Fonctionnalités

- **Composition du foyer** : Gestion des membres de la famille
- **Description du patrimoine** : Actifs et passifs
- **Flux financiers** : Revenus et dépenses
- **Analyses et projections** : Calculs patrimoniaux avancés
- **Optimisation fiscale** : Simulations avec OpenFisca
- **Génération de rapports** : Export PDF des analyses

## 🔧 Technologies

- **Frontend** : Streamlit
- **Backend** : Python 3.12
- **Calculs fiscaux** : OpenFisca-France
- **Visualisations** : Plotly, Matplotlib
- **Données** : Pandas, NumPy

## 📞 Support

Pour toute question ou problème, consultez les logs de l'application ou contactez l'équipe de développement.