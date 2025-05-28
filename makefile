.PHONY: help build up start stop restart status logs clean backup shell-api shell-db

help: ## Afficher cette aide
	@echo "🚀 Strava Analytics - Commandes disponibles:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "📝 Exemples:"
	@echo "  make build    # Construire les images"
	@echo "  make up       # Démarrer le projet"
	@echo "  make logs     # Voir les logs en temps réel"

build: ## Construire les images Docker
	@echo "🔨 Construction des images Docker..."
	docker-compose build

up: build ## Démarrer tous les services
	@echo "🚀 Démarrage des services..."
	docker-compose up -d
	@echo "✅ Services démarrés!"
	@echo "🌐 API disponible sur: http://localhost:58001"
	@echo "🔐 Authentification Strava: http://localhost:58001/auth/strava"

start: up ## Alias pour up

stop: ## Arrêter tous les services
	@echo "🛑 Arrêt des services..."
	docker-compose stop
	@echo "✅ Services arrêtés"

restart: ## Redémarrer tous les services
	@echo "🔄 Redémarrage des services..."
	docker-compose restart
	@echo "✅ Services redémarrés"

status: ## Afficher le statut des services
	@echo "📊 Statut des services:"
	docker-compose ps

logs: ## Afficher tous les logs en temps réel
	@echo "📋 Logs en temps réel (Ctrl+C pour arrêter):"
	docker-compose logs -f

logs-api: ## Afficher les logs de l'API seulement
	@echo "📋 Logs API:"
	docker-compose logs -f api

logs-db: ## Afficher les logs de la base de données
	@echo "📋 Logs PostgreSQL:"
	docker-compose logs -f db

logs-sync: ## Afficher les logs du synchroniseur
	@echo "📋 Logs Synchroniseur:"
	docker-compose logs -f sync-scheduler

clean: ## Nettoyer complètement (⚠️ supprime les données!)
	@echo "⚠️  ATTENTION: Cette commande va supprimer TOUTES les données!"
	@read -p "Êtes-vous sûr? (tapez 'oui' pour confirmer): " confirm && [ "$$confirm" = "oui" ] || exit 1
	@echo "🧹 Nettoyage complet..."
	docker-compose down -v
	docker system prune -f
	@echo "✅ Nettoyage terminé"

backup: ## Créer une sauvegarde de la base de données
	@echo "💾 Création d'une sauvegarde..."
	@mkdir -p database/backup
	@docker-compose exec -T db pg_dump -U strava_user strava_analytics_db > database/backup/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "✅ Sauvegarde créée dans database/backup/"

shell-api: ## Accéder au shell du container API
	@echo "🐚 Accès au shell API..."
	docker-compose exec api /bin/bash

shell-db: ## Accéder au shell PostgreSQL
	@echo "🐚 Accès à PostgreSQL..."
	docker-compose exec db psql -U strava_user strava_analytics_db

test-api: ## Tester que l'API fonctionne
	@echo "🧪 Test de l'API..."
	@curl -s http://localhost:58001/health | grep -q "healthy" && echo "✅ API fonctionne" || echo "❌ API ne répond pas"

init: ## Initialiser le projet (première installation)
	@echo "🎯 Initialisation du projet Strava Analytics..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "📝 Fichier .env créé. Configurez vos paramètres Strava!"; \
	else \
		echo "📝 Fichier .env existe déjà"; \
	fi
	@mkdir -p data/exports database/backup logs
	@touch data/exports/.gitkeep database/backup/.gitkeep logs/.gitkeep
	@echo "✅ Initialisation terminée!"
	@echo ""
	@echo "📋 Prochaines étapes:"
	@echo "  1. Éditez le fichier .env avec vos paramètres Strava"
	@echo "  2. Lancez: make up"
	@echo "  3. Allez sur: http://localhost:58001/auth/strava"

dev: ## Mode développement avec logs
	@echo "🛠️  Mode développement..."
	docker-compose up --build

quick-test: up ## Test rapide du système complet
	@echo "🏃 Test rapide du système..."
	@sleep 5
	@make test-api
	@echo "📊 Vérification des services:"
	@make status

# Commandes avancées
reset-db: ## Réinitialiser uniquement la base de données
	@echo "⚠️  Réinitialisation de la base de données..."
	docker-compose stop db
	docker volume rm strava-analytics_postgres-data 2>/dev/null || true
	docker-compose up -d db
	@echo "✅ Base de données réinitialisée"

update: ## Mettre à jour le projet
	@echo "🔄 Mise à jour du projet..."
	git pull
	docker-compose build
	docker-compose up -d
	@echo "✅ Projet mis à jour"

install: init up ## Installation complète (init + démarrage)
	@echo "🎉 Installation terminée!"
	@echo "🌐 Votre application est disponible sur: http://localhost:58001"