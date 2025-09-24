#!/usr/bin/env python3
"""
Script de nettoyage pour supprimer tous les fichiers de test et de démonstration.
"""

import os
import shutil
import glob

def cleanup():
    """Nettoie tous les fichiers générés par les tests et démonstrations."""
    print("🧹 Nettoyage des fichiers de test et démonstration...")
    
    # Dossiers à supprimer
    folders_to_remove = [
        'charts_output',
        'test_png', 
        'demo_complete',
        'demo_png',
        'demo_html'
    ]
    
    # Fichiers à supprimer
    files_to_remove = [
        'demo_data.json',
        'example_data.json'  # Optionnel: garder pour les futurs tests
    ]
    
    removed_count = 0
    
    # Supprimer les dossiers
    for folder in folders_to_remove:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"✅ Dossier supprimé: {folder}/")
            removed_count += 1
        else:
            print(f"ℹ️  Dossier inexistant: {folder}/")
    
    # Supprimer les fichiers (sauf example_data.json qui peut servir)
    files_to_remove_filtered = [f for f in files_to_remove if f != 'example_data.json']
    
    for file in files_to_remove_filtered:
        if os.path.exists(file):
            os.remove(file)
            print(f"✅ Fichier supprimé: {file}")
            removed_count += 1
        else:
            print(f"ℹ️  Fichier inexistant: {file}")
    
    if removed_count == 0:
        print("✨ Aucun fichier à nettoyer - workspace déjà propre !")
    else:
        print(f"🎉 Nettoyage terminé - {removed_count} éléments supprimés")
        print("📖 Le fichier example_data.json a été conservé pour les futurs tests")

if __name__ == "__main__":
    cleanup()