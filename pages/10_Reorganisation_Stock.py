import streamlit as st
import pandas as pd
from core.patrimoine_logic import get_patrimoine_df

def initialize_reorganisation_state():
    """Initialise les données de réorganisation dans le session_state"""
    if 'reorganisation_data' not in st.session_state:
        st.session_state.reorganisation_data = []
    if 'epargne_precaution' not in st.session_state:
        st.session_state.epargne_precaution = 0.0
    if 'reserve_projet' not in st.session_state:
        st.session_state.reserve_projet = 0.0

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
    
    #st.markdown("---")
    st.subheader("Sélection des actifs à réorienter")
    
    if not st.session_state.reorganisation_data:
        st.info("Aucun actif financier à afficher.")
        return
    
    # Conteneur pour limiter la largeur du tableau
    tableau_col, espace_col = st.columns([8, 4])
    
    with tableau_col:
        # En-têtes de colonnes
        col1, col2, col3, col4 = st.columns([2, 1.3, 0.7, 1.3])
        with col1:
            st.markdown("**Actif financier**")
        with col2:
            st.markdown("**Valeur totale**")
        with col3:
            st.markdown("**À réorienter**")
        with col4:
            st.markdown("**Montant réorientable**")
        
        #st.markdown("---")
        
        # Affichage sous forme de tableau interactif
        for i, item in enumerate(st.session_state.reorganisation_data):
            col1, col2, col3, col4 = st.columns([2, 1.3, 0.7, 1.3])
            
            with col1:
                st.write(f"**{item['libelle']}**")
            
            with col2:
                st.write(f"{item['valeur']:,.2f} €")
            
            with col3:
                # Gérer le changement d'état de la checkbox
                was_reorientable = item.get('reorientable', False)
                item['reorientable'] = st.checkbox(
                    "Y/N",
                    value=was_reorientable,
                    key=f"reorientable_{i}_{item['id']}"
                )
                
                # Si l'état change de False à True, mettre 100% par défaut
                if item['reorientable'] and not was_reorientable:
                    item['montant_reorientable'] = item['valeur']
                elif not item['reorientable']:
                    item['montant_reorientable'] = 0.0
            
            with col4:
                if item['reorientable']:
                    # Utiliser la valeur complète par défaut si pas encore définie
                    default_value = item.get('montant_reorientable', item['valeur'])
                    if default_value == 0.0:
                        default_value = item['valeur']
                    
                    item['montant_reorientable'] = st.number_input(
                        "",
                        value=default_value,
                        min_value=0.0,
                        max_value=item['valeur'],
                        step=100.0,
                        format="%.2f",
                        key=f"montant_{i}_{item['id']}",
                        label_visibility="collapsed"
                    )
                else:
                    item['montant_reorientable'] = 0.0
                    st.write("—")
            
            # Ajouter un séparateur plus fin seulement si ce n'est pas la dernière ligne
            #if i < len(st.session_state.reorganisation_data) - 1:
             #   st.markdown("<hr style='margin: 0.5rem 0; border: none; border-top: 1px solid #e0e0e0;'>", unsafe_allow_html=True)    # Résumé
    display_reorganisation_summary()

