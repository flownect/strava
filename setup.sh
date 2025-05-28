#!/bin/bash

# Script d'installation automatique pour Strava Analytics
# Usage: ./setup.sh

set -e  # Arrêter en cas d'erreur

echo "🚀 Installation de Strava Analytics"
echo "====================================="

# Vérifications préalables
echo "🔍 Vérification des prérequis..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker n'est pas installé. Veuillez l'installer d'abord."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose n'est pas installé. Veuillez l'installer d'abord."
    exit 1
fi

echo "✅ Docker et Docker Compose détectés"

# Création de la structure
echo ""
echo "📁 Création de la structure du projet..."

# Créer les dossiers
mkdir -p api/{models,services,routes}
mkdir -p database/backup
mkdir -p data/exports
mkdir -p scripts
mkdir -p logs

# Créer les fichiers __init__.py
touch api/models/__init__.py
touch api/services/__init__.py  
touch api/routes/__init__.py

# Créer les fichiers .gitkeep
touch data/exports/.gitkeep
touch database/backup/.gitkeep
touch logs/.gitkeep

echo "✅ Structure créée"

# Fichier .env
echo ""
echo "📝 Configuration de l'environnement..."

if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ Fichier .env créé depuis .env.example"
    else
        echo "⚠️  Fichier .env.example non trouvé, création manuelle"
        cat > .env << EOF
# Base de données PostgreSQL
POSTGRES_USER=strava_user
POSTGRES_PASSWORD=VotreMoTdePasseSecurise123!
POSTGRES_DB=strava_analytics_db

# Configuration Strava API (à configurer)
STRAVA_CLIENT_ID=your_strava_client_id
STRAVA_CLIENT_SECRET=your_strava_client_secret
STRAVA_REDIRECT_URI=http://localhost:58001/auth/strava/callback

# Configuration application
FLASK_SECRET_KEY=votre_cle_secrete_flask_tres_longue_et_complexe
FLASK_ENV=production
EOF
    fi
else
    echo "📝 Fichier .env existe déjà"
fi

# Vérifier les paramètres Strava
echo ""
echo "🔐 Configuration Strava API"
echo "============================"

if grep -q "your_strava_client_id" .env; then
    echo "⚠️  IMPORTANT: Vous devez configurer vos paramètres Strava dans .env"
    echo ""
    echo "📋 Étapes à suivre:"
    echo "  1. Allez sur https://www.strava.com/settings/api"
    echo "  2. Créez une nouvelle application"
    echo "  3. Configurez:"
    echo "     - Authorization Callback Domain: localhost"
    echo "     - Website: http://localhost:58001"
    echo "  4. Copiez Client ID et Client Secret dans .env"
    echo ""
    
    read -p "Voulez-vous éditer .env maintenant? (o/n): " edit_env
    if [[ $edit_env =~ ^[Oo]$ ]]; then
        ${EDITOR:-nano} .env
    fi
fi

# Construction et démarrage
echo ""
echo "🔨 Construction des images Docker..."
docker-compose build

echo ""
echo "🚀 Démarrage des services..."
docker-compose up -d

# Attendre que les services soient prêts
echo ""
echo "⏳ Attente du démarrage des services..."
sleep 10

# Vérifier que les services tournent
echo ""
echo "📊 Vérification des services..."
docker-compose ps

# Test de l'API
echo ""
echo "🧪 Test de l'API..."
if curl -s http://localhost:58001/health | grep -q "healthy"; then
    echo "✅ API fonctionne correctement"
else
    echo "⚠️  API ne répond pas encore, vérifiez les logs avec: make logs"
fi

# Instructions finales
echo ""
echo "🎉 Installation terminée!"
echo "========================="
echo ""
echo "🌐 Votre application est accessible sur:"
echo "   http://localhost:58001"
echo ""
echo "🔐 Pour vous connecter à Strava:"
echo "   http://localhost:58001/auth/strava"
echo ""
echo "📋 Commandes utiles:"
echo "   make logs       # Voir les logs"
echo "   make status     # Statut des services"
echo "   make stop       # Arrêter les services"
echo "   make backup     # Sauvegarder la base"
echo ""

if grep -q "your_strava_client_id" .env; then
    echo "⚠️  ATTENTION: N'oubliez pas de configurer vos paramètres Strava dans .env"
    echo "   Éditez le fichier .env puis redémarrez avec: make restart"
else
    echo "✅ Configuration Strava détectée"
    echo "   Vous pouvez maintenant vous authentifier sur Strava!"
fi

echo ""
echo "📖 Documentation complète dans README.md"
echo "🆘 En cas de problème: make logs"
echo ""
echo "🚀 Bon entraînement avec Strava Analytics!"