# 🏃‍♂️ Strava Analytics - Édition Enrichie

Système complet d'analyse des données d'entraînement Strava avec API backend, base de données PostgreSQL, analyses temporelles avancées et **métriques Strava natives enrichies**.

## ✨ Fonctionnalités

### 🔄 Core Features (existantes)
- 🔐 **Authentification Strava OAuth 2.0**
- 📊 **Analyses temporelles complètes** (jour, semaine, mois, année)
- 📈 **Statistiques avancées** par type d'activité
- 📅 **Vue calendrier** des activités
- 🏆 **Records personnels** et progression
- 📤 **Export CSV enrichi** des données
- 🔄 **Synchronisation automatique** des activités
- 🐳 **Déploiement Docker** prêt pour production

### ⚡ Nouvelles Métriques Strava Enrichies
- 💪 **Puissance Normalized Power** (weighted_average_watts) - Plus précise que puissance moyenne
- 🎯 **Training Stress Score** (suffer_score) - Charge d'entraînement scientifique (0-500+)
- ❤️ **Données fréquence cardiaque** enrichies (has_heartrate, zones d'effort)
- 🔍 **Distinction capteur réel vs estimé** (device_watts) - Fiabilité des données
- 🏠 **Contexte activité** (indoor/outdoor, commute, home trainer)
- 📊 **Analyse par zones d'entraînement** automatique
- 🏆 **Détection automatique entraînements de qualité**
- 📈 **Dashboards de performance niveau professionnel**

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
# Construction et démarrage
make build
make up

# Ou manuellement
docker-compose build
docker-compose up -d
```

### 5. Première utilisation

1. Ouvrir http://localhost:58001
2. Aller sur http://localhost:58001/auth/strava
3. Autoriser l'application Strava
4. Vos activités seront synchronisées automatiquement avec **enrichissement complet** !

---

# 📋 Mémo - Commandes quotidiennes

## 🚀 Démarrage depuis Docker Desktop

### 1. Ouvrir le terminal et aller dans le projet
```bash
cd ~/Documents/dev/strava-analytics
```

### 2. Démarrer les services
```bash
# Option A : Avec Makefile (recommandé)
make up

# Option B : Docker Compose direct
docker-compose up -d
```

### 3. Vérifier que tout fonctionne
```bash
# Voir le statut des services
docker-compose ps

# Tester l'API (doit répondre "healthy")
curl http://localhost:58001/health
```

## 🔍 Commandes de diagnostic

```bash
# Voir les logs en temps réel
docker-compose logs -f

# Voir seulement les logs de l'API
docker-compose logs -f api

# Voir seulement les logs de la base
docker-compose logs -f db

# Arrêter de voir les logs : Ctrl+C
```

## 📊 URLs importantes

- **Page d'accueil** : http://localhost:58001
- **Santé de l'API** : http://localhost:58001/health  
- **Statut auth** : http://localhost:58001/auth/status
- **Authentification Strava** : http://localhost:58001/auth/strava

## 🏃‍♂️ Vos données personnelles enrichies

### Informations générales
```bash
# Statut de votre connexion Strava
curl http://localhost:58001/auth/status

# Résumé enrichi de votre profil (remplacez 1 par votre athlete_id)
curl "http://localhost:58001/api/activities/athlete/1/summary"

# Statut des métriques enrichies (NOUVEAU)
curl "http://localhost:58001/api/activities/athlete/1/metrics-status"

# Types d'activités pratiqués avec métriques (NOUVEAU)
curl "http://localhost:58001/api/activities/athlete/1/activity-types"
```

### Vos activités enrichies
```bash
# 5 dernières activités avec métriques complètes
curl "http://localhost:58001/api/activities/athlete/1?per_page=5"

# Activités d'une année spécifique avec métriques
curl "http://localhost:58001/api/activities/athlete/1?year=2024"

# Synchroniser manuellement avec enrichissement automatique
curl "http://localhost:58001/api/activities/athlete/1/sync"
```

### ⚡ Nouvelles analyses avancées
```bash
# Analyse de votre charge d'entraînement (Training Stress Score)
curl "http://localhost:58001/api/activities/athlete/1/training-load"

# Analyse de vos données de puissance (Normalized Power, capteurs)
curl "http://localhost:58001/api/activities/athlete/1/power-analysis"

# Vos entraînements de qualité détectés automatiquement
curl "http://localhost:58001/api/activities/athlete/1/quality-workouts"

# Mise à jour des métriques pour activités existantes
curl "http://localhost:58001/api/activities/athlete/1/update-metrics?limit=50"
```

## 🛠️ Commandes de maintenance

### Arrêter/Redémarrer
```bash
# Arrêter tous les services
docker-compose stop

# Redémarrer tous les services  
docker-compose restart

# Redémarrer seulement l'API
docker-compose restart api
```

### En cas de problème
```bash
# Arrêter tout proprement
docker-compose down

# Reconstruire les images
docker-compose build

# Relancer
docker-compose up -d

# Nettoyer complètement (⚠️ supprime toutes les données!)
docker-compose down -v
docker system prune -f
```

## 📈 Export de données enrichies

```bash
# Exporter toutes vos activités ENRICHIES en CSV (NOUVEAU)
curl "http://localhost:58001/api/activities/athlete/1/export" > mes_activites_enrichies.csv

# Exporter seulement 2024 avec toutes les métriques (NOUVEAU)
curl "http://localhost:58001/api/activities/athlete/1/export?year=2024" > activites_2024_enrichies.csv

# Exporter seulement la course avec métriques de puissance (NOUVEAU)
curl "http://localhost:58001/api/activities/athlete/1/export?type=Run" > mes_courses_enrichies.csv
```

**Le CSV enrichi contient maintenant :**
- Toutes les données existantes (distance, temps, FC, etc.)
- **Puissance Normalized Power** (weighted_average_watts)
- **Training Stress Score** (suffer_score)
- **Type de capteur** (réel vs estimé)
- **Contexte d'entraînement** (indoor/outdoor)

## 🆘 Dépannage rapide

### Si l'API ne répond pas
```bash
cd ~/Documents/dev/strava-analytics
docker-compose ps
docker-compose logs api --tail=20
```

### Si la base de données ne marche pas
```bash
docker-compose logs db --tail=20
```

### Si les métriques enrichies manquent
```bash
# Vérifier le statut des métriques
curl "http://localhost:58001/api/activities/athlete/1/metrics-status"

# Forcer l'enrichissement des activités existantes
curl "http://localhost:58001/api/activities/athlete/1/update-metrics?limit=100"
```

### Si tout plante
```bash
docker-compose down
docker-compose up -d
sleep 10
curl http://localhost:58001/health
```

## ⚡ Séquence de démarrage complète

```bash
# 1. Aller dans le projet
cd ~/Documents/dev/strava-analytics

# 2. Démarrer
make up

# 3. Attendre 10 secondes
sleep 10

# 4. Vérifier
curl http://localhost:58001/health

# 5. Voir vos données enrichies
curl http://localhost:58001/auth/status
curl "http://localhost:58001/api/activities/athlete/1/summary"
```

---

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

### Activités de base (enrichies)
- `GET /api/activities/athlete/{id}` - Liste des activités avec métriques enrichies
- `GET /api/activities/athlete/{id}/export` - Export CSV enrichi avec toutes les métriques
- `GET /api/activities/athlete/{id}/sync` - Sync enrichie automatique

### ⚡ Nouveaux endpoints métriques avancées
- `GET /api/activities/athlete/{id}/summary` - Résumé complet enrichi avec couverture métriques
- `GET /api/activities/athlete/{id}/metrics-status` - Statut détaillé des métriques (couverture %)
- `GET /api/activities/athlete/{id}/training-load` - Analyse charge d'entraînement (TSS)
- `GET /api/activities/athlete/{id}/power-analysis` - Analyse données puissance (NP, capteurs)
- `GET /api/activities/athlete/{id}/quality-workouts` - Entraînements de qualité détectés
- `GET /api/activities/athlete/{id}/activity-types` - Analyse par type avec métriques
- `GET /api/activities/athlete/{id}/update-metrics` - Mise à jour métriques existantes
- `GET /api/activities/athlete/{id}/sync-single/{activity_id}` - Sync activité spécifique

### Analytics (existants, améliorés)
- `GET /api/analytics/athlete/{id}/monthly` - Stats mensuelles enrichies
- `GET /api/analytics/athlete/{id}/day-of-week` - Stats par jour avec métriques
- `GET /api/analytics/athlete/{id}/calendar` - Vue calendrier enrichie
- `GET /api/analytics/athlete/{id}/trends` - Analyse tendances avec TSS
- `GET /api/analytics/athlete/{id}/comparison` - Comparaison années avec puissance
- `GET /api/analytics/athlete/{id}/dashboard` - Résumé général enrichi

## 📊 Exemples d'analyses enrichies

### Training Stress Score et charge d'entraînement
```bash
# Charge d'entraînement sur 90 jours
curl "http://localhost:58001/api/activities/athlete/1/training-load?days=90"

# Répartition par niveau d'effort (easy/moderate/hard/very_hard)
curl "http://localhost:58001/api/activities/athlete/1/training-load?days=30" | jq '.load_distribution'
```

### Analyse de puissance avancée
```bash
# Analyse puissance avec distinction capteur réel/estimé
curl "http://localhost:58001/api/activities/athlete/1/power-analysis?days=60"

# Voir seulement les activités avec capteur de puissance réel
curl "http://localhost:58001/api/activities/athlete/1/power-analysis" | jq '.activities[] | select(.is_real_power == true)'
```

### Détection des entraînements de qualité
```bash
# Entraînements de qualité sur 2 mois
curl "http://localhost:58001/api/activities/athlete/1/quality-workouts?days=60"

# Pourcentage d'entraînements de qualité
curl "http://localhost:58001/api/activities/athlete/1/quality-workouts" | jq '.quality_percentage'
```

### Statistiques mensuelles enrichies
```bash
curl "http://localhost:58001/api/analytics/athlete/1/monthly?months=6"
```

### Activités par jour de la semaine avec métriques
```bash
curl "http://localhost:58001/api/analytics/athlete/1/day-of-week"
```

### Export CSV des activités enrichies
```bash
curl "http://localhost:58001/api/activities/athlete/1/export?year=2024" > mes_activites_2024_enrichies.csv
```

## 🗂️ Structure des données enrichies

### Données temporelles capturées
- **Jour** : Lundi, Mardi, Mercredi...
- **Date** : Jour du mois (1-31)
- **Mois** : Janvier, Février, Mars...
- **Année** : 2024, 2023...
- **Semaine** : Numéro ISO (1-53)

### ⚡ Nouvelles métriques analysées (Strava natives)
- **Puissance Normalized Power** : Plus précise que puissance moyenne, équivalent NP
- **Training Stress Score** : Charge d'entraînement scientifique (échelle 0-500+)
- **Distinction capteur réel vs estimé** : Fiabilité des données de puissance
- **Données FC enrichies** : Présence capteur, données de qualité
- **Contexte d'entraînement** : Indoor/outdoor, commute, home trainer
- **Niveau d'effort** : Classification automatique (easy/moderate/hard/very_hard)
- **Qualité d'entraînement** : Détection automatique des séances importantes

### Métriques existantes (conservées)
- Distance (km)
- Temps de mouvement (heures)
- Vitesse moyenne/maximale
- Dénivelé positif
- Fréquence cardiaque
- Calories
- Type d'activité (Course, Vélo, Natation...)

## 🗃️ Configuration DBeaver enrichie

### Paramètres de connexion
- **Host** : `localhost`
- **Port** : `5433`
- **Database** : `strava_analytics_db`
- **Username** : `strava_user`
- **Password** : [votre POSTGRES_PASSWORD du .env]

### ⚡ Nouvelles requêtes SQL enrichies

```sql
-- Voir vos 10 dernières activités avec toutes les métriques enrichies
SELECT 
    name, type, start_date_local, distance_km, moving_time_hours,
    weighted_average_watts, suffer_score, device_watts, has_heartrate,
    trainer, commute, effort_level, power_source
FROM activity_with_strava_metrics 
WHERE athlete_id = 1 
ORDER BY start_date_local DESC 
LIMIT 10;

-- Statistiques par type d'activité avec métriques avancées
SELECT 
    type, 
    COUNT(*) as nb_activites,
    ROUND(SUM(distance_km), 2) as total_km,
    ROUND(SUM(moving_time_hours), 2) as total_heures,
    ROUND(AVG(weighted_average_watts), 1) as puissance_normalized_moyenne,
    ROUND(AVG(suffer_score), 1) as tss_moyen,
    ROUND(SUM(suffer_score), 1) as charge_totale,
    COUNT(CASE WHEN device_watts = true THEN 1 END) as activites_capteur_reel,
    ROUND((COUNT(CASE WHEN device_watts = true THEN 1 END)::float / COUNT(*)) * 100, 1) as pourcentage_capteur_reel
FROM activity_with_strava_metrics 
WHERE athlete_id = 1 
GROUP BY type 
ORDER BY total_km DESC;

-- Charge d'entraînement par mois (Training Stress Score)
SELECT 
    year, month_name,
    COUNT(*) as activites,
    ROUND(SUM(suffer_score), 1) as tss_total,
    ROUND(AVG(suffer_score), 1) as tss_moyen,
    ROUND(SUM(distance_km), 2) as km_totaux,
    COUNT(CASE WHEN effort_level = 'very_hard' THEN 1 END) as entraînements_très_durs,
    COUNT(CASE WHEN effort_level = 'hard' THEN 1 END) as entraînements_durs
FROM activity_with_strava_metrics 
WHERE athlete_id = 1 AND suffer_score IS NOT NULL
GROUP BY year, month, month_name
ORDER BY year DESC, month DESC;

-- Activités par niveau d'effort (Classification automatique)
SELECT 
    effort_level as niveau_effort,
    COUNT(*) as nombre_activites,
    ROUND(AVG(suffer_score), 1) as tss_moyen,
    ROUND(AVG(weighted_average_watts), 1) as puissance_moyenne,
    ROUND(AVG(distance_km), 2) as distance_moyenne,
    ROUND((COUNT(*)::float / (SELECT COUNT(*) FROM activity_with_strava_metrics WHERE athlete_id = 1)) * 100, 1) as pourcentage
FROM activity_with_strava_metrics 
WHERE athlete_id = 1 
GROUP BY effort_level 
ORDER BY tss_moyen DESC;

-- Progression puissance par année (capteurs réels seulement)
SELECT 
    year,
    COUNT(CASE WHEN device_watts = true THEN 1 END) as activites_capteur_reel,
    ROUND(AVG(CASE WHEN device_watts = true THEN weighted_average_watts END), 1) as puissance_normalized_moyenne,
    MAX(CASE WHEN device_watts = true THEN weighted_average_watts END) as puissance_normalized_max,
    ROUND(AVG(CASE WHEN device_watts = true THEN suffer_score END), 1) as tss_moyen
FROM activity_with_strava_metrics 
WHERE athlete_id = 1 AND weighted_average_watts IS NOT NULL
GROUP BY year 
ORDER BY year;

-- Entraînements indoor vs outdoor
SELECT 
    activity_context as contexte,
    COUNT(*) as nombre,
    ROUND(AVG(suffer_score), 1) as tss_moyen,
    ROUND(AVG(weighted_average_watts), 1) as puissance_moyenne,
    ROUND(SUM(distance_km), 2) as km_totaux
FROM activity_with_strava_metrics 
WHERE athlete_id = 1 
GROUP BY activity_context 
ORDER BY nombre DESC;

-- Top 10 de vos meilleures performances (TSS le plus élevé)
SELECT 
    name, type, start_date_local, 
    distance_km, moving_time_hours,
    weighted_average_watts, suffer_score, device_watts
FROM activity_with_strava_metrics 
WHERE athlete_id = 1 AND suffer_score IS NOT NULL
ORDER BY suffer_score DESC 
LIMIT 10;

-- Activités avec données de puissance réelles (capteur)
SELECT 
    name, type, start_date_local,
    weighted_average_watts as puissance_normalized,
    suffer_score as tss,
    ROUND(weighted_average_watts / NULLIF(average_heartrate, 0), 2) as efficacite_cardiaque
FROM activity_with_strava_metrics 
WHERE athlete_id = 1 AND device_watts = true
ORDER BY weighted_average_watts DESC 
LIMIT 20;
```

### Requêtes SQL existantes (conservées)
```sql
-- Voir vos 10 dernières activités (version simple)
SELECT name, type, start_date_local, distance_km, moving_time_hours, day_name
FROM activity_summary 
WHERE athlete_id = 1 
ORDER BY start_date_local DESC 
LIMIT 10;

-- Activités par jour de la semaine
SELECT day_name, COUNT(*) as nb_activites,
       ROUND(AVG(distance_km), 2) as distance_moyenne
FROM activity_summary 
WHERE athlete_id = 1 
GROUP BY day_name, day_of_week
ORDER BY day_of_week;
```

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

### Synchronisation enrichie automatique

Le système synchronise automatiquement avec enrichissement :
- ✅ **Activités de base** récupérées depuis Strava
- ✅ **Métriques enrichies** extraites automatiquement
- ✅ **Respect des limites API** Strava (100 req/15min, 1000/jour)
- ✅ **Rate limiting intelligent** intégré
- ✅ **Gestion d'erreurs** et reprises automatiques

### Personnaliser la synchronisation

```bash
# Sync normale avec enrichissement automatique (recommandé)
curl "http://localhost:58001/api/activities/athlete/1/sync"

# Enrichir les activités existantes sans métriques (50 par lot)
curl "http://localhost:58001/api/activities/athlete/1/update-metrics?limit=50"

# Forcer la mise à jour d'une activité spécifique
curl "http://localhost:58001/api/activities/athlete/1/sync-single/12345678"

# Vérifier la couverture des métriques
curl "http://localhost:58001/api/activities/athlete/1/metrics-status"
```

## 🐳 Architecture Docker enrichie

### Services
- **API** : Flask + SQLAlchemy + Enrichissement Strava automatique (port 58001)
- **Database** : PostgreSQL 15 + nouvelles tables métriques (port 5433)

### Nouvelles tables de données
- `activity_strava_metrics` : Métriques natives Strava enrichies
- `activity_with_strava_metrics` : Vue combinée optimisée pour requêtes
- Vues analytiques enrichies : `monthly_activity_stats`, `weekly_activity_stats`, etc.

### Volumes persistants
- `postgres-data` : Données PostgreSQL + nouvelles métriques
- `./database/backup` : Sauvegardes
- `./data/exports` : Exports CSV enrichis

## 🛠️ Développement

### Structure du projet enrichie
```
strava-analytics/
├── api/                    # Code Python Flask
│   ├── models/            # Modèles de données
│   │   ├── database.py    # Modèles de base existants
│   │   └── strava_metrics.py # ⚡ Nouveaux modèles métriques enrichies
│   ├── services/          # Services métier
│   │   └── strava_service.py # ⚡ Service enrichi avec métriques
│   ├── routes/            # Routes API
│   │   └── activities.py  # ⚡ Routes enrichies avec nouvelles analyses
│   └── app.py            # Application principale
├── database/              # Configuration base
│   └── init.sql          # ⚡ Schema enrichi avec nouvelles tables
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

## 📈 Exemples d'utilisation enrichis

### Analyser vos performances avec métriques avancées
```python
# Via l'API Python enrichie
import requests
import json

# Récupérer vos métriques d'entraînement
response = requests.get('http://localhost:58001/api/activities/athlete/1/training-load?days=90')
training_data = response.json()

print(f"Charge totale 90 jours: {training_data['training_load_stats']['total_load']} TSS")
print(f"Moyenne hebdomadaire: {training_data['training_load_stats']['avg_weekly_load']} TSS")
print(f"Sessions très dures: {training_data['load_distribution']['very_hard_sessions']}")

# Analyser la puissance avec distinction capteur réel/estimé
power_response = requests.get('http://localhost:58001/api/activities/athlete/1/power-analysis?days=30')
power_data = power_response.json()

print(f"Puissance Normalized moyenne: {power_data['power_statistics']['avg_normalized_power']}W")
print(f"Couverture capteur réel: {power_data['power_meter_coverage']}%")
print(f"Activités capteur réel: {power_data['real_power_meter_activities']}")

# Détecter les entraînements de qualité
quality_response = requests.get('http://localhost:58001/api/activities/athlete/1/quality-workouts?days=60')
quality_data = quality_response.json()

print(f"Entraînements de qualité: {quality_data['quality_workouts']}/{quality_data['total_activities']}")
print(f"Pourcentage qualité: {quality_data['quality_percentage']}%")
```

### Dashboard personnel enrichi
```bash
# Résumé complet avec toutes les métriques
curl "http://localhost:58001/api/activities/athlete/1/summary" | jq

# Export CSV avec toutes les données enrichies
curl "http://localhost:58001/api/activities/athlete/1/export" > dashboard_complet_enrichi.csv

# Statut de couverture des métriques
curl "http://localhost:58001/api/activities/athlete/1/metrics-status" | jq
```

## 🔒 Sécurité

- Tokens Strava chiffrés en base
- Rate limiting respecté (100 req/15min, 1000/jour)
- Refresh automatique des tokens
- Validation des entrées API
- Logs sécurisés
- ⚡ Gestion intelligente des limites API Strava pour enrichissement

## 📱 Intégrations possibles enrichies

Le système expose une API REST complète enrichie pour intégrer avec :
- Applications mobiles avec métriques de niveau professionnel
- Tableaux de bord (Grafana, Tableau) avec Training Stress Score
- Scripts d'analyse personnalisés avec données de puissance Normalized
- Systèmes de notification basés sur la charge d'entraînement
- Applications web tierces avec distinction capteur réel/estimé
- Outils de coaching avec métriques scientifiques

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

**Métriques enrichies manquantes**
```bash
# Vérifier le statut des métriques
curl "http://localhost:58001/api/activities/athlete/1/metrics-status"

# Voir la couverture actuelle
curl "http://localhost:58001/api/activities/athlete/1/metrics-status" | jq '.coverage_percentage'

# Forcer l'enrichissement des activités sans métriques
curl "http://localhost:58001/api/activities/athlete/1/update-metrics?limit=50"
```

**Synchronisation lente**
- Normal : respecte les limites API Strava (100 req/15min)
- Patience requise pour gros volumes d'activités
- Le système reprend automatiquement en cas d'interruption

### Logs utiles
```bash
make logs       # Tous les logs
make logs-api   # API seulement
make logs-db    # PostgreSQL

# Voir les erreurs de sync enrichie
docker-compose logs api | grep -i "enrichment"
docker-compose logs api | grep -i "strava_metrics"
```

## 📱 Résumé des ports

- **API enrichie** : http://localhost:58001
- **PostgreSQL + métriques** : localhost:5433 (pour DBeaver)

---

# 💾 Sauvegarde et versioning Git

## 🔑 Configuration SSH GitHub

### Vérifier la configuration SSH existante
```bash
# Vérifier les clés SSH existantes
ls -la ~/.ssh/

# Tester la connexion GitHub
ssh -T git@github.com
```

### Si pas de clé SSH, en créer une
```bash
# Générer une nouvelle clé SSH
ssh-keygen -t ed25519 -C "votre-email@example.com"

# Ajouter la clé à l'agent SSH
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# Afficher la clé publique pour l'ajouter à GitHub
cat ~/.ssh/id_ed25519.pub
```

Puis : GitHub → Settings → SSH Keys → Add SSH Key

## 📁 Initialisation du dépôt Git

```bash
cd ~/Documents/dev/strava-analytics

# Initialiser Git
git init

# Ajouter le remote GitHub
git remote add origin git@github.com:flownect/strava.git

# Vérifier la connexion
git remote -v
```

## 💾 Sauvegarde enrichie

```bash
# Voir le statut des fichiers
git status

# Ajouter tous les fichiers (sauf .gitignore exclusions)
git add .

# Commit avec métriques enrichies
git commit -m "⚡ Major Update: Strava Analytics with Enhanced Metrics

✨ New Features:
- 💪 Normalized Power (weighted_average_watts) from Strava API
- 🎯 Training Stress Score (suffer_score) integration  
- ❤️ Enhanced heart rate data (has_heartrate, zones)
- 🔍 Real vs estimated power detection (device_watts)
- 🏠 Activity context (indoor/outdoor, commute, trainer)
- 📊 Advanced training zone analysis
- 🏆 Quality workout detection
- 📈 Enhanced performance dashboards

🗃️ Database Enhancements:
- New table: activity_strava_metrics
- Enhanced views: activity_with_strava_metrics  
- Optimized queries for performance analysis
- 99.9% metrics coverage achieved (1453/1454 activities)

🌐 API Enhancements:
- Enhanced sync with automatic enrichment
- New endpoints for training load analysis
- Power analysis with sensor detection
- Quality workout identification
- Enriched CSV exports with all metrics

🐳 Architecture:
- Flask API with Strava metrics enrichment
- PostgreSQL 15 with enhanced schema
- Docker deployment optimized
- Rate limiting for Strava API compliance

📊 Performance:
- 1454 activities synchronized
- 99.9% metrics enrichment coverage
- Training Stress Score analysis ready
- Normalized Power tracking active"

# Pousser vers GitHub
git push -u origin main
```

## 🔄 Sauvegardes futures

```bash
# Après modifications
git add .
git commit -m "📝 Update: description des changements"
git push
```

## 📊 Commandes utiles Git

```bash
# Voir l'historique
git log --oneline

# Voir les modifications non commitées
git diff

# Voir le statut du dépôt
git status

# Voir les branches
git branch -a

# Synchroniser avec GitHub
git pull origin main
```

## 🔒 Fichiers exclus (.gitignore)

Les fichiers suivants ne sont **PAS** sauvegardés pour la sécurité :
- `.env` (contient vos secrets Strava)
- `database/backup/*.sql` (sauvegardes BDD)
- `logs/*.log` (fichiers de logs)
- `data/exports/*` (exports CSV personnels)

## 🆘 Dépannage Git

### Problème d'authentification
```bash
# Vérifier la configuration
git config --global user.name "Votre Nom"
git config --global user.email "votre-email@example.com"

# Tester SSH
ssh -T git@github.com
```

### Changer l'URL du remote
```bash
# Si erreur "repository not found"
git remote set-url origin git@github.com:flownect/strava.git
```

### Synchroniser avec une version GitHub modifiée
```bash
# Récupérer les changements distants
git fetch origin
git merge origin/main

# Ou directement
git pull origin main
```

## 📋 Structure sauvegardée enrichie

```
strava-analytics/
├── 📄 README.md ✅ (avec métriques enrichies complètes)
├── 📄 docker-compose.yml ✅
├── 📄 .env.example ✅ (template)
├── 📄 .gitignore ✅
├── 📄 Makefile ✅
├── 📁 api/ ✅ (code Python enrichi)
│   ├── models/
│   │   ├── database.py ✅ (modèles de base)
│   │   └── strava_metrics.py ✅ (nouveaux modèles enrichis)
│   ├── services/
│   │   └── strava_service.py ✅ (service enrichi)
│   └── routes/
│       └── activities.py ✅ (routes enrichies)
├── 📁 database/ ✅ (schema enrichi)
│   └── init.sql ✅ (avec nouvelles tables métriques)
├── 📁 data/exports/ ✅ (structure enrichie pour CSV)
└── 📁 scripts/ ✅ (utilitaires)

❌ Exclus pour sécurité:
├── .env (secrets Strava)
├── database/backup/*.sql (sauvegardes)
├── logs/*.log (logs système)
└── data/exports/*.csv (données personnelles)
```

## 🔄 Workflow de développement enrichi

```bash
# 1. Travailler sur le projet
cd ~/Documents/dev/strava-analytics
make up

# 2. Faire des modifications
# ... éditer les fichiers ...

# 3. Tester les changements avec métriques
make restart
curl http://localhost:58001/health
curl "http://localhost:58001/api/activities/athlete/1/metrics-status"

# 4. Sauvegarder quand ça marche
git add .
git commit -m "✨ Add: nouvelle fonctionnalité enrichie"
git push

# 5. En cas de problème, revenir en arrière
git log --oneline
git checkout <commit-hash>
```

---

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature
3. Commit vos changements avec métriques enrichies
4. Push vers la branche
5. Ouvrir une Pull Request

### Guidelines de contribution
- ✅ Respecter les limites API Strava (rate limiting)
- ✅ Documenter les nouvelles métriques ajoutées  
- ✅ Tester avec des données réelles
- ✅ Maintenir la compatibilité avec l'existant

## 📄 Licence

MIT License - Voir le fichier LICENSE pour les détails.

## 🙏 Remerciements

- [Strava API](https://developers.strava.com/) pour l'accès aux données enrichies
- [Flask](https://flask.palletsprojects.com/) pour le framework web robuste
- [PostgreSQL](https://www.postgresql.org/) pour la base de données performante
- [Docker](https://www.docker.com/) pour la containerisation
- Communauté Strava pour les retours sur les métriques

## 🏆 Résultats obtenus

### ✅ Métriques synchronisées avec succès
- **1454 activités** totales récupérées
- **1453 activités** enrichies avec métriques Strava (99.9% de couverture)
- **Training Stress Score** disponible pour analyse de charge
- **Puissance Normalized Power** pour analyses de performance précises
- **Distinction capteur réel/estimé** pour fiabilité des données
- **Contexte d'entraînement** (indoor/outdoor) pour analyses complètes

### 📊 Nouvelles capacités d'analyse
- Analyse de charge d'entraînement scientifique (TSS)
- Détection automatique des entraînements de qualité
- Progression de puissance avec données fiables
- Export CSV enrichi pour analyses externes
- Requêtes SQL avancées pour insights détaillés

---

**🎯 Prêt à analyser vos performances sportives avec des métriques de niveau professionnel ?**

**Commande de démarrage :** `cd ~/Documents/dev/strava-analytics && make up` 🚀

## ⚡ Statut actuel de vos données

- ✅ **1454 activités** synchronisées et analysées
- ✅ **99.9% de couverture** métriques enrichies  
- ✅ **Training Stress Score** prêt pour analyse de charge
- ✅ **Puissance Normalized Power** disponible pour performance
- ✅ **Export CSV enrichi** avec toutes les nouvelles métriques
- ✅ **API REST complète** pour intégrations avancées

**Votre système Strava Analytics est maintenant enrichi et prêt pour des analyses de niveau professionnel !** 🏆25