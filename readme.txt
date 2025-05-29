# 🏃‍♂️ Strava Analytics - Système Complet

Système d'analyse avancé des données d'entraînement Strava avec métriques natives enrichies et calculs personnalisés.

## ✨ Fonctionnalités

### 🔄 Métriques Strava Natives Enrichies
- 🔐 **Authentification Strava OAuth 2.0**
- 💪 **Puissance Normalized Power** (weighted_average_watts)
- 🎯 **Training Stress Score** (suffer_score)
- ❤️ **Données fréquence cardiaque** enrichies
- 🔍 **Distinction capteur réel vs estimé** (device_watts)
- 🏠 **Contexte activité** (indoor/outdoor, commute)
- ✅ **99.9% de couverture** sur vos activités

### ⚡ Calculs Personnalisés Avancés
- 🎯 **TSS personnalisé** avec votre FTP réel
- 💪 **Records de puissance** automatiques (1min, 5min, 20min)
- 🏃 **Records de distance** automatiques (1km, 5km, 10km, semi, marathon)
- 📊 **Zones d'intensité précises** basées sur votre FTP
- 🔄 **Comparaison Strava vs Personnel**
- 📈 **Analyses de charge d'entraînement**
- 📋 **Recommandations personnalisées**

### 📊 Dashboard Web Intégré
- 🌐 **Interface web intuitive** avec graphiques interactifs
- 📈 **Visualisations temps réel** de vos performances
- 📱 **Responsive design** pour mobile et desktop
- 🎨 **Tableaux de bord personnalisés**

## 🚀 Installation Rapide

### Prérequis
- Docker et Docker Compose
- Compte Strava avec application API créée

### 1. Configuration Strava API

1. Allez sur https://www.strava.com/settings/api
2. Créez une nouvelle application :
   - **Authorization Callback Domain** : `localhost`
   - **Website** : `http://localhost:58001`
3. Notez votre `Client ID` et `Client Secret`

### 2. Installation du Projet

```bash
# Cloner ou créer le projet
cd ~/Documents/dev
mkdir strava-analytics && cd strava-analytics

# Copier la configuration
cp .env.example .env
```

Configurez `.env` avec vos paramètres Strava :
```env
STRAVA_CLIENT_ID=votre_client_id
STRAVA_CLIENT_SECRET=votre_client_secret
STRAVA_REDIRECT_URI=http://localhost:58001/auth/strava/callback
```

### 3. Démarrage

```bash
# Construction et démarrage
make build && make up

# Attendre le démarrage complet
sleep 15

# Vérifier le bon fonctionnement
curl http://localhost:58001/health
```

### 4. Configuration Personnalisée

```bash
# Configurer votre FTP (remplacez 240 par votre FTP)
curl -X POST http://localhost:58001/api/activities/athlete/1/settings \
  -H "Content-Type: application/json" \
  -d '{"ftp": 240, "weight": 75}'

# Lancer les calculs personnalisés
curl -X POST http://localhost:58001/api/activities/athlete/1/calculate-custom-metrics
```

## 📊 Accès aux Interfaces

### URLs Principales
- **🏠 Page d'accueil** : http://localhost:58001
- **📊 Dashboard Sport** : http://localhost:58001/dashboard/sport-km.html
- **⚕️ Santé API** : http://localhost:58001/health
- **🔐 Auth Strava** : http://localhost:58001/auth/strava
- **📈 Statut** : http://localhost:58001/auth/status

### Configuration Dashboard
Le fichier `dashboard/sport-km.html` est automatiquement servi via l'API Flask. Pour y accéder :

1. **Via navigateur** : http://localhost:58001/dashboard/sport-km.html
2. **Via API** : Le dashboard peut consommer les endpoints API directement

## 🛠️ Commandes Quotidiennes

### Démarrage Standard
```bash
cd ~/Documents/dev/strava-analytics
make up
```

### Vérifications Rapides
```bash
# Statut des services
docker-compose ps

# Santé de l'API
curl http://localhost:58001/health

# Vos paramètres actuels
curl "http://localhost:58001/api/activities/athlete/1/settings"

# Dernières activités
curl "http://localhost:58001/api/activities/athlete/1?per_page=5"
```

### Maintenance
```bash
# Redémarrer les services
make restart

# Voir les logs
make logs

# Arrêter proprement
make stop

# Nettoyage complet (⚠️ supprime les données)
make clean
```

## 🌐 Endpoints API Principaux

