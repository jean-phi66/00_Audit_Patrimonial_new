# 🏛️ Nouvelle Fonctionnalité : Calcul Automatique de l'Impôt sur le Revenu

## 📋 Description

J'ai ajouté une nouvelle fonctionnalité à la page **Flux** qui calcule automatiquement l'impôt sur le revenu mensuel en fonction des revenus du foyer.

## ✨ Fonctionnalités Ajoutées

### 1. Calcul Automatique de l'IR
- **Calcul intelligent** : Utilise OpenFisca quand disponible pour un calcul précis
- **Fallback robuste** : Calcul simplifié basé sur les tranches 2024 si OpenFisca n'est pas disponible
- **Prise en compte** :
  - Salaires des parents
  - Revenus fonciers nets
  - Nombre d'enfants à charge
  - Situation familiale (parent isolé ou couple)

### 2. Interface Utilisateur Améliorée
- **Section dédiée** : "🏛️ Fiscalité (auto)" séparée des autres dépenses automatiques
- **Contrôle utilisateur** : Option dans la sidebar pour activer/désactiver le calcul automatique
- **Information contextuelle** : Bouton d'aide expliquant le calcul

### 3. Option de Configuration
- **Checkbox dans la sidebar** : "🏛️ Calcul automatique de l'impôt sur le revenu"
- **Par défaut activé** : Le calcul automatique est activé par défaut
- **Flexibilité** : Possibilité de désactiver et saisir manuellement si souhaité

## 🔧 Modifications Techniques

### Fichiers Modifiés

#### `core/fiscal_logic.py`
- **Nouvelle fonction** : `calculate_monthly_income_tax()` 
  - Calcul principal avec OpenFisca
  - Gestion des erreurs robuste
- **Nouvelle fonction** : `calculate_simple_income_tax_monthly()`
  - Calcul de fallback avec les tranches d'imposition 2024
  - Prise en compte des parts fiscales

#### `core/flux_logic.py`
- **Import ajouté** : `from core.fiscal_logic import calculate_monthly_income_tax`
- **Modification de** : `sync_all_flux_data()`
  - Ajout du calcul automatique de l'IR
  - Respect de l'option utilisateur `auto_ir_enabled`
  - Création d'une dépense automatique avec `source_id: 'fiscal_auto'`

#### `core/flux_display.py`
- **Modification de** : `display_depenses_ui()`
  - Séparation des dépenses automatiques par type
  - Section dédiée pour la fiscalité
  - Bouton d'information pour expliquer le calcul

#### `pages/4_Flux.py`
- **Ajout sidebar** : Options de configuration
- **Contrôle utilisateur** : Checkbox pour activer/désactiver l'IR automatique
- **Persistance** : Sauvegarde de la préférence utilisateur

## 📊 Exemple de Calcul

Pour un foyer avec :
- **Jean** : 4000€/mois (48000€/an)
- **Marie** : 3500€/mois (42000€/an)
- **2 enfants** à charge
- **Revenus fonciers** : 0€

**Calcul simplifié** :
- Revenus totaux : 90000€/an
- Parts fiscales : 3 (2 adultes + 2×0.5 enfants)
- Revenu par part : 30000€
- Tranche applicable : 11% sur la partie > 11294€
- IR annuel estimé : ~2058€
- **IR mensuel : ~172€**

## 🎯 Avantages

1. **Automatisation** : Plus besoin de calculer manuellement l'IR
2. **Précision** : Utilise OpenFisca quand possible pour des calculs officiels
3. **Mise à jour automatique** : Se recalcule quand les revenus changent
4. **Flexibilité** : Peut être désactivé si l'utilisateur préfère saisir manuellement
5. **Intégration transparente** : S'intègre naturellement dans le flux existant

## 🚀 Utilisation

1. **Renseigner les salaires** dans la section "Revenus"
2. **Le calcul s'effectue automatiquement** et apparaît dans "🏛️ Fiscalité (auto)"
3. **Possibilité de désactiver** via la sidebar si besoin
4. **Le montant se met à jour** automatiquement quand les revenus changent

## 🔮 Évolutions Futures Possibles

- Calcul des acomptes trimestriels
- Prise en compte de réductions d'impôts spécifiques
- Simulation de l'impact fiscal de nouveaux investissements
- Intégration avec d'autres pages pour l'optimisation fiscale
