#!/bin/bash

# Script de lancement de l'application Streamlit
echo "🚀 Lancement de l'application Audit Patrimonial..."

# Se déplacer dans le bon répertoire
cd "/Users/jean-philippenavarro/Documents/10_CGP/20_Outils - Simulateurs/00_Audit_Patrimonial_new"

# Arrêter tous les processus Streamlit existants
echo "📄 Arrêt des processus Streamlit existants..."
pkill -f streamlit 2>/dev/null || true

# Attendre un peu
sleep 2

# Lancer l'application
echo "🌐 Lancement de Streamlit sur http://localhost:8501"
echo "⚠️  IMPORTANT: Ouvrez votre navigateur et allez à http://localhost:8501"
echo "⚠️  Pour arrêter l'application, appuyez sur Ctrl+C dans ce terminal"
echo ""

streamlit run app.py --server.port=8501 --server.address=localhost --browser.gatherUsageStats=false