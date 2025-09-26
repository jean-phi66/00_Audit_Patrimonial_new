import streamlit as st
import json
from datetime import date, datetime

# --- Fonctions utilitaires pour la sérialisation JSON ---

class CustomJSONEncoder(json.JSONEncoder):
    """Encodeur JSON personnalisé pour gérer les objets date et les types NumPy."""
    def default(self, obj):
        if isinstance(obj, date):
            # Stocke la date dans un format reconnaissable
            return {'_type': 'date', 'value': obj.isoformat()}
        
        # Gestion des objets OpenFisca non sérialisables
        if hasattr(obj, '__class__') and 'MarginalRateTaxScale' in str(type(obj)):
            # Convertit l'objet MarginalRateTaxScale en représentation simple
            return {'_type': 'MarginalRateTaxScale', 'value': 'non_serializable_openfisca_object'}
        
        # Gestion des types NumPy
        import numpy as np
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        
        # Gestion des types Pandas
        try:
            import pandas as pd
            if isinstance(obj, pd.Series):
                return obj.tolist()
            elif isinstance(obj, pd.DataFrame):
                return obj.to_dict()
        except ImportError:
            pass
        
        # Pour tous les autres objets non sérialisables, on les ignore
        try:
            return super().default(obj)
        except TypeError:
            # Si l'objet n'est pas sérialisable, on le remplace par une représentation string
            return f"non_serializable_{type(obj).__name__}"

def json_decoder_hook(obj):
    """Décodeur JSON personnalisé pour reconstruire les objets date."""
    if '_type' in obj:
        if obj['_type'] == 'date':
            return datetime.fromisoformat(obj['value']).date()
        elif obj['_type'] == 'MarginalRateTaxScale':
            # Pour les objets OpenFisca non sérialisables, on retourne None ou une valeur par défaut
            return None
    return obj

# --- Clés du session_state à sauvegarder ---
PERSISTENT_KEYS = [
    'parents', 'enfants', 'actifs', 'passifs', 
    'projection_settings', 'revenus', 'depenses',
    'reorganisation_data', 'epargne_precaution', 'reserve_projet',
    'per_input_parameters', 'scpi_credit_parameters'
]

# --- Fonctions principales de la page ---

def debug_data_types(data, path=""):
    """Fonction de debug pour identifier les types de données problématiques."""
    import numpy as np
    problematic_types = []
    
    def check_recursively(obj, current_path):
        if isinstance(obj, dict):
            for key, value in obj.items():
                check_recursively(value, f"{current_path}.{key}" if current_path else key)
        elif isinstance(obj, list):
            for i, value in enumerate(obj):
                check_recursively(value, f"{current_path}[{i}]")
        else:
            # Vérifier si c'est un type problématique
            if hasattr(obj, 'dtype') and 'float32' in str(obj.dtype):
                problematic_types.append(f"{current_path}: {type(obj)} avec dtype {obj.dtype}")
            elif isinstance(obj, np.floating) and obj.dtype == np.float32:
                problematic_types.append(f"{current_path}: {type(obj)} (float32)")
    
    check_recursively(data, path)
    return problematic_types

def get_data_to_save():
    """Rassemble toutes les données pertinentes du session_state dans un dictionnaire."""
    data_to_save = {}
    for key in PERSISTENT_KEYS:
        # Utilise une valeur par défaut appropriée selon le type de données
        if 'settings' in key or key in ['per_input_parameters', 'scpi_credit_parameters']:
            default_value = {}
        elif key in ['epargne_precaution', 'reserve_projet']:
            default_value = 0.0
        else:
            default_value = []
        data_to_save[key] = st.session_state.get(key, default_value)
    return data_to_save

def load_data_into_session(data):
    """Charge les données depuis un dictionnaire dans le session_state."""
    for key in PERSISTENT_KEYS:
        # Utilise une valeur par défaut appropriée selon le type de données
        if 'settings' in key or key in ['per_input_parameters', 'scpi_credit_parameters']:
            default_value = {}
        elif key in ['epargne_precaution', 'reserve_projet']:
            default_value = 0.0
        else:
            default_value = []
        setattr(st.session_state, key, data.get(key, default_value))

#def main():
st.title("💾 Sauvegarde et Chargement")
st.markdown("Utilisez cette page pour sauvegarder l'ensemble de vos données dans un fichier, ou pour recharger une session de travail précédente.")

col_save, col_load = st.columns(2)

# --- Section Sauvegarde ---
with col_save:
    st.header("⬇️ Sauvegarder mes données")
    st.markdown("Cliquez sur le bouton ci-dessous pour télécharger un fichier `patrimoine_data.json` contenant toutes les informations que vous avez saisies.")

    try:
        data_to_save = get_data_to_save()
        
        # Debug : identifier les types problématiques
        with st.expander("🔍 Debug - Types de données", expanded=False):
            problematic = debug_data_types(data_to_save)
            if problematic:
                st.warning("Types problématiques détectés :")
                for item in problematic:
                    st.text(item)
            else:
                st.success("Aucun type problématique détecté")
            
            # Afficher un échantillon des données
            st.json(data_to_save, expanded=False)
        
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
        # Afficher des informations de debug supplémentaires
        st.error(f"Type d'erreur : {type(e)}")
        
        # Essayer de débugger chaque clé individuellement
        with st.expander("🔍 Debug détaillé", expanded=True):
            for key in PERSISTENT_KEYS:
                try:
                    data = st.session_state.get(key, [])
                    json.dumps(data, cls=CustomJSONEncoder)
                    st.success(f"✅ {key}: OK")
                except Exception as key_error:
                    st.error(f"❌ {key}: {key_error}")
                    st.text(f"Type: {type(data)}")
                    if hasattr(data, '__len__') and len(data) > 0:
                        st.text(f"Premier élément: {type(data[0]) if isinstance(data, list) else 'N/A'}")

# --- Section Chargement ---
with col_load:
    st.header("⬆️ Charger des données")
    uploaded_file = st.file_uploader("Choisissez un fichier de sauvegarde", type="json")
    st.warning("Attention, le chargement d'un fichier écrasera toutes les données actuellement saisies.")

    if uploaded_file is not None:
        try:
            file_content = uploaded_file.getvalue().decode("utf-8")
            loaded_data = json.loads(file_content, object_hook=json_decoder_hook)
            load_data_into_session(loaded_data)
            st.success("✅ Données chargées avec succès ! L'application va s'actualiser.")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Erreur lors du chargement du fichier : {e}")
