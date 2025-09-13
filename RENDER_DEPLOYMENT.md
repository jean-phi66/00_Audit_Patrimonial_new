# Configuration Render.com pour déploiement automatique

## 1. Dans le dashboard Render.com :

### Settings > Build & Deploy :
- **Build Command** : `pip install -r requirements.txt`
- **Start Command** : `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true`
- **Auto-Deploy** : `Yes` (pour déploiement automatique sur push)

### Environment Variables :
```
PORT=10000
STREAMLIT_SERVER_PORT=10000
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
```

### Runtime :
- **Runtime** : `Python 3`
- **Python Version** : `3.12`

## 2. Fichiers optionnels à ajouter au repo :

### render.yaml (déploiement Infrastructure as Code)
```yaml
services:
  - type: web
    name: audit-patrimonial
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
    envVars:
      - key: STREAMLIT_SERVER_HEADLESS
        value: true
      - key: STREAMLIT_BROWSER_GATHER_USAGE_STATS
        value: false
```

## 3. Vérifier le déploiement :
Une fois configuré, chaque push sur la branche main déclenchera automatiquement un nouveau déploiement.