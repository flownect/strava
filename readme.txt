# 🏃‍♂️ Strava Analytics - Dashboard Groupe

Système d'analyse avancé des données Strava avec dashboard web et authentification multi-utilisateurs pour comparer les performances entre amis.

## 📋 Vue d'ensemble

### Fonctionnalités principales

#### 🔐 Système personnel
- Authentification Strava OAuth 2.0
- Synchronisation automatique de vos activités
- Calculs de métriques personnalisées (TSS, zones, records)
- Dashboard sport-km avec filtres avancés (vélo, course, home trainer)
- Export CSV enrichi

#### 👥 Système groupe
- Invitation d'amis via interface web Firebase
- Authentification OAuth individuelle pour chaque ami
- Tableau de bord comparatif entre membres du groupe
- Stats de groupe privées et sécurisées
- Gestion multi-utilisateurs

### Technologies utilisées
- **Backend** : Python Flask + PostgreSQL
- **Frontend** : HTML/CSS/JavaScript + Chart.js
- **Hébergement web** : Firebase Hosting
- **Tunnel local** : ngrok (développement)
- **Containerisation** : Docker + Docker Compose

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────┐
│    Strava API   │◄──►│  Firebase Web    │◄──►│   Amis      │
│   OAuth Flow    │    │   (Interface)    │    │ (Invités)   │
└─────────────────┘    └──────────────────┘    └─────────────┘
         ▲                        │                           
         │                        ▼                           
┌─────────────────┐    ┌──────────────────┐                  
│      ngrok      │◄──►│   API Flask      │                  
│    (Tunnel)     │    │  (Backend Local) │                  
└─────────────────┘    └──────────────────┘                  
                                │                           
                       ┌──────────────────┐                  
                       │   PostgreSQL     │                  
                       │  (Base données)  │                  
                       └──────────────────┘                  
```

## ✅ Prérequis

### Comptes nécessaires
- **Strava Developer Account** : https://www.strava.com/settings/api
- **Firebase Account** : https://console.firebase.google.com
- **ngrok Account** : https://dashboard.ngrok.com (gratuit)

### Logiciels requis
- Docker 20.x+ et Docker Compose 2.x+
- Node.js 16.x+ (pour Firebase CLI)
- Python 3.8+

## 🚀 Installation rapide

```bash
# 1. Cloner le projet
cd ~/Documents/dev
git clone https://github.com/VOTRE-USERNAME/strava-analytics.git
cd strava-analytics

# 2. Configuration
cp .env.example .env
# Modifier .env avec vos identifiants Strava

# 3. Démarrer l'API locale
make up

# 4. Installer Firebase CLI
npm install -g firebase-tools
firebase login

# 5. Configurer Firebase
mkdir firebase-app && cd firebase-app
firebase init
# Choisir : Hosting, projet existant, public directory: public

# 6. Installer ngrok
brew install ngrok/ngrok/ngrok
ngrok config add-authtoken VOTRE_AUTHTOKEN
```

## ⚙️ Configuration

### Variables principales (.env)
```env
# Strava API
STRAVA_CLIENT_ID=161590
STRAVA_CLIENT_SECRET=abc123def456...

# Base de données
POSTGRES_USER=strava_user
POSTGRES_PASSWORD=mot_de_passe_securise
POSTGRES_DB=strava_analytics_db
POSTGRES_PORT=5433

# Application
FLASK_SECRET_KEY=cle_secrete_unique
```

### Configuration Firebase (firebase-app/public/js/config.js)
```javascript
const CONFIG = {
    STRAVA_CLIENT_ID: '161590',
    STRAVA_REDIRECT_URI: 'https://strava-jerome.web.app/callback.html',
    API_BASE_URL: 'https://1455-78-245-248-89.ngrok-free.app',
    STRAVA_SCOPES: 'read_all,activity:read_all'
};
```

### ⚠️ Configuration Strava OAuth (Important)
Dans votre compte développeur Strava (https://www.strava.com/settings/api) :
- **Authorization Callback Domain** : `strava-jerome.web.app`
- **Website** : `https://strava-jerome.web.app`
- **Application Name** : Strava Analytics Dashboard

## 🏃‍♂️ Utilisation quotidienne

### Démarrage standard
```bash
# Terminal 1 - API Flask
cd ~/Documents/dev/strava-analytics
make up

# Terminal 2 - ngrok (pour les amis)
ngrok http 58001

# Terminal 3 - Firebase (si modifications)
cd firebase-app
firebase deploy
```

### 🔑 Authentification et synchronisation initiale
```bash
# 1. S'authentifier avec Strava (dans le navigateur)
open http://localhost:58001/auth/strava

# 2. Configurer vos paramètres personnels (FTP, poids)
curl -X POST http://localhost:58001/api/activities/athlete/1/settings \
  -H "Content-Type: application/json" \
  -d '{"ftp": 240, "weight": 75}'

# 3. Synchroniser vos activités Strava
curl -X POST http://localhost:58001/api/activities/sync

# 4. Calculer métriques personnalisées
curl -X POST http://localhost:58001/api/activities/athlete/1/calculate-custom-metrics

# 5. Vérifier que tout a marché
curl http://localhost:58001/api/activities/athlete/1?per_page=5
```

