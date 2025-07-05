import streamlit as st
import pandas as pd
import plotly.express as px
import uuid
from core.patrimoine_logic import calculate_monthly_payment

# --- Fonctions de gestion de la page ---

def sync_all_flux_data():
    """
    Synchronise les revenus et dépenses avec les données des autres pages (Famille, Patrimoine).
    - Salaires des parents.
    - Loyers, charges, et taxes des biens immobiliers.
    - Mensualités des prêts.
    Cette fonction reconstruit les listes à chaque exécution pour garantir la cohérence.
    """
    if 'revenus' not in st.session_state:
        st.session_state.revenus = []
    if 'depenses' not in st.session_state:
        st.session_state.depenses = []

    # --- 1. Conserver les entrées manuelles et séparer les salaires ---
    manual_revenus = [r for r in st.session_state.revenus if 'source_id' not in r and r.get('type') != 'Salaire']
    manual_depenses = [d for d in st.session_state.depenses if 'source_id' not in d]
    
    # On commence avec une liste vide pour les flux automatiques
    auto_revenus = []
    auto_depenses = []

    # --- 2. Synchronisation des salaires ---
    sync_salaires(auto_revenus) # Modifie la liste auto_revenus directement

    # --- 3. Synchronisation avec le patrimoine ---
    # Actifs productifs -> Revenus (loyers) et Dépenses (charges, taxe)
    for asset in st.session_state.get('actifs', []):
        if asset.get('type') == 'Immobilier productif':
            asset_id = asset['id']
            if asset.get('loyers_mensuels', 0.0) > 0:
                auto_revenus.append({'id': f"revenu_{asset_id}", 'libelle': f"Loyers de '{asset.get('libelle', 'N/A')}'", 'montant': asset['loyers_mensuels'], 'type': 'Patrimoine', 'source_id': asset_id})
            if asset.get('charges', 0.0) > 0:
                auto_depenses.append({'id': f"charges_{asset_id}", 'libelle': f"Charges de '{asset.get('libelle', 'N/A')}'", 'montant': asset['charges'], 'categorie': 'Logement', 'source_id': asset_id})
            if asset.get('taxe_fonciere', 0.0) > 0:
                auto_depenses.append({'id': f"taxe_{asset_id}", 'libelle': f"Taxe Foncière de '{asset.get('libelle', 'N/A')}'", 'montant': asset['taxe_fonciere'] / 12, 'categorie': 'Impôts et taxes', 'source_id': asset_id})

    # Passifs (prêts) -> Dépenses (mensualités)
    for passif in st.session_state.get('passifs', []):
        passif_id = passif.get('id', str(uuid.uuid4()))
        if 'id' not in passif: passif['id'] = passif_id
        mensualite = calculate_monthly_payment(passif.get('montant_initial', 0), passif.get('taux_annuel', 0), passif.get('duree_mois', 0))
        if mensualite > 0:
            auto_depenses.append({'id': f"pret_{passif_id}", 'libelle': f"Mensualité de '{passif.get('libelle', 'Prêt N/A')}'", 'montant': mensualite, 'categorie': 'Remboursement de prêts', 'source_id': passif_id})

    # --- 4. Réassemblage des listes ---
    st.session_state.revenus = auto_revenus + manual_revenus
    st.session_state.depenses = auto_depenses + manual_depenses

def sync_salaires(auto_revenus_list):
    """
    S'assure que chaque parent a une entrée de salaire et l'ajoute à la liste fournie.
    """
    # On s'assure que chaque parent a une entrée de salaire
    parent_prenoms = {p['prenom'] for p in st.session_state.get('parents', []) if p.get('prenom')}
    salaire_prenoms = {r['libelle'].split(' ')[1] for r in st.session_state.revenus if r.get('type') == 'Salaire'}

    # Ajouter les salaires manquants
    for prenom in parent_prenoms - salaire_prenoms:
        st.session_state.revenus.insert(0, {
            'id': f"salaire_{prenom}",
            'libelle': f"Salaire {prenom}",
            'montant': 0.0,
            'type': 'Salaire'
        })
    
    # Ajoute les salaires existants et corrects à la liste des revenus auto
    for r in st.session_state.revenus:
        if r.get('type') == 'Salaire' and r['libelle'].split(' ')[1] in parent_prenoms:
            auto_revenus_list.append(r)

