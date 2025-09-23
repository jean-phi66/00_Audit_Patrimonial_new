# 🚀 Comment lancer l'application Audit Patrimonial

## 🔧 Méthode 1 : Script automatique (RECOMMANDÉ)

```bash
./start_app.sh
```

Ou double-cliquez sur le fichier `start_app.sh` dans le Finder.

## 🔧 Méthode 2 : Commande manuelle

```bash
streamlit run app.py --server.port=8501 --server.address=localhost
```

Puis ouvrez votre navigateur à : **http://localhost:8501**

## 🌐 Accès à l'application

Une fois lancée, l'application sera accessible à :
- **URL principale :** http://localhost:8501
- **URL alternative :** http://127.0.0.1:8501

## ❗ Problèmes courants

### L'application ne s'ouvre pas dans le navigateur
1. ✅ Vérifiez que l'application est bien lancée (message "You can now view your Streamlit app...")
2. ✅ Ouvrez **MANUELLEMENT** votre navigateur
3. ✅ Tapez l'URL : `http://localhost:8501`
4. ✅ Assurez-vous qu'aucun autre processus n'utilise le port 8501

### Page blanche ou erreur 404
1. ✅ Vérifiez l'URL exacte : `http://localhost:8501` (pas 8080 ou autre)
2. ✅ Attendez quelques secondes que l'application se charge complètement
3. ✅ Rafraîchissez la page (F5 ou Cmd+R)

### Erreur de port occupé
```bash
# Arrêter tous les processus Streamlit
pkill -f streamlit

# Relancer l'application
./start_app.sh
```

## 💡 Notes importantes

- ⚠️ **Ne fermez pas le terminal** tant que vous utilisez l'application
- ⚠️ Pour arrêter l'application : `Ctrl+C` dans le terminal
- ⚠️ L'application ne s'ouvre pas toujours automatiquement dans le navigateur
- ✅ Si ça ne marche pas, ouvrez **manuellement** http://localhost:8501

## 🆘 En cas de problème persistant

1. Redémarrez votre terminal
2. Lancez : `./start_app.sh`
3. Ouvrez manuellement : http://localhost:8501