def display_reorganisation_summary():
    """Affiche le résumé de la réorganisation"""
    st.subheader("📈 Résumé de la réorganisation")
    
    # Calculs de base
    total_patrimoine_financier = sum(item['valeur'] for item in st.session_state.reorganisation_data)
    total_reorientable = sum(
        item['montant_reorientable'] 
        for item in st.session_state.reorganisation_data 
        if item['reorientable']
    )
    
    # Calcul de l'épargne bloquée (actifs non sélectionnés pour réorientation)
    epargne_bloquee = total_patrimoine_financier - total_reorientable
    
    # Calcul du stock mobilisable après déduction des réserves
    stock_mobilisable = max(0, total_reorientable - st.session_state.epargne_precaution - st.session_state.reserve_projet)
    
    # Calcul du pourcentage réorientable
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
        
        # Section pour les réserves
        st.markdown("---")
        st.markdown("### 🛡️ Gestion des réserves et stock mobilisable")
    
    # Organisation en 3 colonnes : inputs à gauche, espace au milieu, KPIs à droite
    reserve_col, espace_col, kpi_col = st.columns([1, 0.2, 2])
    
    with reserve_col:
        st.markdown("#### Réserves à déduire")
        st.session_state.epargne_precaution = st.number_input(
            "💰 Épargne de précaution (€)",
            value=st.session_state.get('epargne_precaution', 0.0),
            min_value=0.0,
            step=1000.0,
            format="%.2f",
            help="Montant à conserver en épargne de sécurité"
        )
        
        st.session_state.reserve_projet = st.number_input(
            "🏗️ Réserve projet (travaux, etc.) (€)",
            value=st.session_state.get('reserve_projet', 0.0),
            min_value=0.0,
            step=1000.0,
            format="%.2f",
            help="Montant à réserver pour des projets futurs"
        )
    
    # Calcul du stock mobilisable APRÈS la mise à jour des inputs
    stock_mobilisable = max(0, total_reorientable - st.session_state.epargne_precaution - st.session_state.reserve_projet)
    
    with kpi_col:
        st.markdown("#### Indicateurs patrimoniaux")
        
        # Première ligne : patrimoine total, épargne bloquée, stock réorientable
        kpi_row1_col1, kpi_row1_col2, kpi_row1_col3 = st.columns(3)
        
        with kpi_row1_col1:
            st.metric(
                "💰 Stock financier total",
                f"{total_patrimoine_financier:,.2f} €",
                help="Somme de tous vos actifs financiers"
            )
        
        with kpi_row1_col2:
            st.metric(
                "🔒 Épargne bloquée",
                f"{epargne_bloquee:,.2f} €",
                help="Actifs financiers non sélectionnés pour réorientation"
            )
        
        with kpi_row1_col3:
            st.metric(
                "💼 Stock réorientable",
                f"{total_reorientable:,.2f} €",
                help="Montant sélectionné pour réorientation"
            )
        
        # Deuxième ligne : déductions et résultat final
        kpi_row2_col1, kpi_row2_col2, kpi_row2_col3 = st.columns(3)
        
        with kpi_row2_col1:
            st.metric(
                "🛡️ Épargne de précaution",
                f"{st.session_state.epargne_precaution:,.2f} €",
                help="Montant à déduire du stock réorientable pour la sécurité"
            )
        
        with kpi_row2_col2:
            st.metric(
                "🏗️ Réserve projet",
                f"{st.session_state.reserve_projet:,.2f} €",
                help="Montant à déduire du stock réorientable pour vos projets"
            )
        
        with kpi_row2_col3:
            # Calcul du pourcentage du stock mobilisable par rapport au stock financier total
            if total_patrimoine_financier > 0:
                pourcentage_mobilisable = (stock_mobilisable / total_patrimoine_financier) * 100
            else:
                pourcentage_mobilisable = 0
            
            # Couleur selon le montant disponible
            delta_color = "normal" if stock_mobilisable > 0 else "inverse"
            
            # Affichage du delta avec le pourcentage
            if stock_mobilisable >= 0:
                delta_text = f"{pourcentage_mobilisable:.1f}% du total"
            else:
                delta_text = "Réserves trop élevées"
            
            st.metric(
                "🚀 **STOCK MOBILISABLE**",
                f"{stock_mobilisable:,.2f} €",
                delta=delta_text,
                help=f"Stock réorientable ({total_reorientable:,.2f} €) - Épargne de précaution ({st.session_state.epargne_precaution:,.2f} €) - Réserve projet ({st.session_state.reserve_projet:,.2f} €)"
            )
    
    # Message informatif
    if stock_mobilisable > 0:
        st.success(f"✅ Vous disposez de **{stock_mobilisable:,.2f} €** mobilisables pour vos objectifs patrimoniaux.")
    elif stock_mobilisable == 0:
        st.warning("⚠️ Aucun montant disponible après déduction des réserves.")
    else:
        st.error("❌ Les réserves dépassent le montant réorientable. Veuillez ajuster vos paramètres.")

# --- Exécution principale ---
st.title("🔄 Réorganisation Stock")
st.markdown("Sélectionnez les actifs financiers que vous souhaitez réorienter et définissez les montants.")

# Initialisation
initialize_reorganisation_state()

# Affichage de l'interface
display_reorganisation_ui()