def add_flux_item(category):
    """Ajoute un revenu (non-salaire) ou une dépense."""
    if category == 'revenus':
        st.session_state.revenus.append({
            'id': str(uuid.uuid4()),
            'libelle': '',
            'montant': 0.0,
            'type': 'Autre'
        })
    elif category == 'depenses':
        st.session_state.depenses.append({
            'id': str(uuid.uuid4()),
            'libelle': '',
            'montant': 0.0,
            'categorie': 'Dépenses courantes'
        })

def remove_flux_item(category, item_id):
    """Supprime un item de flux par son ID."""
    if category == 'revenus':
        st.session_state.revenus = [r for r in st.session_state.revenus if r['id'] != item_id]
    elif category == 'depenses':
        st.session_state.depenses = [d for d in st.session_state.depenses if d['id'] != item_id]
    st.rerun()

# --- Fonctions d'UI ---

def display_revenus_ui():
    """Affiche l'interface pour la gestion des revenus."""
    st.header("💰 Revenus Mensuels")

    # --- Salaires (obligatoires) ---
    for revenu in st.session_state.revenus:
        if revenu['type'] == 'Salaire':
            with st.container(border=True):
                st.subheader(revenu['libelle'])
                montant = st.number_input("Montant net mensuel (€)", value=float(revenu.get('montant', 0.0)), min_value=0.0, step=100.0, format="%.2f", key=f"revenu_montant_{revenu['id']}")
                revenu['montant'] = montant
                if montant == 0.0:
                    st.warning("Le salaire de ce parent est obligatoire et doit être renseigné.")
    
    # --- Revenus du patrimoine (automatiques) ---
    st.markdown("---")
    st.subheader("Revenus du patrimoine (auto)")
    patrimoine_revenus = [r for r in st.session_state.revenus if r.get('type') == 'Patrimoine']
    if not patrimoine_revenus:
        st.info("Aucun revenu locatif détecté depuis la page Patrimoine.")
    else:
        for revenu in patrimoine_revenus:
            r_c1, r_c2 = st.columns([3, 2])
            r_c1.text_input("Libellé (auto)", value=revenu['libelle'], key=f"revenu_libelle_auto_{revenu['id']}", disabled=True)
            r_c2.number_input("Montant mensuel (€) (auto)", value=float(revenu.get('montant', 0.0)), key=f"revenu_montant_auto_{revenu['id']}", disabled=True, format="%.2f")

    # --- Autres revenus (manuels) ---
    st.markdown("---")
    st.subheader("Autres revenus manuels")
    if st.button("➕ Ajouter un autre revenu manuel", use_container_width=True):
        add_flux_item('revenus')

    manual_revenus = [r for r in st.session_state.revenus if r.get('type') == 'Autre']
    if not manual_revenus:
        st.info("Cliquez sur 'Ajouter un autre revenu manuel' pour commencer.")

    for revenu in manual_revenus:
        if revenu.get('type') == 'Autre':
            r_c1, r_c2, r_c3 = st.columns([4, 2, 1])
            revenu['libelle'] = r_c1.text_input("Libellé", value=revenu['libelle'], key=f"revenu_libelle_{revenu['id']}", placeholder="Ex: Pension, Aide...")
            revenu['montant'] = r_c2.number_input("Montant mensuel (€)", value=float(revenu.get('montant', 0.0)), min_value=0.0, step=50.0, format="%.2f", key=f"revenu_montant_{revenu['id']}")
            with r_c3:
                st.write("")
                st.write("")
                if st.button("🗑️", key=f"del_revenu_{revenu['id']}", help="Supprimer ce revenu"):
                    remove_flux_item('revenus', revenu['id'])