### Configuration Personnelle
```bash
# Voir vos paramètres
GET /api/activities/athlete/1/settings

# Configurer FTP et poids
POST /api/activities/athlete/1/settings
```

### Données d'Activités
```bash
# Activités enrichies
GET /api/activities/athlete/1

# Métriques personnalisées
GET /api/activities/athlete/1/custom-metrics

# Export CSV complet
GET /api/activities/athlete/1/export-custom
```

### Analyses Avancées
```bash
# Records personnels
GET /api/activities/athlete/1/personal-records

# Comparaison TSS
GET /api/activities/athlete/1/compare-tss

# Dashboard complet
GET /api/activities/athlete/1/dashboard-custom

# Recommandations
GET /api/activities/athlete/1/recommendations
```

## 📈 Exemples d'Utilisation

### Configuration Initiale Complète
```bash
# 1. Démarrer le système
cd ~/Documents/dev/strava-analytics && make up && sleep 15

# 2. Configurer vos paramètres (ajustez selon vos valeurs)
curl -X POST http://localhost:58001/api/activities/athlete/1/settings \
  -H "Content-Type: application/json" \
  -d '{"ftp": 240, "weight": 75, "max_heartrate": 190}'

# 3. Calculer les métriques personnalisées
curl -X POST http://localhost:58001/api/activities/athlete/1/calculate-custom-metrics

# 4. Voir votre dashboard
curl "http://localhost:58001/api/activities/athlete/1/dashboard-custom"

# 5. Accéder au dashboard web
# Ouvrir http://localhost:58001/dashboard/sport-km.html
```

### Export de Données
```bash
# Export CSV avec toutes les métriques
curl "http://localhost:58001/api/activities/athlete/1/export-custom" > mes_activites_completes.csv

# Export par année
curl "http://localhost:58001/api/activities/athlete/1/export-custom?year=2024" > activites_2024.csv

# Export par type d'activité
curl "http://localhost:58001/api/activities/athlete/1/export-custom?type=Run" > mes_courses.csv
```

## 🗃️ Architecture Technique

### Services Docker
- **API Flask** : http://localhost:58001 (application principale)
- **PostgreSQL** : localhost:5433 (base de données)
- **Dashboard Web** : Intégré dans l'API Flask

### Structure des Données
```
📊 Métriques Strava Natives
├── Puissance Normalized Power (weighted_average_watts)
├── Training Stress Score (suffer_score)
├── Données cardio enrichies (has_heartrate)
└── Contexte activité (indoor/outdoor/commute)

⚡ Calculs Personnalisés
├── TSS avec votre FTP réel
├── Intensity Factor précis
├── Zones de puissance personnalisées
├── Records automatiques (puissance + distance)
└── Recommandations d'entraînement
```

### Base de Données
```sql
-- Tables principales
activity_summary              -- Activités de base
activity_strava_metrics      -- Métriques Strava natives
activity_custom_metrics      -- Calculs personnalisés
athlete_settings            -- Paramètres utilisateur (FTP, poids)

-- Vues optimisées
activity_with_strava_metrics    -- Vue combinée enrichie
activity_complete_analysis      -- Vue avec tous les calculs
```

## 🔧 Configuration Avancée

### Variables d'Environnement (.env)
```env
# Base de données
POSTGRES_USER=strava_user
POSTGRES_PASSWORD=votre_mot_de_passe_securise
POSTGRES_DB=strava_analytics_db

# Strava API
STRAVA_CLIENT_ID=votre_client_id
STRAVA_CLIENT_SECRET=votre_client_secret
STRAVA_REDIRECT_URI=http://localhost:58001/auth/strava/callback

# Application
FLASK_SECRET_KEY=votre_cle_secrete_flask
FLASK_ENV=production
```

### Accès Base de Données (DBeaver)
- **Host** : `localhost`
- **Port** : `5433`
- **Database** : `strava_analytics_db`
- **Username** : `strava_user`
- **Password** : [votre mot de passe du .env]

### Requêtes SQL Utiles
```sql
-- Voir vos 10 dernières activités avec métriques complètes
SELECT name, type, start_date_local, distance_km, 
       weighted_average_watts, suffer_score, custom_tss, 
       intensity_factor, power_zone
FROM activity_complete_analysis 
WHERE athlete_id = 1 
ORDER BY start_date_local DESC 
LIMIT 10;

-- Statistiques par type d'activité
SELECT type, COUNT(*) as nb_activites,
       ROUND(AVG(custom_tss), 1) as tss_moyen,
       ROUND(AVG(intensity_factor), 3) as if_moyen,
       ROUND(SUM(distance_km), 2) as km_total
FROM activity_complete_analysis 
WHERE athlete_id = 1 
GROUP BY type 
ORDER BY nb_activites DESC;
```

