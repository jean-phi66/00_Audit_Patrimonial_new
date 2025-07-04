import streamlit as st
from datetime import date
import pandas as pd

st.title("👤 Composition du Foyer Fiscal")
#st.markdown("Veuillez renseigner les informations concernant les membres de votre foyer.")

# --- Initialisation du Session State ---
# Indispensable sur chaque page pour que l'application fonctionne de manière autonome
# si on rafraîchit la page ou si on y accède directement.
if 'parents' not in st.session_state:
    st.session_state.parents = [
        {'prenom': '', 'date_naissance': None}
    ]
if 'enfants' not in st.session_state:
    st.session_state.enfants = []

# --- Fonctions de logique métier (Calculs et manipulation de données) ---

def calculate_age(born):
    """Calcule l'âge à partir d'une date de naissance."""
    if not born:
        return None
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

def add_parent():
    """Ajoute le second parent à la session state."""
    if len(st.session_state.parents) < 2:
        st.session_state.parents.append({'prenom': '', 'date_naissance': None})
        st.rerun()

def remove_parent():
    """Supprime le second parent de la session state."""
    if len(st.session_state.parents) == 2:
        st.session_state.parents.pop(1)
        st.rerun()

def add_child():
    """Ajoute un enfant à la session state."""
    st.session_state.enfants.append({'prenom': '', 'date_naissance': None})
    st.rerun()

def remove_child(index):
    """Supprime un enfant de la session state à un index donné."""
    if 0 <= index < len(st.session_state.enfants):
        st.session_state.enfants.pop(index)
        st.rerun()

def get_family_summary_df(parents, enfants):
    """Crée et retourne un DataFrame formaté du résumé de la famille."""
    family_members_data = []

    for role, members in [("Parent", parents), ("Enfant", enfants)]:
        for member in members:
            if member.get('prenom'):
                age = calculate_age(member.get('date_naissance'))
                family_members_data.append({
                    "Rôle": role,
                    "Prénom": member['prenom'],
                    "Date de naissance": member.get('date_naissance'),
                    "Âge": age if age is not None else "N/A",
                })

    if not family_members_data:
        return None

    df = pd.DataFrame(family_members_data)
    df['Date de naissance'] = pd.to_datetime(df['Date de naissance']).dt.strftime('%d/%m/%Y').replace('NaT', 'N/A')
    return df

# Utilisation de colonnes pour séparer Parents et Enfants
col1, col2 = st.columns(2)

# --- COLONNE 1 : PARENTS ---
with col1:
    st.header("👨‍👩‍👧 Parents")
    
    # Formulaire pour le premier parent (toujours présent)
    prenom_p1 = st.session_state.parents[0]['prenom']
    with st.expander(f"👤 Parent 1 : {prenom_p1 or 'À compléter'}", expanded=False):
        st.session_state.parents[0]['prenom'] = st.text_input("Prénom", value=st.session_state.parents[0]['prenom'], key="p1_prenom")
        st.session_state.parents[0]['date_naissance'] = st.date_input(
            "Date de naissance",
            value=st.session_state.parents[0]['date_naissance'],
            min_value=date(1920, 1, 1),
            max_value=date.today(),
            key="p1_dob"
        )

    #st.markdown("---")
    
    # Logique pour le second parent (optionnel)
    if len(st.session_state.parents) == 2:
        # Si le second parent existe, afficher son formulaire avec un bouton de suppression
        prenom_p2 = st.session_state.parents[1]['prenom']
        with st.expander(f"👤 Parent 2 : {prenom_p2 or 'À compléter'}", expanded=False):
            field_col, button_col = st.columns([4, 1])
            with field_col:
                st.session_state.parents[1]['prenom'] = st.text_input("Prénom", value=st.session_state.parents[1]['prenom'], key="p2_prenom")
                st.session_state.parents[1]['date_naissance'] = st.date_input(
                    "Date de naissance",
                    value=st.session_state.parents[1]['date_naissance'],
                    min_value=date(1920, 1, 1),
                    max_value=date.today(),
                    key="p2_dob"
                )
            with button_col:
                st.write("") # Espaceur
                st.write("")
                if st.button("🗑️", key="del_parent_2", help="Supprimer le parent 2"):
                    remove_parent()
    
    # Bouton pour ajouter le second parent s'il n'existe pas et que le max n'est pas atteint
    if len(st.session_state.parents) < 2:
        if st.button("➕ Ajouter un deuxième parent", use_container_width=True):
            add_parent()

# --- COLONNE 2 : ENFANTS ---
with col2:
    st.header("👶 Enfants")

    # Affichage des formulaires pour chaque enfant
    if not st.session_state.enfants:
        st.info("Cliquez sur 'Ajouter un enfant' pour commencer à saisir les informations.")
        
    for i, enfant in enumerate(st.session_state.enfants):
        prenom_enfant = enfant['prenom']
        with st.expander(f"👶 Enfant {i + 1} : {prenom_enfant or 'À compléter'}", expanded=False):
            # Utilisation de colonnes pour aligner le bouton de suppression
            field_col, button_col = st.columns([4, 1])
            
            with field_col:
                enfant['prenom'] = st.text_input("Prénom", value=enfant['prenom'], key=f"enf_prenom_{i}")
                enfant['date_naissance'] = st.date_input(
                    "Date de naissance",
                    value=enfant['date_naissance'],
                    min_value=date(1980, 1, 1),
                    max_value=date.today(),
                    key=f"enf_dob_{i}"
                )
            
            with button_col:
                # Ajoute un espace pour mieux aligner le bouton verticalement
                st.write("") 
                st.write("")
                if st.button("🗑️", key=f"del_enf_{i}", help="Supprimer cet enfant"):
                    remove_child(i)

    # Bouton pour ajouter un enfant
    if st.button("➕ Ajouter un enfant", use_container_width=True):
        add_child()

# --- Affichage du résumé de la famille ---
st.markdown("---")
st.header("👨‍👩‍👧‍👦 Résumé de la Famille")

df_summary = get_family_summary_df(st.session_state.parents, st.session_state.enfants)

if df_summary is not None:
    # Réorganiser les colonnes pour l'affichage
    df_summary = df_summary[["Rôle", "Prénom", "Date de naissance", "Âge"]]
    st.dataframe(df_summary, use_container_width=True, hide_index=True)
else:
    st.info("Aucun membre de la famille n'a été renseigné pour le moment.")
