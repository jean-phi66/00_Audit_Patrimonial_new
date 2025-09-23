import streamlit as st

# Page d'accueil
st.title("Outil d'Audit Patrimonial 💰")

st.markdown("""
Bienvenue dans votre assistant d'audit patrimonial complet.

NOUVELLE VERSION 2.0 avec des fonctionnalités améliorées !

Cette application vous permet de :

### 🏠 **Audit Complet**
1. **Définir la composition de votre foyer** - Configurez votre famille (parents et enfants)
2. **Analyser votre patrimoine** - Détaillez vos actifs et passifs avec visualisations
3. **Projeter vos flux financiers** - Anticipez revenus, dépenses et événements futurs
4. **Optimiser votre fiscalité** - Simulations et conseils d'optimisation

### 📊 **Fonctionnalités Avancées**
- **Visualisations interactives** de votre patrimoine et projections
- **Simulations fiscales** avec OpenFisca-France
- **Rapports détaillés** de votre situation patrimoniale
- **Optimisation PER** et stratégies d'investissement
- **Capacité d'endettement** et simulations de crédit

### 💾 **Gestion des Données**
- **Sauvegarde/Chargement** de vos données
- **Import/Export** de vos analyses

**👈 Utilisez le menu de navigation sur la gauche pour commencer votre audit.**

---
*Application utilisant [OpenFisca-France](https://github.com/openfisca/openfisca-france) pour des calculs fiscaux précis et à jour.*
""")

# Afficher les données actuelles (utile pour le débogage)
with st.expander("Voir les données en cours (pour le développement)"):
    st.write("### Données du Foyer :")
    st.json(st.session_state.parents)
    st.json(st.session_state.enfants)
    st.write("### Données du Patrimoine :")
    st.json(st.session_state.actifs)
    st.json(st.session_state.passifs)
