from flask import Blueprint, request, redirect, session, jsonify, current_app
from models.database import db, Athlete
from services.strava_service import StravaService
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/strava')
def strava_auth():
    """Rediriger vers l'autorisation Strava"""
    auth_url = (
        f"{current_app.config['STRAVA_AUTHORIZE_URL']}?"
        f"client_id={current_app.config['STRAVA_CLIENT_ID']}&"
        f"response_type=code&"
        f"redirect_uri={current_app.config['STRAVA_REDIRECT_URI']}&"
        f"scope=read,activity:read_all,profile:read_all"
    )
    return redirect(auth_url)

@auth_bp.route('/strava/callback')
def strava_callback():
    """Handle du callback Strava"""
    code = request.args.get('code')
    error = request.args.get('error')
    
    if error:
        return jsonify({'error': f'Strava authorization error: {error}'}), 400
    
    if not code:
        return jsonify({'error': 'No authorization code received'}), 400
    
    try:
        strava_service = StravaService()
        
        # Échanger le code contre des tokens
        token_data = strava_service.exchange_code_for_token(code)
        
        if 'access_token' not in token_data:
            return jsonify({'error': 'Failed to get access token', 'details': token_data}), 400
        
        # Récupérer les informations de l'athlète
        athlete_data = strava_service.get_authenticated_athlete(token_data['access_token'])
        
        if 'id' not in athlete_data:
            return jsonify({'error': 'Failed to get athlete data', 'details': athlete_data}), 400
        
        # Sauvegarder ou mettre à jour l'athlète
        athlete = Athlete.query.filter_by(strava_id=athlete_data['id']).first()
        
        if not athlete:
            athlete = Athlete(strava_id=athlete_data['id'])
            db.session.add(athlete)
        
        # Mettre à jour les informations
        athlete.username = athlete_data.get('username')
        athlete.firstname = athlete_data.get('firstname')
        athlete.lastname = athlete_data.get('lastname')
        athlete.city = athlete_data.get('city')
        athlete.state = athlete_data.get('state')
        athlete.country = athlete_data.get('country')
        athlete.sex = athlete_data.get('sex')
        athlete.premium = athlete_data.get('premium', False)
        athlete.profile_medium = athlete_data.get('profile_medium')
        athlete.profile = athlete_data.get('profile')
        
        # Tokens
        athlete.access_token = token_data['access_token']
        athlete.refresh_token = token_data['refresh_token']
        athlete.token_expires_at = datetime.utcnow() + timedelta(seconds=token_data.get('expires_in', 21600))
        athlete.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Déclencher la synchronisation des activités
        print(f"Démarrage de la synchronisation pour l'athlète {athlete.firstname} {athlete.lastname}")
        sync_result = strava_service.sync_athlete_activities(athlete.id)
        
        return jsonify({
            'message': 'Authentification réussie !',
            'athlete': {
                'id': athlete.id,
                'strava_id': athlete.strava_id,
                'name': f"{athlete.firstname} {athlete.lastname}",
                'username': athlete.username,
                'city': athlete.city,
                'country': athlete.country
            },
            'sync_result': sync_result,
            'next_steps': [
                f'Voir vos activités: /api/activities/athlete/{athlete.id}',
                f'Statistiques mensuelles: /api/analytics/athlete/{athlete.id}/monthly',
                f'Analyse par jour: /api/analytics/athlete/{athlete.id}/day-of-week'
            ]
        })
        
    except Exception as e:
        print(f"Erreur lors de l'authentification: {str(e)}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@auth_bp.route('/status')
def auth_status():
    """Vérifier le statut d'authentification"""
    athletes = Athlete.query.all()
    return jsonify({
        'total_athletes': len(athletes),
        'authenticated_athletes': [
            {
                'id': athlete.id,
                'strava_id': athlete.strava_id,
                'name': f"{athlete.firstname} {athlete.lastname}",
                'username': athlete.username,
                'token_expires_at': athlete.token_expires_at.isoformat() if athlete.token_expires_at else None,
                'activities_count': len(athlete.activities)
            }
            for athlete in athletes
        ]
    })

@auth_bp.route('/refresh/<int:athlete_id>')
def refresh_athlete_token(athlete_id):
    """Actualiser manuellement le token d'un athlète"""
    athlete = Athlete.query.get(athlete_id)
    if not athlete:
        return jsonify({'error': 'Athlete not found'}), 404
    
    try:
        strava_service = StravaService()
        token_data = strava_service.refresh_token(athlete.refresh_token)
        
        athlete.access_token = token_data.get('access_token')
        athlete.refresh_token = token_data.get('refresh_token')
        athlete.token_expires_at = datetime.utcnow() + timedelta(seconds=token_data.get('expires_in', 21600))
        
        db.session.commit()
        
        return jsonify({
            'message': 'Token refreshed successfully',
            'expires_at': athlete.token_expires_at.isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500