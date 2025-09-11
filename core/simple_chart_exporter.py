"""
Version simplifiée de l'exporteur de graphiques.
Cette version se concentre sur l'identification et la création de graphiques types
sans exécuter complètement les pages.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime
import re
import os

class SimpleChartExporter:
    """Version simplifiée de l'exporteur de graphiques."""
    
    def __init__(self, export_dir="exports/charts"):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)
        
    def create_sample_charts(self):
        """
        Crée des graphiques d'exemple basés sur les types couramment utilisés 
        dans l'application.
        """
        charts = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. Graphique treemap du patrimoine
        df_patrimoine = pd.DataFrame({
            'Type': ['Immobilier', 'Immobilier', 'Financier', 'Financier', 'Autres'],
            'Libellé': ['Résidence principale', 'Immobilier locatif', 'Assurance vie', 'PEA', 'Voiture'],
            'Valeur': [300000, 150000, 80000, 45000, 15000]
        })
        
        fig_treemap = px.treemap(
            df_patrimoine, 
            path=['Type', 'Libellé'], 
            values='Valeur',
            title="Répartition du Patrimoine"
        )
        
        charts.append({
            'fig': fig_treemap,
            'name': f"patrimoine_treemap_{timestamp}",
            'title': "Répartition du Patrimoine"
        })
        
        # 2. Graphique de projection
        years = list(range(2024, 2045))
        patrimoine_values = [500000 + i * 20000 + (i**2) * 500 for i in range(len(years))]
        
        fig_projection = go.Figure()
        fig_projection.add_trace(go.Scatter(
            x=years,
            y=patrimoine_values,
            mode='lines+markers',
            name='Patrimoine projeté',
            line=dict(width=3)
        ))
        fig_projection.update_layout(
            title="Projection du Patrimoine",
            xaxis_title="Année",
            yaxis_title="Patrimoine (€)",
            hovermode='x unified'
        )
        
        charts.append({
            'fig': fig_projection,
            'name': f"patrimoine_projection_{timestamp}",
            'title': "Projection du Patrimoine"
        })
        
        # 3. Graphique en barres des revenus/dépenses
        categories = ['Salaires', 'Revenus locatifs', 'Autres revenus', 'Charges courantes', 'Impôts']
        values = [60000, 12000, 5000, -35000, -15000]
        colors = ['green' if v > 0 else 'red' for v in values]
        
        fig_flux = go.Figure(data=[
            go.Bar(x=categories, y=values, marker_color=colors)
        ])
        fig_flux.update_layout(
            title="Flux Annuels - Revenus et Dépenses",
            xaxis_title="Catégorie",
            yaxis_title="Montant (€)"
        )
        
        charts.append({
            'fig': fig_flux,
            'name': f"flux_revenus_depenses_{timestamp}",
            'title': "Flux Annuels"
        })
        
        # 4. Graphique immobilier - évolution valeur
        years_immo = list(range(2020, 2030))
        valeur_bien = [250000 * (1.03 ** i) for i in range(len(years_immo))]
        capital_restant = [200000 * (0.9 ** i) for i in range(len(years_immo))]
        
        fig_immo = go.Figure()
        fig_immo.add_trace(go.Scatter(
            x=years_immo, y=valeur_bien, name='Valeur du bien',
            line=dict(color='blue', width=3)
        ))
        fig_immo.add_trace(go.Scatter(
            x=years_immo, y=capital_restant, name='Capital restant dû',
            line=dict(color='red', width=3)
        ))
        fig_immo.update_layout(
            title="Évolution Immobilière",
            xaxis_title="Année",
            yaxis_title="Valeur (€)"
        )
        
        charts.append({
            'fig': fig_immo,
            'name': f"immobilier_evolution_{timestamp}",
            'title': "Évolution Immobilière"
        })
        
        # 5. Graphique en secteurs de répartition d'actifs
        labels = ['Immobilier', 'Assurance vie', 'Actions', 'Livret A', 'Autres']
        sizes = [65, 15, 10, 5, 5]
        
        fig_pie = go.Figure(data=[go.Pie(labels=labels, values=sizes)])
        fig_pie.update_layout(title="Répartition des Actifs")
        
        charts.append({
            'fig': fig_pie,
            'name': f"repartition_actifs_{timestamp}",
            'title': "Répartition des Actifs"
        })
        
        return charts
    
    def export_sample_charts(self):
        """Exporte les graphiques d'exemple."""
        charts = self.create_sample_charts()
        results = []
        
        for chart in charts:
            try:
                filename = f"{chart['name']}.png"
                filepath = self.export_dir / filename
                
                chart['fig'].write_image(
                    str(filepath),
                    width=1200,
                    height=800,
                    scale=2
                )
                
                results.append({
                    'name': chart['name'],
                    'title': chart['title'],
                    'file': filename,
                    'path': str(filepath),
                    'success': True
                })
                
            except Exception as e:
                results.append({
                    'name': chart['name'],
                    'title': chart['title'],
                    'file': f"{chart['name']}.png",
                    'path': '',
                    'success': False,
                    'error': str(e)
                })
        
        return results
    
    def analyze_page_for_chart_patterns(self, page_file):
        """
        Analyse une page pour identifier les patterns de graphiques
        sans exécuter le code.
        """
        patterns_found = []
        
        try:
            with open(page_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Patterns de détection de graphiques
            chart_patterns = {
                'treemap': r'(px\.treemap|treemap)',
                'bar_chart': r'(px\.bar|go\.Bar)',
                'line_chart': r'(px\.line|go\.Scatter)',
                'pie_chart': r'(px\.pie|go\.Pie)',
                'scatter': r'(px\.scatter)',
                'waterfall': r'(go\.Waterfall)',
                'plotly_chart': r'st\.plotly_chart'
            }
            
            for pattern_name, pattern in chart_patterns.items():
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    # Trouver la ligne
                    lines_before = content[:match.start()].count('\n')
                    line_content = content.split('\n')[lines_before] if lines_before < len(content.split('\n')) else ""
                    
                    patterns_found.append({
                        'type': pattern_name,
                        'line': lines_before + 1,
                        'content': line_content.strip(),
                        'file': page_file.name
                    })
            
        except Exception as e:
            st.error(f"Erreur lors de l'analyse de {page_file}: {e}")
        
        return patterns_found
    
    def get_all_chart_patterns(self):
        """Analyse toutes les pages pour les patterns de graphiques."""
        pages_dir = Path("pages")
        all_patterns = {}
        
        if pages_dir.exists():
            for page_file in pages_dir.glob("*.py"):
                if not page_file.name.startswith("__"):
                    patterns = self.analyze_page_for_chart_patterns(page_file)
                    if patterns:
                        all_patterns[page_file.name] = patterns
        
        return all_patterns