## 🌐 URLs principales

### Dashboard personnel (vous)
- **API locale** : http://localhost:58001
- **Dashboard sport-km** : http://localhost:58001/dashboard/sport-km.html
- **Santé système** : http://localhost:58001/health

### Interface groupe (amis)
- **Page d'accueil** : https://strava-jerome.web.app
- **Invitation amis** : https://strava-jerome.web.app/invite.html
- **Dashboard groupe** : https://strava-jerome.web.app/dashboard.html

## 📊 Fonctionnalités détaillées

### Dashboard personnel
- **Filtres sports** : Course, Vélo, Home trainer, "Vélo (Tous)" (additionne route + indoor)
- **Périodes** : 30j, 3mois, 6mois, 1an, personnalisée
- **Groupements** : Par jour, semaine, mois
- **Statistiques** : Distance totale, moyenne, maximum, nombre d'activités
- **Graphiques** : Évolution temporelle + répartition circulaire

### Système amis
- **Invitation sécurisée** : Chaque ami autorise individuellement votre app
- **Données privées** : Aucune exposition publique, dashboard groupe fermé
- **Synchronisation** : Activités des amis synchronisées dans votre base locale
- **Comparaisons** : Stats groupées, classements, évolutions comparatives

## 🗃️ Base de données

### Structure principale (nouvelles tables ajoutées)
```sql
-- Vos données principales
activity_summary              -- Vos activités de base
athletes                     -- Informations des athlètes

-- Métriques enrichies (NOUVELLES TABLES Phase 1)
activity_strava_metrics      -- Métriques Strava natives (puissance, FC, TSS)
activity_custom_metrics      -- Calculs personnalisés (TSS recalculé, zones)
athlete_settings            -- Vos paramètres (FTP, poids, seuils)

-- Données amis (en développement)
friends_auth                -- Tokens d'autorisation des amis
friends_activity_summary    -- Activités des amis autorisés
```

### 📊 Nouvelles métriques disponibles
- **Puissance** : Normalized Power, TSS Strava, zones personnalisées
- **Fréquence cardiaque** : Zones FC, moyennes, pics
- **Records personnels** : Meilleurs temps 1km, 5km, 10km, 21km, 42km
- **Records de puissance** : Pics 1min, 5min, 20min
- **Charge d'entraînement** : TSS personnalisé basé sur votre FTP

### Accès base (DBeaver)
- **Host** : localhost
- **Port** : 5433
- **Database** : strava_analytics_db
- **Username** : strava_user

### 🔍 Requêtes utiles pour explorer les nouvelles données
```sql
-- Voir vos activités avec métriques enrichies
SELECT 
    a.name, 
    a.type,
    a.distance_km,
    sm.weighted_average_watts as normalized_power,
    sm.suffer_score as tss_strava,
    cm.custom_tss,
    cm.intensity_factor
FROM activity_summary a
LEFT JOIN activity_strava_metrics sm ON a.id = sm.activity_id
LEFT JOIN activity_custom_metrics cm ON a.id = cm.activity_id
WHERE a.athlete_id = 1
ORDER BY a.start_date_local DESC
LIMIT 10;

-- Voir vos records personnels
SELECT * FROM athlete_personal_records WHERE athlete_id = 1;

-- Stats mensuelles enrichies
SELECT * FROM monthly_activity_stats 
WHERE athlete_id = 1 AND year = 2024 
ORDER BY month DESC;
```

## 🔧 Maintenance

### Commandes utiles
```bash
# Vérifications santé
curl http://localhost:58001/health
docker-compose ps

# Logs système
make logs
docker-compose logs -f api

# Redémarrages
make restart
make stop && make up

# Synchronisation amis
curl -X POST http://localhost:58001/api/friends/sync-all

# Tests des endpoints amis
curl http://localhost:58001/api/friends/status
curl http://localhost:58001/api/friends/list
```

### Gestion ngrok
```bash
# L'URL ngrok change à chaque redémarrage (version gratuite)
# Après redémarrage ngrok :

# 1. Noter nouvelle URL
open http://localhost:4040

# 2. Mettre à jour firebase-app/public/js/config.js
# Changer API_BASE_URL: 'https://NOUVELLE-URL.ngrok.io'

# 3. Redéployer Firebase
cd firebase-app
firebase deploy
```

### 🔄 Mise à jour des métriques
```bash
# Recalculer toutes les métriques personnalisées
curl -X POST http://localhost:58001/api/activities/athlete/1/calculate-custom-metrics

# Mettre à jour vos seuils
curl -X POST http://localhost:58001/api/activities/athlete/1/settings \
  -H "Content-Type: application/json" \
  -d '{"ftp": 250, "weight": 70}'

# Synchroniser nouvelles activités
curl -X POST http://localhost:58001/api/activities/sync
```

