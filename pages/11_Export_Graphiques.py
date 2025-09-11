"""
Page d'export automatique des graphiques.
Cette page permet d'exporter tous les graphiques de l'application en fichiers PNG.
"""

import streamlit as st
import os
from datetime import datetime
from pathlib import Path
from core.chart_exporter import ChartExporter
from core.simple_chart_exporter import SimpleChartExporter

st.title("📊 Export des Graphiques")
st.markdown("""
Cette fonctionnalité permet d'exporter automatiquement tous les graphiques de l'application 
en fichiers PNG avec des noms cohérents basés sur le contenu et la page source.
""")

# Choix du mode d'export
st.subheader("🎯 Mode d'Export")

export_mode = st.radio(
    "Choisissez le mode d'export :",
    options=["Analyse statique", "Simulation complète"],
    help="""
    - **Analyse statique** : Analyse le code et crée des graphiques d'exemple (plus rapide, plus sûr)
    - **Simulation complète** : Exécute chaque page pour capturer les vrais graphiques (plus lent, peut échouer)
    """
)

# Configuration de l'export
st.subheader("⚙️ Configuration de l'Export")

col1, col2 = st.columns(2)

with col1:
    export_dir = st.text_input(
        "Répertoire de destination",
        value="exports/charts",
        help="Répertoire où seront sauvegardés les graphiques"
    )

with col2:
    include_timestamp = st.checkbox(
        "Inclure timestamp dans les noms",
        value=True,
        help="Ajoute la date et l'heure dans le nom des fichiers"
    )

# Options avancées
with st.expander("🔧 Options avancées"):
    image_width = st.number_input(
        "Largeur des images (px)",
        min_value=600,
        max_value=2400,
        value=1200,
        step=100
    )
    
    image_height = st.number_input(
        "Hauteur des images (px)",
        min_value=400,
        max_value=1600,
        value=800,
        step=100
    )
    
    image_scale = st.slider(
        "Facteur d'échelle",
        min_value=1,
        max_value=4,
        value=2,
        help="Augmente la résolution des images"
    )

# Prévisualisation des pages à traiter
st.subheader("📁 Pages à Analyser")

if export_mode == "Analyse statique":
    # Mode analyse statique avec l'exporteur simplifié
    simple_exporter = SimpleChartExporter(export_dir)
    
    st.info("🔍 Mode analyse statique sélectionné")
    st.markdown("""
    Ce mode analyse le code source des pages pour identifier les types de graphiques 
    et génère des exemples représentatifs sans exécuter les pages.
    """)
    
    # Analyser les patterns de graphiques
    chart_patterns = simple_exporter.get_all_chart_patterns()
    
    if chart_patterns:
        st.success(f"✅ {len(chart_patterns)} pages avec graphiques détectées")
        
        with st.expander("Voir les patterns détectés"):
            for page_name, patterns in chart_patterns.items():
                st.write(f"📄 **{page_name}** - {len(patterns)} patterns détectés")
                for pattern in patterns:
                    st.write(f"   - {pattern['type']} (ligne {pattern['line']})")
    else:
        st.warning("⚠️ Aucun pattern de graphique détecté")

else:
    # Mode simulation complète avec l'exporteur complet
    exporter = ChartExporter(export_dir)
    page_files = exporter.get_page_files()
    
    st.info("🚀 Mode simulation complète sélectionné")
    st.markdown("""
    Ce mode exécute chaque page pour capturer les vrais graphiques générés.
    Plus précis mais plus lent et potentiellement instable.
    """)
    
    if page_files:
        st.success(f"✅ {len(page_files)} pages détectées")
        
        # Afficher la liste des pages avec détection préliminaire des graphiques
        with st.expander("Voir le détail des pages"):
            for page_file in page_files:
                chart_functions = exporter.get_chart_functions_from_file(page_file)
                st.write(f"📄 **{page_file.name}** - {len(chart_functions)} graphiques détectés")
                
                if chart_functions:
                    for func in chart_functions[:3]:  # Afficher les 3 premiers
                        st.write(f"   - Ligne {func['line']}: `{func['content'][:50]}...`")
                    if len(chart_functions) > 3:
                        st.write(f"   - ... et {len(chart_functions) - 3} autres")
    else:
        st.warning("⚠️ Aucune page détectée dans le répertoire 'pages'")

