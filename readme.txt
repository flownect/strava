# 🏃‍♂️ Strava Analytics

Système complet d'analyse des données d'entraînement Strava avec API backend, base de données PostgreSQL et analyses temporelles avancées.

## ✨ Fonctionnalités

- 🔐 **Authentification Strava OAuth 2.0**
- 📊 **Analyses temporelles complètes** (jour, semaine, mois, année)
- 📈 **Statistiques avancées** par type d'activité
- 📅 **Vue calendrier** des activités
- 🏆 **Records personnels** et progression
- 📤 **Export CSV** des données
- 🔄 **Synchronisation automatique** des nouvelles activités
- 🐳 **Déploiement Docker** prêt pour production

## 🚀 Installation rapide

### Prérequis
- Docker et Docker Compose
- Compte Strava avec application API créée

### 1. Créer le projet

```bash
# Dans Documents/dev
cd ~/Documents/dev
mkdir strava-analytics && cd strava-analytics
```

### 2. Configuration Strava API

1. Allez sur https://www.strava.com/settings/api
2. Créez une nouvelle application avec :
   - **Authorization Callback Domain** : `localhost`
   - **Website** : `http://localhost:58001`
3. Notez votre `Client ID` et `Client Secret`

### 3. Configuration du projet

```bash
# Copier le fichier d'environnement
cp .env.example .env

# Éditer avec vos paramètres Strava
nano .env
```

Configurez dans `.env` :
```env
STRAVA_CLIENT_ID=votre_client_id
STRAVA_CLIENT_SECRET=votre_client_secret
STRAVA_REDIRECT_URI=http://localhost:58001/auth/strava/callback
```

### 4. Lancement

```bash
# Installation et démarrage automatique
make install

# Ou manuellement
make build
make up
```

### 5. Première utilisation

1. Ouvrir http://localhost:58001
2. Aller sur http://localhost:58001/auth/strava
3. Autoriser l'application Strava
4. Vos activités seront synchronisées automatiquement !

## 📋 Commandes principales

```bash
make help          # Voir toutes les commandes
make up            # Démarrer les services
make logs          # Voir les logs
make status        # Statut des services
make backup        # Sauvegarder la base
make stop          # Arrêter les services
make clean         # Nettoyage complet
```

## 🌐 Endpoints API

### Authentification
- `GET /auth/strava` - Authentification Strava
- `GET /auth/status` - Statut des athlètes connectés

### Activités  
- `GET /api/activities/athlete/{id}` - Liste des activités
- `GET /api/activities/athlete/{id}/export` - Export CSV
- `GET /api/activities/athlete/{id}/sync` - Sync manuelle

### Analytics
- `GET /api/analytics/athlete/{id}/monthly` - Stats mensuelles
- `GET /api/analytics/athlete/{id}/day-of-week` - Stats par jour
- `GET /api/analytics/athlete/{id}/calendar` - Vue calendrier
- `GET /api/analytics/athlete/{id}/trends` - Analyse tendances
- `GET /api/analytics/athlete/{id}/comparison` - Comparaison années
- `GET /api/analytics/athlete/{id}/dashboard` - Résumé général

## 📊 Exemples d'analyses

### Statistiques mensuelles
```bash
curl "http://localhost:58001/api/analytics/athlete/1/monthly?months=6"
```

### Activités par jour de la semaine
```bash
curl "http://localhost:58001/api/analytics/athlete/1/day-of-week"
```

### Export CSV des activités
```bash
curl "http://localhost:58001/api/activities/athlete/1/export?year=2024" > mes_activites_2024.csv
```

## 🗂️ Structure des données

### Données temporelles capturées
- **Jour** : Lundi, Mardi, Mercredi...
- **Date** : Jour du mois (1-31)
- **Mois** : Janvier, Février, Mars...
- **Année** : 2024, 2023...
- **Semaine** : Numéro ISO (1-53)

### Métriques analysées
- Distance (km)
- Temps de mouvement (heures)
- Vitesse moyenne/maximale
- Dénivelé positif
- Fréquence cardiaque
- Calories
- Type d'activité (Course, Vélo, Natation...)

## 🔧 Configuration avancée

### Variables d'environnement

