#!/bin/bash

# Script de lancement simple et efficace
echo "🚀 Lancement de l'Audit Patrimonial"
echo ""

# Arrêter les processus existants
pkill -f streamlit 2>/dev/null || true
sleep 1

# Lancer l'application
echo "📱 Application lancée sur: http://localhost:8501"
echo ""
echo "🌐 OUVREZ VOTRE NAVIGATEUR et allez à:"
echo "    👉 http://localhost:8501"
echo ""
echo "❌ Pour arrêter: Ctrl+C"
echo "⏰ Attente du démarrage..."
echo ""

cd "/Users/jean-philippenavarro/Documents/10_CGP/20_Outils - Simulateurs/00_Audit_Patrimonial_new"

# Lancer avec ouverture automatique du navigateur
streamlit run app.py \
    --server.port=8501 \
    --server.address=localhost \
    --browser.gatherUsageStats=false \
    --server.headless=false