# Section d'export
st.subheader("🚀 Lancement de l'Export")

# Vérifications préalables
ready_to_export = True
checks = []

# Vérifier que le répertoire peut être créé
try:
    Path(export_dir).mkdir(parents=True, exist_ok=True)
    checks.append("✅ Répertoire de destination accessible")
except Exception as e:
    checks.append(f"❌ Erreur avec le répertoire: {e}")
    ready_to_export = False

# Vérifier qu'il y a des pages à traiter
if export_mode == "Analyse statique":
    if chart_patterns:
        checks.append(f"✅ Patterns de graphiques détectés")
    else:
        checks.append("⚠️ Aucun pattern détecté - continuera avec les exemples")
else:
    if page_files:
        checks.append(f"✅ {len(page_files)} pages à traiter")
    else:
        checks.append("❌ Aucune page à traiter")
        ready_to_export = False

# Vérifier les dépendances
try:
    import plotly
    import kaleido  # Nécessaire pour l'export PNG
    checks.append("✅ Dépendances disponibles")
except ImportError as e:
    checks.append(f"❌ Dépendance manquante: {e}")
    ready_to_export = False

# Afficher les vérifications
for check in checks:
    if "✅" in check:
        st.success(check)
    else:
        st.error(check)

if not ready_to_export:
    st.error("🚫 L'export ne peut pas démarrer. Veuillez corriger les erreurs ci-dessus.")
    
    if "kaleido" in str(checks):
        st.info("💡 Pour installer Kaleido: `pip install kaleido`")

# Bouton d'export
if ready_to_export:
    if st.button("🎯 Démarrer l'Export", type="primary", use_container_width=True):
        
        if export_mode == "Analyse statique":
            # Export en mode simplifié
            st.info("🔍 Export en mode analyse statique...")
            
            simple_exporter = SimpleChartExporter(export_dir)
            
            try:
                # Exporter les graphiques d'exemple
                with st.spinner("Génération des graphiques d'exemple..."):
                    results = simple_exporter.export_sample_charts()
                
                # Afficher les résultats
                st.success("🎉 Export terminé!")
                
                successful_exports = [r for r in results if r['success']]
                failed_exports = [r for r in results if not r['success']]
                
                # Métriques de résumé
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Graphiques générés", len(results))
                
                with col2:
                    st.metric("Exports réussis", len(successful_exports))
                
                with col3:
                    st.metric("Échecs", len(failed_exports))
                
                # Détails des exports
                if successful_exports:
                    st.subheader("📊 Graphiques Exportés")
                    for result in successful_exports:
                        st.success(f"✅ {result['title']} → `{result['file']}`")
                
                if failed_exports:
                    st.subheader("❌ Échecs d'Export")
                    for result in failed_exports:
                        st.error(f"❌ {result['title']}: {result.get('error', 'Erreur inconnue')}")
                
            except Exception as e:
                st.error(f"💥 Erreur pendant l'export: {e}")
                st.exception(e)
        
        else:
            # Export en mode simulation complète
            st.warning("🚀 Export en mode simulation complète...")
            st.info("⚠️ Ce mode peut prendre plusieurs minutes et peut être instable")
            
            # Créer une nouvelle instance avec la configuration choisie
            exporter = ChartExporter(export_dir)
            
            # Conteneurs pour l'affichage en temps réel
            progress_container = st.container()
            status_container = st.container()
            
            with progress_container:
                progress_bar = st.progress(0)
                status_text = st.empty()
            
            def update_progress(value, message):
                progress_bar.progress(value)
                status_text.text(message)
            
            # Lancer l'export
            try:
                with st.spinner("Export en cours..."):
                    export_summary = exporter.export_all_charts(update_progress)
                
                # Afficher les résultats
                with status_container:
                    st.success("🎉 Export terminé!")
                    
                    # Métriques de résumé
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Pages traitées", export_summary['processed_pages'])
                    
                    with col2:
                        st.metric("Graphiques détectés", export_summary['total_charts'])
                    
                    with col3:
                        st.metric("Exports réussis", export_summary['successful_exports'])
                    
                    with col4:
                        st.metric("Échecs", export_summary['failed_exports'])
                    
                    # Détails de l'export
                    if export_summary['successful_exports'] > 0:
                        st.subheader("📁 Fichiers Exportés")
                        
                        export_dir_path = Path(export_dir)
                        if export_dir_path.exists():
                            files = list(export_dir_path.glob("*.png"))
                            files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                            
                            # Afficher les fichiers les plus récents
                            for file in files[:10]:  # Les 10 plus récents
                                file_size = file.stat().st_size
                                file_size_mb = file_size / (1024 * 1024)
                                modification_time = datetime.fromtimestamp(file.stat().st_mtime)
                                
                                st.write(f"📊 `{file.name}` ({file_size_mb:.1f} MB) - {modification_time.strftime('%H:%M:%S')}")
                            
                            if len(files) > 10:
                                st.info(f"... et {len(files) - 10} autres fichiers dans le répertoire")
                    
                    # Sauvegarder et afficher le rapport
                    try:
                        report_file = exporter.save_report(export_summary)
                        st.subheader("📋 Rapport d'Export")
                        
                        report_content = exporter.generate_export_report(export_summary)
                        st.markdown(report_content)
                        
                        st.success(f"📄 Rapport sauvegardé: `{report_file}`")
                        
                    except Exception as e:
                        st.warning(f"⚠️ Impossible de sauvegarder le rapport: {e}")
            
            except Exception as e:
                st.error(f"💥 Erreur pendant l'export: {e}")
                st.exception(e)
        
        # Bouton pour ouvrir le répertoire d'export
        if st.button("📂 Ouvrir le répertoire d'export"):
            try:
                os.startfile(export_dir)  # Windows
            except AttributeError:
                try:
                    os.system(f"open '{export_dir}'")  # macOS
                except:
                    os.system(f"xdg-open '{export_dir}'")  # Linux

