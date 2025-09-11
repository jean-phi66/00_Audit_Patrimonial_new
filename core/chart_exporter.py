"""
Module pour l'exportation automatique des graphiques de toutes les pages en PNG.
Ce module analyse toutes les pages de l'application et sauvegarde les graphiques générés.
"""

import os
import re
import sys
import importlib.util
from datetime import datetime
import streamlit as st
import plotly.graph_objects as go
from pathlib import Path

class ChartExporter:
    """Classe pour exporter automatiquement tous les graphiques de l'application."""
    
    def __init__(self, export_dir="exports/charts"):
        """
        Initialise l'exporteur de graphiques.
        
        Args:
            export_dir (str): Répertoire de destination des exports
        """
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self.exported_charts = []
        
    def get_page_files(self):
        """Récupère la liste de tous les fichiers de pages."""
        pages_dir = Path("pages")
        page_files = []
        
        if pages_dir.exists():
            for file in pages_dir.glob("*.py"):
                if not file.name.startswith("__"):
                    page_files.append(file)
        
        return sorted(page_files)
    
    def get_chart_functions_from_file(self, file_path):
        """
        Analyse un fichier Python pour identifier les fonctions qui créent des graphiques.
        
        Args:
            file_path (Path): Chemin vers le fichier à analyser
            
        Returns:
            list: Liste des fonctions de création de graphiques trouvées
        """
        chart_functions = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Recherche des patterns de création de graphiques
            patterns = [
                r'fig\s*=\s*px\.',
                r'fig\s*=\s*go\.',
                r'fig\s*=\s*ff\.',
                r'create_.*_chart',
                r'create_.*_plot',
                r'create_.*_treemap',
                r'create_.*_waterfall',
                r'create_.*_bar',
                r'create_.*_line'
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.MULTILINE)
                for match in matches:
                    # Extraire le contexte autour du match
                    lines = content[:match.start()].split('\n')
                    line_num = len(lines)
                    
                    # Trouver le nom de la fonction ou du graphique
                    line_content = lines[-1] if lines else ""
                    
                    chart_functions.append({
                        'file': file_path.name,
                        'line': line_num,
                        'content': line_content.strip(),
                        'pattern': pattern
                    })
                    
        except Exception as e:
            st.error(f"Erreur lors de l'analyse du fichier {file_path}: {e}")
            
        return chart_functions
    
    def simulate_page_execution(self, page_file):
        """
        Simule l'exécution d'une page pour capturer les graphiques générés.
        Cette version améliore la gestion des erreurs et la capture des graphiques.
        
        Args:
            page_file (Path): Fichier de la page à exécuter
            
        Returns:
            list: Liste des graphiques capturés
        """
        charts_captured = []
        
        try:
            # Sauvegarde de l'état actuel
            original_plotly_chart = st.plotly_chart
            chart_counter = 0
            
            def capture_plotly_chart(fig, **kwargs):
                """Fonction qui intercepte les appels à st.plotly_chart"""
                nonlocal chart_counter
                chart_counter += 1
                
                if isinstance(fig, go.Figure):
                    # Générer un nom de fichier basé sur le titre du graphique et la page
                    chart_title = ""
                    if fig.layout.title and fig.layout.title.text:
                        chart_title = str(fig.layout.title.text)
                    else:
                        # Essayer d'extraire un titre des données du graphique
                        if fig.data:
                            trace = fig.data[0]
                            if hasattr(trace, 'name') and trace.name:
                                chart_title = str(trace.name)
                            elif hasattr(trace, 'hovertemplate') and trace.hovertemplate:
                                chart_title = f"chart_{chart_counter}"
                        else:
                            chart_title = f"chart_{chart_counter}"
                    
                    # Nettoyer le titre pour en faire un nom de fichier valide
                    chart_title = re.sub(r'[^\w\s-]', '', chart_title).strip()
                    chart_title = re.sub(r'[-\s]+', '_', chart_title)
                    if not chart_title:
                        chart_title = f"chart_{chart_counter}"
                    
                    page_name = page_file.stem
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{page_name}_{chart_title}_{timestamp}_{chart_counter}.png"
                    filepath = self.export_dir / filename
                    
                    # Sauvegarder le graphique
                    try:
                        # Configurer le graphique pour l'export
                        fig_copy = go.Figure(fig)
                        fig_copy.update_layout(
                            width=1200,
                            height=800,
                            showlegend=True,
                            title_font_size=16
                        )
                        
                        fig_copy.write_image(
                            str(filepath), 
                            width=1200, 
                            height=800, 
                            scale=2,
                            format='png'
                        )
                        
                        charts_captured.append({
                            'file': filename,
                            'path': str(filepath),
                            'page': page_name,
                            'title': chart_title,
                            'counter': chart_counter,
                            'success': True
                        })
                        
                        st.success(f"✅ Graphique sauvegardé: {filename}")
                        
                    except Exception as e:
                        charts_captured.append({
                            'file': filename,
                            'path': str(filepath),
                            'page': page_name,
                            'title': chart_title,
                            'counter': chart_counter,
                            'success': False,
                            'error': str(e)
                        })
                        
                        st.warning(f"⚠️ Erreur lors de la sauvegarde de {filename}: {e}")
                
                # Ne pas appeler la fonction originale pour éviter l'affichage
                # return original_plotly_chart(fig, **kwargs)
                return None
            
            # Remplacer temporairement st.plotly_chart
            st.plotly_chart = capture_plotly_chart
            
            # Créer un environnement d'exécution sécurisé
            try:
                # Lire le contenu du fichier
                with open(page_file, 'r', encoding='utf-8') as f:
                    page_content = f.read()
                
                # Créer un namespace d'exécution
                exec_globals = {
                    '__name__': '__main__',
                    '__file__': str(page_file),
                    'st': st,
                    'os': os,
                    'sys': sys,
                    'Path': Path,
                    'datetime': datetime,
                    # Ajouter d'autres imports communs si nécessaire
                }
                
                # Exécuter le code de la page
                exec(compile(page_content, str(page_file), 'exec'), exec_globals)
                
            except Exception as e:
                st.warning(f"Erreur lors de l'exécution de {page_file.name}: {e}")
                charts_captured.append({
                    'file': f"error_{page_file.stem}",
                    'path': '',
                    'page': page_file.stem,
                    'title': 'Erreur d\'exécution',
                    'counter': 0,
                    'success': False,
                    'error': str(e)
                })
            
            # Restaurer la fonction originale
            st.plotly_chart = original_plotly_chart
            
        except Exception as e:
            st.error(f"Erreur critique lors de la simulation de {page_file.name}: {e}")
        
        return charts_captured
    
    def export_all_charts(self, progress_callback=None):
        """
        Exporte tous les graphiques de toutes les pages.
        
        Args:
            progress_callback (callable): Fonction appelée pour mettre à jour la progression
            
        Returns:
            dict: Résumé de l'export
        """
        page_files = self.get_page_files()
        total_pages = len(page_files)
        
        export_summary = {
            'total_pages': total_pages,
            'processed_pages': 0,
            'total_charts': 0,
            'successful_exports': 0,
            'failed_exports': 0,
            'details': []
        }
        
        for i, page_file in enumerate(page_files):
            if progress_callback:
                progress_callback(i / total_pages, f"Traitement de {page_file.name}")
            
            # Analyser le fichier pour détecter les graphiques
            chart_functions = self.get_chart_functions_from_file(page_file)
            
            page_detail = {
                'page': page_file.name,
                'chart_functions_found': len(chart_functions),
                'charts_exported': [],
                'errors': []
            }
            
            if chart_functions:
                st.info(f"📊 Analyse de {page_file.name} - {len(chart_functions)} graphiques détectés")
                
                # Simuler l'exécution pour capturer les graphiques
                try:
                    captured_charts = self.simulate_page_execution(page_file)
                    page_detail['charts_exported'] = captured_charts
                    
                    for chart in captured_charts:
                        export_summary['total_charts'] += 1
                        if chart['success']:
                            export_summary['successful_exports'] += 1
                        else:
                            export_summary['failed_exports'] += 1
                            page_detail['errors'].append(chart.get('error', 'Erreur inconnue'))
                            
                except Exception as e:
                    page_detail['errors'].append(str(e))
                    st.error(f"Erreur lors du traitement de {page_file.name}: {e}")
            
            export_summary['processed_pages'] += 1
            export_summary['details'].append(page_detail)
        
        if progress_callback:
            progress_callback(1.0, "Export terminé")
        
        return export_summary
    
    def generate_export_report(self, export_summary):
        """
        Génère un rapport détaillé de l'export.
        
        Args:
            export_summary (dict): Résumé de l'export
            
        Returns:
            str: Rapport formaté
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""
# Rapport d'Export des Graphiques
**Date d'export:** {timestamp}

## Résumé
- **Pages traitées:** {export_summary['processed_pages']}/{export_summary['total_pages']}
- **Graphiques exportés:** {export_summary['successful_exports']}/{export_summary['total_charts']}
- **Échecs:** {export_summary['failed_exports']}

## Détails par page
"""
        
        for detail in export_summary['details']:
            report += f"\n### {detail['page']}\n"
            report += f"- Fonctions graphiques détectées: {detail['chart_functions_found']}\n"
            report += f"- Graphiques exportés: {len(detail['charts_exported'])}\n"
            
            if detail['charts_exported']:
                report += "\n**Graphiques exportés:**\n"
                for chart in detail['charts_exported']:
                    status = "✅" if chart['success'] else "❌"
                    report += f"- {status} {chart['file']}\n"
            
            if detail['errors']:
                report += "\n**Erreurs:**\n"
                for error in detail['errors']:
                    report += f"- ❌ {error}\n"
        
        return report
    
    def save_report(self, export_summary):
        """
        Sauvegarde le rapport d'export.
        
        Args:
            export_summary (dict): Résumé de l'export
        """
        report = self.generate_export_report(export_summary)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.export_dir / f"export_report_{timestamp}.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return report_file
