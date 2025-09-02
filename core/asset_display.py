import streamlit as st
from .patrimoine_logic import add_item, remove_item

def display_assets_ui():
    """Affiche l'interface utilisateur pour la gestion des actifs."""
    st.header("✅ Actifs")
    st.markdown("Ce que vous possédez (immobilier, placements, comptes bancaires, etc.)")

    for i, actif in enumerate(st.session_state.actifs):
        libelle = actif.get('libelle', f'Actif #{i+1}')
        with st.expander(f"Actif : {libelle or 'À compléter'}", expanded=not bool(libelle)):
            cols = st.columns([3, 1])
            with cols[0]:
                st.session_state.actifs[i]['libelle'] = st.text_input(
                    "Libellé de l'actif",
                    value=actif.get('libelle', ''),
                    key=f"actif_libelle_{i}"
                )
                st.session_state.actifs[i]['type'] = st.selectbox(
                    "Type d'actif",
                    options=[
                        "Immobilier de jouissance", "Immobilier productif",
                        "Placements financiers", "Comptes bancaires", "Autres"
                    ],
                    index=[
                        "Immobilier de jouissance", "Immobilier productif",
                        "Placements financiers", "Comptes bancaires", "Autres"
                    ].index(actif.get('type', 'Immobilier de jouissance')),
                    key=f"actif_type_{i}"
                )
                st.session_state.actifs[i]['valeur'] = st.number_input(
                    "Valeur de l'actif (€)",
                    min_value=0.0,
                    value=float(actif.get('valeur', 0.0)),
                    step=1000.0,
                    format="%.2f",
                    key=f"actif_valeur_{i}"
                )

            with cols[1]:
                st.write("") # Spacer
                st.write("")
                if st.button("🗑️ Supprimer", key=f"del_actif_{i}", use_container_width=True):
                    remove_item('actifs', i)

            # --- Champs conditionnels pour l'immobilier productif ---
            if st.session_state.actifs[i]['type'] == 'Immobilier productif':
                st.markdown("---")
                st.subheader("Détails de l'investissement locatif")
                
                immo_cols = st.columns(2)
                with immo_cols[0]:
                    st.session_state.actifs[i]['loyers_mensuels'] = st.number_input(
                        "Loyers mensuels (€)", min_value=0.0,
                        value=float(actif.get('loyers_mensuels', 0.0)), step=50.0, key=f"actif_loyers_{i}"
                    )
                    st.session_state.actifs[i]['charges'] = st.number_input(
                        "Charges mensuelles (non récupérables)", min_value=0.0,
                        value=float(actif.get('charges', 0.0)), step=10.0, key=f"actif_charges_{i}"
                    )
                    st.session_state.actifs[i]['taxe_fonciere'] = st.number_input(
                        "Taxe foncière annuelle (€)", min_value=0.0,
                        value=float(actif.get('taxe_fonciere', 0.0)), step=50.0, key=f"actif_tf_{i}"
                    )

                with immo_cols[1]:
                    st.session_state.actifs[i]['mode_exploitation'] = st.selectbox(
                        "Mode d'exploitation",
                        options=['Location Nue', 'Location Meublée'],
                        index=['Location Nue', 'Location Meublée'].index(actif.get('mode_exploitation', 'Location Nue')),
                        key=f"actif_mode_expl_{i}"
                    )
                    st.session_state.actifs[i]['dispositif_fiscal'] = st.selectbox(
                        "Dispositif fiscal",
                        options=['Aucun', 'Pinel', 'Scellier', 'Scellier Intermediaire'],
                        index=['Aucun', 'Pinel', 'Scellier', 'Scellier Intermediaire'].index(
                            actif.get('dispositif_fiscal', 'Aucun')
                        ),
                        key=f"actif_dispo_fiscal_{i}"
                    )
                    # Champs spécifiques pour Pinel ou Scellier
                    if st.session_state.actifs[i]['dispositif_fiscal'] in ['Pinel', 'Scellier', 'Scellier Intermediaire']:
                        st.session_state.actifs[i]['annee_debut_dispositif'] = st.number_input(
                            "Année de début du dispositif",
                            min_value=2009, max_value=2100,
                            value=int(actif.get('annee_debut_dispositif', 2020)),
                            step=1,
                            key=f"actif_annee_debut_dispositif_{i}"
                        )
                        # Durées possibles selon le dispositif
                        if st.session_state.actifs[i]['dispositif_fiscal'] in ['Scellier', 'Scellier Intermediaire']:
                            duree_options = [9, 12, 15]
                        else:
                            duree_options = [9, 12]
                        st.session_state.actifs[i]['duree_dispositif'] = st.selectbox(
                            "Durée d'engagement (ans)",
                            options=duree_options,
                            index=duree_options.index(int(actif.get('duree_dispositif', duree_options[0]))),
                            key=f"actif_duree_dispositif_{i}"
                        )

                # --- Champs conditionnels pour LMNP ---
                if st.session_state.actifs[i]['mode_exploitation'] == 'Location Meublée':
                    st.markdown("##### Ventilation pour amortissement LMNP")
                    lmnp_cols = st.columns(3)
                    with lmnp_cols[0]:
                        st.session_state.actifs[i]['part_amortissable_foncier'] = st.number_input(
                            "Part Foncier (non amortissable)", min_value=0.0,
                            value=float(actif.get('part_amortissable_foncier', actif.get('valeur', 0.0) * 0.2)),
                            help="Part de la valeur du terrain, généralement entre 15% et 25% de la valeur totale.",
                            key=f"actif_lmnp_foncier_{i}"
                        )
                    with lmnp_cols[1]:
                        st.session_state.actifs[i]['part_travaux'] = st.number_input(
                            "Part Travaux", min_value=0.0,
                            value=float(actif.get('part_travaux', 0.0)), key=f"actif_lmnp_travaux_{i}"
                        )
                    with lmnp_cols[2]:
                        st.session_state.actifs[i]['part_meubles'] = st.number_input(
                            "Part Meubles", min_value=0.0,
                            value=float(actif.get('part_meubles', 0.0)), key=f"actif_lmnp_meubles_{i}"
                        )

            # --- Champs conditionnels pour l'immobilier de jouissance ---
            if st.session_state.actifs[i]['type'] == 'Immobilier de jouissance':
                st.markdown("---")
                st.subheader("Détails du bien")
                jouissance_cols = st.columns(2)
                with jouissance_cols[0]:
                    st.session_state.actifs[i]['charges'] = st.number_input(
                        "Charges mensuelles (copropriété, etc.)", min_value=0.0,
                        value=float(actif.get('charges', 0.0)), step=10.0, key=f"actif_charges_jouissance_{i}"
                    )
                with jouissance_cols[1]:
                    st.session_state.actifs[i]['taxe_fonciere'] = st.number_input(
                        "Taxe foncière annuelle (€)", min_value=0.0,
                        value=float(actif.get('taxe_fonciere', 0.0)), step=50.0, key=f"actif_tf_jouissance_{i}"
                    )

    if st.button("➕ Ajouter un actif", use_container_width=True):
        add_item('actifs')