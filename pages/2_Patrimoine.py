import streamlit as st

# Import des composants UI spécifiques
from core.patrimoine_display import (
    display_assets_ui,
    initialize_session_state,
    run_data_migrations,
    display_liabilities_ui,
    display_summary_and_charts
)

# --- Exécution Principale ---

st.title("🏡 Description du Patrimoine")
st.markdown("Listez ici vos actifs (ce que vous possédez) et vos passifs (ce que vous devez).")

initialize_session_state()
run_data_migrations()

col1, col2 = st.columns(2)
with col1:
    display_assets_ui()
with col2:
    display_liabilities_ui()

display_summary_and_charts()
