# 🚀 Guide de déploiement sur Google Cloud

Ce guide vous explique comment déployer votre application Streamlit "Audit Patrimonial" sur Google Cloud Run.

## 📋 Prérequis

### 1. Compte Google Cloud
- Créez un compte sur [Google Cloud Console](https://console.cloud.google.com/)
- Créez un nouveau projet ou utilisez un projet existant
- Activez la facturation (Google Cloud offre des crédits gratuits pour débuter)

### 2. Outils nécessaires
- **Google Cloud CLI** : [Guide d'installation](https://cloud.google.com/sdk/docs/install)
- **Docker** : [Guide d'installation](https://docs.docker.com/get-docker/)

### 3. Configuration initiale
```bash
# Installer Google Cloud CLI (macOS)
brew install --cask google-cloud-sdk

# Authentification
gcloud auth login

# Lister vos projets (optionnel)
gcloud projects list
```

## 🚀 Déploiement automatique

### Option 1 : Script automatisé (Recommandé)
```bash
# Exécuter le script de déploiement
./deploy.sh
```

Le script va :
1. Vérifier les prérequis
2. Demander votre Project ID Google Cloud
3. Activer les APIs nécessaires
4. Construire l'image Docker
5. La pousser vers Google Container Registry
6. Déployer sur Cloud Run

### Option 2 : Déploiement manuel

#### Étape 1 : Configuration
```bash
# Définir vos variables
export PROJECT_ID="votre-project-id"
export SERVICE_NAME="audit-patrimonial"
export REGION="europe-west1"

# Configurer le projet
gcloud config set project $PROJECT_ID
```

#### Étape 2 : Activer les services
```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

#### Étape 3 : Construction et déploiement
```bash
# Construire l'image
docker build -t gcr.io/$PROJECT_ID/$SERVICE_NAME .

# Configurer Docker pour GCR
gcloud auth configure-docker

# Pousser l'image
docker push gcr.io/$PROJECT_ID/$SERVICE_NAME

# Déployer sur Cloud Run
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 8080 \
    --memory 2Gi \
    --cpu 1 \
    --max-instances 10
```

## 📊 Monitoring et gestion

### Voir les logs
```bash
gcloud run services logs tail audit-patrimonial --region europe-west1
```

### Mettre à jour l'application
```bash
# Reconstruire et redéployer
./deploy.sh
```

### Supprimer le service
```bash
gcloud run services delete audit-patrimonial --region europe-west1
```

## 💰 Coûts estimés

Google Cloud Run utilise un modèle de tarification "pay-as-you-go" :
- **Gratuit** : 2 millions de requêtes par mois
- **CPU** : ~0,000024€ par seconde de CPU
- **Mémoire** : ~0,0000025€ par seconde de Go de RAM
- **Requêtes** : 0,40€ par million de requêtes

Pour une application peu sollicitée, les coûts restent très faibles (quelques euros par mois).

## 🔧 Configuration avancée

### Variables d'environnement
Vous pouvez ajouter des variables d'environnement lors du déploiement :
```bash
gcloud run deploy audit-patrimonial \
    --set-env-vars="VAR1=value1,VAR2=value2"
```

### Domaine personnalisé
1. Allez dans Google Cloud Console > Cloud Run
2. Sélectionnez votre service
3. Cliquez sur "Gérer les domaines personnalisés"
4. Suivez les instructions pour configurer votre domaine

### Authentification
Pour restreindre l'accès :
```bash
# Supprimer l'accès public
gcloud run services remove-iam-policy-binding audit-patrimonial \
    --member="allUsers" \
    --role="roles/run.invoker" \
    --region europe-west1

# Ajouter des utilisateurs spécifiques
gcloud run services add-iam-policy-binding audit-patrimonial \
    --member="user:email@example.com" \
    --role="roles/run.invoker" \
    --region europe-west1
```

## 🆘 Dépannage

### Problèmes fréquents

1. **Erreur de permissions** :
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Image trop lourde** :
   - Vérifiez le fichier `.dockerignore`
   - Utilisez une image de base plus légère

3. **Timeout au démarrage** :
   - Augmentez la mémoire allouée
   - Optimisez le temps de démarrage de Streamlit

4. **Erreurs de dépendances** :
   - Vérifiez le fichier `requirements.txt`
   - Testez localement avec Docker

### Logs de débogage
```bash
# Logs en temps réel
gcloud run services logs tail audit-patrimonial --region europe-west1 --format="table(time, severity, message)"

# Logs avec filtre
gcloud run services logs read audit-patrimonial --region europe-west1 --filter="severity>=ERROR"
```

## 📚 Ressources utiles

- [Documentation Google Cloud Run](https://cloud.google.com/run/docs)
- [Guide Streamlit + Cloud Run](https://cloud.google.com/blog/topics/developers-practitioners/deploy-streamlit-apps-cloud-run)
- [Tarification Cloud Run](https://cloud.google.com/run/pricing)
- [Limites de Cloud Run](https://cloud.google.com/run/quotas)

## ✅ Checklist de déploiement

- [ ] Compte Google Cloud créé et configuré
- [ ] Google Cloud CLI installé et authentifié
- [ ] Docker installé
- [ ] Project ID défini
- [ ] APIs activées (Cloud Build, Cloud Run, Container Registry)
- [ ] Application testée localement
- [ ] Script de déploiement exécuté
- [ ] URL de l'application testée
- [ ] Logs vérifiés

---

🎉 **Félicitations !** Votre application Streamlit est maintenant déployée sur Google Cloud et accessible publiquement !