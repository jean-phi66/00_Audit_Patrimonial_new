import streamlit as st
import pandas as pd
from core.patrimoine_logic import get_patrimoine_df

def initialize_reorganisation_state():
    """Initialise les données de réorganisation dans le session_state"""
    if 'reorganisation_data' not in st.session_state:
        st.session_state.reorganisation_data = []

def get_financial_assets():
    """Récupère les actifs financiers depuis le patrimoine"""
    financial_assets = []
    for actif in st.session_state.get('actifs', []):
        if actif.get('type') == "Actifs financiers":
            financial_assets.append({
                'id': actif.get('id'),
                'libelle': actif.get('libelle', ''),
                'valeur': actif.get('valeur', 0.0),
                'reorientable': False,
                'montant_reorientable': 0.0
            })
    return financial_assets

def update_reorganisation_data():
    """Met à jour les données de réorganisation avec les actifs financiers actuels"""
    current_financial_assets = get_financial_assets()
    existing_ids = {item['id'] for item in st.session_state.reorganisation_data}
    
    # Ajouter les nouveaux actifs financiers
    for asset in current_financial_assets:
        if asset['id'] not in existing_ids:
            st.session_state.reorganisation_data.append(asset)
    
    # Supprimer les actifs qui n'existent plus
    st.session_state.reorganisation_data = [
        item for item in st.session_state.reorganisation_data
        if item['id'] in {asset['id'] for asset in current_financial_assets}
    ]
    
    # Mettre à jour les valeurs des actifs existants
    asset_values = {asset['id']: asset['valeur'] for asset in current_financial_assets}
    for item in st.session_state.reorganisation_data:
        if item['id'] in asset_values:
            item['valeur'] = asset_values[item['id']]

def display_reorganisation_ui():
    """Affiche l'interface de réorganisation des stocks"""
    st.header("📊 Réorganisation des Actifs Financiers")
    
    # Vérifier s'il y a des actifs financiers
    if not any(actif.get('type') == "Actifs financiers" for actif in st.session_state.get('actifs', [])):
        st.warning("⚠️ Aucun actif financier trouvé dans votre patrimoine.")
        st.info("Veuillez d'abord ajouter des actifs financiers dans la section 'Description du patrimoine'.")
        return
    
    # Mise à jour des données
    update_reorganisation_data()
    
    st.markdown("---")
    st.subheader("Sélection des actifs à réorienter")
    
    if not st.session_state.reorganisation_data:
        st.info("Aucun actif financier à afficher.")
        return
    
    # Affichage sous forme de tableau interactif
    for i, item in enumerate(st.session_state.reorganisation_data):
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 2, 1])
            
            with col1:
                st.write(f"**{item['libelle']}**")
            
            with col2:
                st.write(f"{item['valeur']:,.2f} €")
            
            with col3:
                item['reorientable'] = st.checkbox(
                    "Réorientable",
                    value=item.get('reorientable', False),
                    key=f"reorientable_{i}_{item['id']}"
                )
            
            with col4:
                if item['reorientable']:
                    item['montant_reorientable'] = st.number_input(
                        "Montant (€)",
                        value=item.get('montant_reorientable', 0.0),
                        min_value=0.0,
                        max_value=item['valeur'],
                        step=100.0,
                        format="%.2f",
                        key=f"montant_{i}_{item['id']}"
                    )
                else:
                    item['montant_reorientable'] = 0.0
                    st.write("—")
            
            with col5:
                if item['reorientable']:
                    if st.button(
                        "100%",
                        key=f"full_amount_{i}_{item['id']}",
                        help="Reporter 100% du montant"
                    ):
                        item['montant_reorientable'] = item['valeur']
                        st.rerun()
            
            st.markdown("---")
    
    # Résumé
    display_reorganisation_summary()

def display_reorganisation_summary():
    """Affiche le résumé de la réorganisation"""
    st.subheader("📈 Résumé de la réorganisation")
    
    total_patrimoine_financier = sum(item['valeur'] for item in st.session_state.reorganisation_data)
    total_reorientable = sum(
        item['montant_reorientable'] 
        for item in st.session_state.reorganisation_data 
        if item['reorientable']
    )
    
    if total_patrimoine_financier == 0:
        pourcentage_reorientable = 0
    else:
        pourcentage_reorientable = (total_reorientable / total_patrimoine_financier) * 100
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Patrimoine financier total",
            f"{total_patrimoine_financier:,.2f} €"
        )
    
    with col2:
        st.metric(
            "Montant réorientable",
            f"{total_reorientable:,.2f} €"
        )
    
    with col3:
        st.metric(
            "% du patrimoine",
            f"{pourcentage_reorientable:.1f}%"
        )
    
    # Détail des actifs réorientables
    if total_reorientable > 0:
        st.markdown("### Détail des actifs sélectionnés pour réorientation")
        
        reorientable_assets = [
            item for item in st.session_state.reorganisation_data 
            if item['reorientable'] and item['montant_reorientable'] > 0
        ]
        
        if reorientable_assets:
            df_reorientable = pd.DataFrame([
                {
                    'Actif': item['libelle'],
                    'Valeur totale (€)': f"{item['valeur']:,.2f}",
                    'Montant réorientable (€)': f"{item['montant_reorientable']:,.2f}",
                    '% de l\'actif': f"{(item['montant_reorientable'] / item['valeur'] * 100):.1f}%"
                }
                for item in reorientable_assets
            ])
            
            st.dataframe(df_reorientable, use_container_width=True, hide_index=True)
        
        # Boutons d'action
        st.markdown("### Actions")
        col_action1, col_action2, col_action3 = st.columns(3)
        
        with col_action1:
            if st.button("💾 Sauvegarder la sélection", use_container_width=True):
                st.success("✅ Sélection sauvegardée avec succès!")
        
        with col_action2:
            if st.button("🔄 Réinitialiser", use_container_width=True):
                for item in st.session_state.reorganisation_data:
                    item['reorientable'] = False
                    item['montant_reorientable'] = 0.0
                st.rerun()
        
        with col_action3:
            if st.button("📊 Analyser l'impact", use_container_width=True):
                st.info("Fonctionnalité d'analyse d'impact à venir...")

# --- Exécution principale ---
st.title("🔄 Réorganisation Stock")
st.markdown("Sélectionnez les actifs financiers que vous souhaitez réorienter et définissez les montants.")

# Initialisation
initialize_reorganisation_state()

# Affichage de l'interface
display_reorganisation_ui()
