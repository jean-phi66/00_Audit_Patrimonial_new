# Utiliser Python 3.12 comme image de base
FROM python:3.12-slim

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de requirements
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code de l'application
COPY . .

# Créer un utilisateur non-root pour la sécurité
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Exposer le port que Streamlit utilise
EXPOSE 8080

# Variables d'environnement pour Cloud Run
ENV PORT=8080

# Commande pour démarrer l'application avec streamlit run
CMD streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true --server.runOnSave=false --server.allowRunOnSave=false