```env
# Base de données
POSTGRES_USER=strava_user
POSTGRES_PASSWORD=votre_mot_de_passe
POSTGRES_DB=strava_analytics_db

# Strava API
STRAVA_CLIENT_ID=votre_client_id
STRAVA_CLIENT_SECRET=votre_client_secret
STRAVA_REDIRECT_URI=http://localhost:58001/auth/strava/callback

# Application
FLASK_SECRET_KEY=votre_cle_secrete
```

### Synchronisation automatique

Le système synchronise automatiquement :
- **Sync complète** : Tous les jours à 6h00
- **Sync rapide** : Toutes les 2h de 8h à 22h
- **Health check** : Toutes les heures

### Personnaliser les horaires

Éditez `api/sync_scheduler.py` pour modifier les horaires :

```python
# Sync quotidienne à 7h au lieu de 6h
scheduler.add_job(sync_all_athletes, 'cron', hour=7, minute=0)
```

## 🐳 Architecture Docker

### Services
- **API** : Flask + SQLAlchemy (port 58001)
- **Database** : PostgreSQL 15 (port 5433)
- **Sync** : Scheduler automatique

### Volumes persistants
- `postgres-data` : Données PostgreSQL
- `./database/backup` : Sauvegardes
- `./data/exports` : Exports CSV

## 🛠️ Développement

### Structure du projet
```
strava-analytics/
├── api/                    # Code Python Flask
│   ├── models/            # Modèles de données
│   ├── services/          # Services métier
│   ├── routes/            # Routes API
│   └── app.py            # Application principale
├── database/              # Configuration base
├── data/                  # Données et exports
└── docker-compose.yml     # Configuration Docker
```

### Mode développement
```bash
make dev  # Démarre avec rebuild automatique
```

### Accès direct aux services
```bash
make shell-api  # Shell du container API
make shell-db   # Console PostgreSQL
```

## 📈 Exemples d'utilisation

### Analyser vos performances
```python
# Via l'API Python
import requests

# Récupérer vos stats mensuelles
response = requests.get('http://localhost:58001/api/analytics/athlete/1/monthly')
stats = response.json()

for month in stats['monthly_stats']:
    print(f"{month['month_name']} {month['year']}: {month['total_km']} km")
```

### Dashboard personnel
```bash
# Résumé complet de vos activités
curl "http://localhost:58001/api/analytics/athlete/1/dashboard" | jq
```

## 🔒 Sécurité

- Tokens Strava chiffrés en base
- Rate limiting respecté (100 req/15min)
- Refresh automatique des tokens
- Validation des entrées API
- Logs sécurisés

## 📱 Intégrations possibles

Le système expose une API REST complète pour intégrer avec :
- Applications mobiles
- Tableaux de bord (Grafana, Tableau)
- Scripts d'analyse personnalisés
- Systèmes de notification
- Applications web tierces

## 🆘 Dépannage

### Problèmes courants

**API ne démarre pas**
```bash
make logs-api  # Voir les erreurs
```

**Authentification Strava échoue**
- Vérifier `STRAVA_CLIENT_ID` et `STRAVA_CLIENT_SECRET` dans `.env`
- Vérifier que `STRAVA_REDIRECT_URI` correspond à la config Strava

**Base de données inaccessible**
```bash
make shell-db  # Tester la connexion
```

**Aucune activité synchronisée**
- Vérifier les logs : `make logs-sync`
- Forcer une sync : `curl http://localhost:58001/api/activities/athlete/1/sync`

### Logs utiles
```bash
make logs       # Tous les logs
make logs-api   # API seulement
make logs-sync  # Synchroniseur
make logs-db    # PostgreSQL
```

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature
3. Commit vos changements
4. Push vers la branche
5. Ouvrir une Pull Request

## 📄 Licence

MIT License - Voir le fichier LICENSE pour les détails.

## 🙏 Remerciements

- [Strava API](https://developers.strava.com/) pour l'accès aux données
- [Flask](https://flask.palletsprojects.com/) pour le framework web
- [PostgreSQL](https://www.postgresql.org/) pour la base de données
- [Docker](https://www.docker.com/) pour la containerisation

---

**🎯 Prêt à analyser vos performances sportives ? Lancez `make install` et c'est parti !** 🚀