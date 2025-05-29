from flask import Flask, request, jsonify, redirect, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from config import Config
from models.database import db
from routes.auth import auth_bp
from routes.activities import activities_bp
from routes.analytics import analytics_bp
import os
import traceback

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialisation de la base de données
    db.init_app(app)
    
    # Enregistrement des blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(activities_bp, url_prefix='/api/activities')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    
    @app.route('/')
    def index():
        return jsonify({
            'message': 'Strava Analytics API',
            'version': '1.0.0',
            'status': 'running',
            'endpoints': {
                'auth': '/auth/strava',
                'activities': '/api/activities',
                'analytics': '/api/analytics',
                'dashboard': '/dashboard/sport-km.html'
            }
        })
    
    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy'})
    
    # ========== ROUTES DASHBOARD ==========
    
    @app.route('/dashboard/<path:filename>')
    def serve_dashboard(filename):
        """
        Sert les fichiers HTML du dashboard depuis le dossier /dashboard
        """
        try:
            # Le fichier est dans dashboard/ depuis la racine du projet
            # Dans Docker, on est dans /app, donc dashboard/ est accessible directement
            dashboard_path = os.path.join('/app', 'dashboard')
            
            # Vérifier si le fichier existe
            full_path = os.path.join(dashboard_path, filename)
            if os.path.exists(full_path):
                return send_from_directory(dashboard_path, filename)
            else:
                # Si pas trouvé dans Docker, essayer depuis la racine locale
                local_dashboard_path = os.path.join(os.path.dirname(__file__), '..', 'dashboard')
                if os.path.exists(os.path.join(local_dashboard_path, filename)):
                    return send_from_directory(local_dashboard_path, filename)
                
                return jsonify({
                    'error': 'Dashboard file not found',
                    'filename': filename,
                    'searched_paths': [dashboard_path, local_dashboard_path]
                }), 404
                
        except Exception as e:
            return jsonify({
                'error': 'Error serving dashboard',
                'message': str(e)
            }), 500
    
    @app.route('/dashboard')
    @app.route('/dashboard/')
    def dashboard_home():
        """
        Redirige vers le dashboard principal
        """
        return redirect('/dashboard/sport-km.html')
    
    # Route de debug pour voir les fichiers disponibles
    @app.route('/dashboard/debug')
    def dashboard_debug():
        """
        Debug: voir les fichiers dans le dossier dashboard
        """
        try:
            paths_to_check = [
                os.path.join('/app', 'dashboard'),
                os.path.join(os.path.dirname(__file__), '..', 'dashboard')
            ]
            
            result = {}
            for i, path in enumerate(paths_to_check):
                if os.path.exists(path):
                    files = os.listdir(path)
                    result[f'path_{i}'] = {
                        'path': path,
                        'exists': True,
                        'files': files
                    }
                else:
                    result[f'path_{i}'] = {
                        'path': path,
                        'exists': False
                    }
            
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)})
    
    # ========== GESTIONNAIRE D'ERREURS GLOBAL (NOUVEAU) ==========
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        """Gestionnaire d'erreurs global pour voir les stack traces"""
        # Log l'erreur complète dans la console
        print("="*50)
        print("ERREUR DÉTECTÉE:")
        print(f"Type: {type(e).__name__}")
        print(f"Message: {str(e)}")
        print("Stack trace:")
        traceback.print_exc()
        print("="*50)
        
        # Retourner l'erreur détaillée au client (pour debug)
        return jsonify({
            'error': str(e),
            'type': type(e).__name__,
            'traceback': traceback.format_exc()
        }), 500
    
    # Configuration CORS pour le dashboard
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
        return response
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    with app.app_context():
        db.create_all()
    
    # CHANGÉ: Debug activé temporairement
    app.run(host='0.0.0.0', port=5000, debug=True)