## 🆘 Dépannage

### Problèmes Courants

**Services ne démarrent pas**
```bash
# Vérifier les logs
docker-compose logs --tail=20

# Redémarrer proprement
docker-compose down && docker-compose up -d
```

**Dashboard HTML ne s'affiche pas**
```bash
# Vérifier que le fichier existe
ls -la dashboard/sport-km.html

# Vérifier les permissions
chmod 644 dashboard/sport-km.html

# Accéder directement
curl http://localhost:58001/dashboard/sport-km.html
```

**Authentification Strava échoue**
- Vérifiez `STRAVA_CLIENT_ID` et `STRAVA_CLIENT_SECRET` dans `.env`
- Vérifiez que l'URL de callback correspond dans les paramètres Strava

**Métriques manquantes**
```bash
# Vérifier la couverture
curl "http://localhost:58001/api/activities/athlete/1/metrics-status"

# Relancer l'enrichissement
curl -X POST "http://localhost:58001/api/activities/athlete/1/calculate-custom-metrics"
```

### Logs Utiles
```bash
# Tous les logs
make logs

# API seulement
docker-compose logs -f api

# Base de données seulement
docker-compose logs -f db

# Logs en temps réel
docker-compose logs -f --tail=100
```

## 📱 Dashboard Web - Configuration

### Servir le Dashboard HTML

Votre fichier `dashboard/sport-km.html` peut être accessible de plusieurs façons :

#### Option 1 : Via Flask (Recommandé)
Ajoutez cette route dans votre API Flask :

```python
from flask import send_from_directory

@app.route('/dashboard/<path:filename>')
def serve_dashboard(filename):
    return send_from_directory('dashboard', filename)
```

Puis accédez à : http://localhost:58001/dashboard/sport-km.html

#### Option 2 : Intégration API Direct
Votre dashboard HTML peut consommer directement les APIs :

```javascript
// Dans sport-km.html
async function loadDashboardData() {
    try {
        const response = await fetch('/api/activities/athlete/1/dashboard-custom');
        const data = await response.json();
        // Traiter les données...
    } catch (error) {
        console.error('Erreur chargement données:', error);
    }
}
```

#### Option 3 : Static Files
Configurez Flask pour servir les fichiers statiques :

```python
app = Flask(__name__, static_folder='dashboard', static_url_path='/dashboard')
```

## 🎯 Résultats Obtenus

### 📊 Couverture des Données
- ✅ **1455 activités** synchronisées et analysées
- ✅ **99.9% métriques enrichies** (Strava natives)
- ✅ **100% calculs personnalisés** disponibles
- ✅ **Records automatiques** détectés et validés

### 🏆 Profil Sportif Analysé
- 🚴 **Vélo** : FTP ~240W, pic 1min à 318W
- 🏃 **Course** : Records 1km=4:17, 10km=4:26/km
- 📈 **Progression** : IF moyen 1.049, charge optimisée

### 🛠️ Fonctionnalités Actives
- ⚡ Synchronisation automatique Strava
- 📊 Calculs en temps réel
- 🌐 Dashboard web interactif
- 📁 Export CSV enrichi
- 🔍 Analyses prédictives

---

## 📄 Commandes de Référence

### Makefile Disponible
```bash
make help          # Voir toutes les commandes
make build         # Construire les images
make up            # Démarrer les services
make down          # Arrêter les services
make restart       # Redémarrer
make logs          # Voir les logs
make status        # Statut des services
make clean         # Nettoyage complet
```

### API Quick Start
```bash
# Séquence complète de démarrage
cd ~/Documents/dev/strava-analytics
make up && sleep 15
curl -X POST http://localhost:58001/api/activities/athlete/1/settings -H "Content-Type: application/json" -d '{"ftp": 240}'
curl -X POST http://localhost:58001/api/activities/athlete/1/calculate-custom-metrics
open http://localhost:58001/dashboard/sport-km.html
```

---

**🎯 Votre système Strava Analytics est opérationnel avec dashboard web intégré !**

**Accès rapide :** `make up` puis http://localhost:58001/dashboard/sport-km.html 🚀