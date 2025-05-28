from flask import Flask, request, jsonify, redirect, session
from flask_sqlalchemy import SQLAlchemy
from config import Config
from models.database import db
from routes.auth import auth_bp
from routes.activities import activities_bp
from routes.analytics import analytics_bp
import os

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
                'analytics': '/api/analytics'
            }
        })
    
    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy'})
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    with app.app_context():
        db.create_all()
    
    app.run(host='0.0.0.0', port=5000, debug=False)