## 🆘 Troubleshooting

### Problèmes courants

**API ne répond pas**
```bash
curl http://localhost:58001/health
# Si erreur : vérifier make up, Docker, ports
```

**Erreur ModuleNotFoundError dans les logs**
```bash
# Le problème est dans ./api/app.py, pas ./app.py
# Vérifier que les imports sont corrects :
# from models.database import db
# from routes.friends_routes import friends_bp
```

**Base de données : tables manquantes**
```bash
# Reconstruire la base avec les nouvelles tables
docker-compose down -v
docker volume rm strava-analytics_postgres-data
make up
```

**Amis ne peuvent pas s'authentifier**
```bash
# Vérifier configuration Strava :
# Authorization Callback Domain = strava-jerome.web.app
# Vérifier ngrok actif et config.js à jour
```

**Dashboard vide**
```bash
# Vérifier données synchronisées
curl http://localhost:58001/api/activities/athlete/1?per_page=5
# Si vide : vérifier auth Strava et tokens
```

**ngrok : "authentication failed"**
```bash
# Vous avez déjà une session active
open http://localhost:4040  # Voir l'URL active

# Ou arrêter et redémarrer
pkill ngrok
ngrok http 58001
```

**Configuration Firebase manquante**
```bash
# Vérifier que config.js existe et contient les bonnes valeurs
ls -la firebase-app/public/js/config.js
cat firebase-app/public/js/config.js

# Redéployer après modification
cd firebase-app
firebase deploy
```

## 📈 Performances

### Couverture données
- ✅ ~1500 activités synchronisées et analysées
- ✅ 99.9% métriques enrichies (Strava natives)
- ✅ 100% calculs personnalisés (TSS, zones, records)
- ✅ Support multi-amis illimité
- ✅ Nouvelles tables optimisées avec index

### Temps de traitement
- **Sync initiale** : ~2-3 minutes pour 1000 activités
- **Sync incrémentale** : ~10-30 secondes
- **Dashboard load** : <2 secondes
- **API response** : <200ms moyenne
- **Calcul métriques personnalisées** : ~30 secondes pour 1000 activités

## 🔐 Sécurité

### Données personnelles
- Vos données restent **locales** (PostgreSQL local)
- Tokens Strava **chiffrés** en base
- Aucune transmission vers des tiers

### Données amis
- Accès **uniquement aux données autorisées** via OAuth
- Stockage **local sécurisé**
- **Révocation possible** à tout moment côté Strava
- **Dashboard privé** - aucune exposition publique

### Configuration sécurisée
- Client ID Strava : **public** (visible dans URLs), pas de risque
- Client Secret : **privé** (reste dans .env serveur)
- URLs Firebase : **publiques** par nature
- API ngrok : **temporaire** et locale

## 📄 Commandes de référence

```bash
# Démarrage complet
cd ~/Documents/dev/strava-analytics
make up && ngrok http 58001 && cd firebase-app && firebase deploy

# Configuration initiale complète
curl -X POST http://localhost:58001/api/activities/athlete/1/settings \
  -H "Content-Type: application/json" -d '{"ftp": 240, "weight": 75}'
curl -X POST http://localhost:58001/api/activities/sync
curl -X POST http://localhost:58001/api/activities/athlete/1/calculate-custom-metrics

# Inviter des amis
echo "Partagez : https://strava-jerome.web.app/invite.html"

# Vérifications système
curl http://localhost:58001/health
curl http://localhost:58001/api/friends/list
curl http://localhost:58001/api/activities/athlete/1?per_page=3

# Arrêt propre
make stop
```

## 🆕 Nouveautés v2.0

### ✅ Phase 1 : Métriques enrichies (TERMINÉ)
- Tables `activity_strava_metrics` et `activity_custom_metrics`
- TSS personnalisé basé sur votre FTP
- Records de puissance et de distance
- Zones d'entraînement personnalisées
- Vues SQL enrichies pour analyses avancées

### 🚧 Phase 2 : Système amis (EN COURS)
- Interface d'invitation Firebase fonctionnelle
- API friends avec endpoints OAuth
- Stockage sécurisé des autorisations amis
- Dashboard comparatif (en développement)

### 🔮 Phase 3 : Analyses avancées (PLANIFIÉ)
- Détection automatique de tests FTP
- Prédictions de performance
- Planification d'entraînement
- Alertes et recommandations

---

**🎯 Système Strava Analytics v2.0 avec métriques avancées et système d'amis !**

**Support** : Consultez les logs avec `make logs` en cas de problème.

**Changelog** : 
- ✅ Métriques Strava natives intégrées
- ✅ Calculs personnalisés TSS/IF basés sur votre FTP  
- ✅ Interface d'invitation Firebase opérationnelle
- ✅ Base de données enrichie avec nouvelles tables
- ✅ Configuration sécurisée et automatisée