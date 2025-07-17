import streamlit as st

# Page d'accueil
st.title("Outil d'Audit Patrimonial 💰")

st.markdown("""
Bienvenue dans votre assistant d'audit patrimonial.

Cette application vous permettra de :
1.  **Définir la composition de votre foyer** (parents et enfants).
2.  **Détailler votre patrimoine** (actifs et passifs).
3.  (Prochainement) **Projeter vos flux financiers** et anticiper les événements clés de votre vie.

**👈 Utilisez le menu de navigation sur la gauche pour commencer.**

---
*Cette application utilisera à terme [OpenFisca-France](https://github.com/openfisca/openfisca-france) pour des calculs de fiscalité précis.*
""")

# Afficher les données actuelles (utile pour le débogage)
with st.expander("Voir les données en cours (pour le développement)"):
    st.write("### Données du Foyer :")
    st.json(st.session_state.parents)
    st.json(st.session_state.enfants)
    st.write("### Données du Patrimoine :")
    #st.json(st.session_state.actifs)
    #st.json(st.session_state.passifs)