def display_depenses_ui():
    """Affiche l'interface pour la gestion des dépenses."""
    st.header("💸 Dépenses Mensuelles")

    # --- Dépenses du patrimoine (automatiques) ---
    st.subheader("Dépenses du patrimoine (auto)")
    auto_depenses = [d for d in st.session_state.depenses if 'source_id' in d]
    if not auto_depenses:
        st.info("Aucune dépense liée au patrimoine détectée (charges, taxes, prêts).")
    else:
        for depense in auto_depenses:
            d_c1, d_c2 = st.columns([3, 2])
            d_c1.text_input("Libellé (auto)", value=depense['libelle'], key=f"depense_libelle_auto_{depense['id']}", disabled=True)
            d_c2.number_input("Montant mensuel (€) (auto)", value=float(depense.get('montant', 0.0)), key=f"depense_montant_auto_{depense['id']}", disabled=True, format="%.2f")

    # --- Dépenses manuelles ---
    st.markdown("---")
    st.subheader("Autres dépenses manuelles")
    if st.button("➕ Ajouter une dépense manuelle", use_container_width=True):
        add_flux_item('depenses')

    manual_depenses = [d for d in st.session_state.depenses if 'source_id' not in d]
    if not manual_depenses:
        st.info("Cliquez sur 'Ajouter une dépense manuelle' pour commencer.")

    categories_depenses = ["Dépenses courantes", "Logement", "Transport", "Loisirs", "Impôts et taxes", "Enfants", "Santé", "Remboursement de prêts", "Autres"]
    for depense in manual_depenses:
        d_c1, d_c2, d_c3, d_c4 = st.columns([3, 2, 2, 1])
        depense['libelle'] = d_c1.text_input("Libellé", value=depense['libelle'], key=f"depense_libelle_{depense['id']}", placeholder="Ex: Courses, Loyer, Électricité...")
        depense['montant'] = d_c2.number_input("Montant mensuel (€)", value=float(depense.get('montant', 0.0)), min_value=0.0, step=50.0, format="%.2f", key=f"depense_montant_{depense['id']}")
        depense['categorie'] = d_c3.selectbox("Catégorie", options=categories_depenses, index=categories_depenses.index(depense['categorie']) if depense['categorie'] in categories_depenses else 0, key=f"depense_cat_{depense['id']}")
        with d_c4:
            st.write("")
            st.write("")
            if st.button("🗑️", key=f"del_depense_{depense['id']}", help="Supprimer cette dépense"):
                remove_flux_item('depenses', depense['id'])

def display_summary():
    """Affiche le résumé des flux et la capacité d'épargne."""
    st.markdown("---")
    st.header("📊 Synthèse des Flux")

    total_revenus = sum(r.get('montant', 0.0) for r in st.session_state.revenus)
    total_depenses = sum(d.get('montant', 0.0) for d in st.session_state.depenses)
    capacite_epargne = total_revenus - total_depenses

    s_c1, s_c2, s_c3 = st.columns(3)
    s_c1.metric("Total des Revenus Mensuels", f"{total_revenus:,.2f} €")
    s_c2.metric("Total des Dépenses Mensuelles", f"{total_depenses:,.2f} €")
    s_c3.metric("Capacité d'Épargne Mensuelle", f"{capacite_epargne:,.2f} €", delta=f"{capacite_epargne:,.2f} €")

    if st.session_state.depenses:
        st.markdown("---")
        st.subheader("Répartition des Dépenses")
        df_depenses = pd.DataFrame(st.session_state.depenses)
        if not df_depenses.empty and df_depenses['montant'].sum() > 0:
            fig = px.pie(df_depenses, values='montant', names='categorie', title='Répartition des dépenses par catégorie', hole=.3)
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)

# --- Exécution Principale ---

def main():
    st.title("🌊 Flux Mensuels (Revenus & Dépenses)")
    st.markdown("Renseignez ici vos revenus et vos dépenses mensuelles pour calculer votre capacité d'épargne.")

    if 'parents' not in st.session_state or not st.session_state.parents or not st.session_state.parents[0].get('prenom'):
        st.warning("⚠️ Veuillez d'abord renseigner les informations du foyer dans la page **1_Famille**.")
        st.stop()

    sync_all_flux_data()

    col1, col2 = st.columns(2)
    with col1:
        display_revenus_ui()
    with col2:
        display_depenses_ui()

    display_summary()

if __name__ == "__main__":
    main()