# Section d'aide
with st.expander("❓ Aide et Informations"):
    st.markdown("""
    ### Comment fonctionne l'export ?
    
    1. **Analyse des pages** : L'outil parcourt tous les fichiers Python dans le répertoire `pages/`
    2. **Détection des graphiques** : Il identifie les fonctions qui créent des graphiques Plotly
    3. **Simulation d'exécution** : Chaque page est exécutée pour générer ses graphiques
    4. **Capture et sauvegarde** : Les graphiques sont interceptés et sauvegardés en PNG
    
    ### Nommage des fichiers
    
    Les fichiers sont nommés selon le pattern :
    `{nom_page}_{titre_graphique}_{timestamp}.png`
    
    ### Dépendances requises
    
    - `plotly` : Pour la création des graphiques
    - `kaleido` : Pour l'export en PNG
    - `streamlit` : Pour l'interface utilisateur
    
    ### Limitations
    
    - Seuls les graphiques Plotly sont supportés
    - L'export peut prendre du temps selon le nombre de pages
    - Certaines pages peuvent échouer si elles dépendent de données manquantes
    """)

# Informations de debug
if st.checkbox("🐛 Mode Debug"):
    st.subheader("Informations de Debug")
    
    st.write("**Répertoire de travail actuel:**", os.getcwd())
    st.write("**Répertoire d'export:**", Path(export_dir).resolve())
    
    # Obtenir les infos selon le mode
    if export_mode == "Analyse statique":
        simple_exporter = SimpleChartExporter(export_dir)
        debug_page_files = simple_exporter.get_all_chart_patterns()
        st.write("**Pages avec patterns détectées:**", len(debug_page_files) if debug_page_files else 0)
        
        if debug_page_files:
            st.write("**Détail des pages:**")
            for page in debug_page_files.keys():
                st.write(f"- {page}")
    else:
        debug_exporter = ChartExporter(export_dir)
        debug_page_files = debug_exporter.get_page_files()
        st.write("**Pages détectées:**", len(debug_page_files))
        
        if debug_page_files:
            st.write("**Détail des pages:**")
            for page in debug_page_files:
                st.write(f"- {page}")
