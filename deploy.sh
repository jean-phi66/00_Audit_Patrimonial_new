#!/bin/bash

# Script de déploiement pour Google Cloud Run
# Déploiement de l'application Streamlit Audit Patrimonial

set -e  # Arrêter le script en cas d'erreur

# Configuration
PROJECT_ID="audit-patrimonial-1757744052"  # Votre Project ID Google Cloud
SERVICE_NAME="audit-patrimonial"
REGION="europe-west1"  # Région européenne
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Déploiement de l'application Audit Patrimonial sur Google Cloud Run${NC}"

# Vérification des prérequis
echo -e "${YELLOW}📋 Vérification des prérequis...${NC}"

# Vérifier si gcloud est installé
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ Google Cloud CLI (gcloud) n'est pas installé${NC}"
    echo "Veuillez installer gcloud: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Vérifier si Docker est installé
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker n'est pas installé${NC}"
    echo "Veuillez installer Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Demander le Project ID s'il n'est pas défini
if [ -z "$PROJECT_ID" ]; then
    echo -e "${YELLOW}🔍 Veuillez entrer votre Google Cloud Project ID:${NC}"
    read -p "Project ID: " PROJECT_ID
    
    if [ -z "$PROJECT_ID" ]; then
        echo -e "${RED}❌ Project ID requis${NC}"
        exit 1
    fi
    
    # Mettre à jour la variable IMAGE_NAME
    IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
fi

echo -e "${GREEN}✅ Project ID: ${PROJECT_ID}${NC}"

# Authentification et configuration du projet
echo -e "${YELLOW}🔐 Configuration du projet Google Cloud...${NC}"
gcloud config set project $PROJECT_ID

# Activer les APIs nécessaires
echo -e "${YELLOW}🔧 Activation des APIs Google Cloud...${NC}"
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Construction de l'image Docker
echo -e "${YELLOW}🏗️  Construction de l'image Docker...${NC}"
docker build --platform linux/amd64 -t $IMAGE_NAME .

# Configuration de Docker pour Google Cloud Registry
echo -e "${YELLOW}🔑 Configuration de Docker pour Google Cloud Registry...${NC}"
gcloud auth configure-docker

# Push de l'image vers Google Container Registry
echo -e "${YELLOW}📤 Push de l'image vers Google Container Registry...${NC}"
docker push $IMAGE_NAME

# Déploiement sur Cloud Run
echo -e "${YELLOW}🚀 Déploiement sur Google Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 8080 \
    --memory 2Gi \
    --cpu 1 \
    --max-instances 10 \
    --set-env-vars="STREAMLIT_SERVER_PORT=8080,STREAMLIT_SERVER_ADDRESS=0.0.0.0,STREAMLIT_SERVER_HEADLESS=true,STREAMLIT_BROWSER_GATHER_USAGE_STATS=false"

# Obtenir l'URL du service
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)')

echo -e "${GREEN}🎉 Déploiement réussi !${NC}"
echo -e "${GREEN}🌐 URL de votre application: ${SERVICE_URL}${NC}"
echo ""
echo -e "${YELLOW}📝 Commandes utiles:${NC}"
echo "• Voir les logs: gcloud run services logs tail $SERVICE_NAME --region $REGION"
echo "• Mettre à jour: ./deploy.sh"
echo "• Supprimer le service: gcloud run services delete $SERVICE_NAME --region $REGION"
echo ""
echo -e "${GREEN}✅ Votre application Streamlit est maintenant accessible publiquement !${NC}"