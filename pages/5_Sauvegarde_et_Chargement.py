import streamlit as st
import json
from datetime import date, datetime

# --- Fonctions utilitaires pour la sérialisation JSON ---

class CustomJSONEncoder(json.JSONEncoder):
    """Encodeur JSON personnalisé pour gérer les objets date."""
    def default(self, obj):
        if isinstance(obj, date):
            # Stocke la date dans un format reconnaissable
            return {'_type': 'date', 'value': obj.isoformat()}
        return super().default(obj)

def json_decoder_hook(obj):
    """Décodeur JSON personnalisé pour reconstruire les objets date."""
    if '_type' in obj and obj['_type'] == 'date':
        return datetime.fromisoformat(obj['value']).date()
    return obj

# --- Fonctions principales de la page ---

def get_data_to_save():
    """Rassemble toutes les données pertinentes du session_state dans un dictionnaire."""
    return {
        'parents': st.session_state.get('parents', []),
        'enfants': st.session_state.get('enfants', []),
        'actifs': st.session_state.get('actifs', []),
        'passifs': st.session_state.get('passifs', []),
        'projection_settings': st.session_state.get('projection_settings', {}),
        'revenus': st.session_state.get('revenus', []),
        'depenses': st.session_state.get('depenses', [])
    }

def load_data_into_session(data):
    """Charge les données depuis un dictionnaire dans le session_state."""
    st.session_state.parents = data.get('parents', [])
    st.session_state.enfants = data.get('enfants', [])
    st.session_state.actifs = data.get('actifs', [])
    st.session_state.passifs = data.get('passifs', [])
    st.session_state.projection_settings = data.get('projection_settings', {})
    st.session_state.revenus = data.get('revenus', [])
    st.session_state.depenses = data.get('depenses', [])


#def main():
st.title("💾 Sauvegarde et Chargement")
st.markdown("Utilisez cette page pour sauvegarder l'ensemble de vos données dans un fichier, ou pour recharger une session de travail précédente.")

# --- Section Sauvegarde ---
st.header("⬇️ Sauvegarder mes données")
st.markdown("Cliquez sur le bouton ci-dessous pour télécharger un fichier `patrimoine_data.json` contenant toutes les informations que vous avez saisies.")

try:
    data_to_save = get_data_to_save()
    json_data = json.dumps(data_to_save, cls=CustomJSONEncoder, indent=4, ensure_ascii=False)
    
    st.download_button(
        label="Télécharger le fichier de sauvegarde",
        data=json_data,
        file_name="patrimoine_data.json",
        mime="application/json",
        use_container_width=True
    )
except Exception as e:
    st.error(f"Une erreur est survenue lors de la préparation des données pour la sauvegarde : {e}")

# --- Section Chargement ---
st.header("⬆️ Charger des données")
st.warning("Attention, le chargement d'un fichier écrasera toutes les données actuellement saisies.")

uploaded_file = st.file_uploader("Choisissez un fichier de sauvegarde", type="json")

if uploaded_file is not None:
    try:
        file_content = uploaded_file.getvalue().decode("utf-8")
        loaded_data = json.loads(file_content, object_hook=json_decoder_hook)
        load_data_into_session(loaded_data)
        st.success("✅ Données chargées avec succès ! L'application va s'actualiser.")
        st.rerun()
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement du fichier : {e}")

