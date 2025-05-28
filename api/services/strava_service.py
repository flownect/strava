import requests
from datetime import datetime, timedelta
import time
from flask import current_app
from models.database import db, Athlete, ActivitySummary

class StravaService:
    def __init__(self):
        self.client_id = current_app.config['STRAVA_CLIENT_ID']
        self.client_secret = current_app.config['STRAVA_CLIENT_SECRET']
        self.base_url = current_app.config['STRAVA_API_BASE_URL']
        self.requests_count = 0
        self.last_request_time = time.time()
    
    def rate_limit_wait(self):
        """Respecter les limites de taux de Strava (100 req/15min)"""
        current_time = time.time()
        if current_time - self.last_request_time < 15 * 60:
            if self.requests_count >= 95:
                wait_time = 15 * 60 - (current_time - self.last_request_time)
                print(f"Rate limit atteint, attente de {wait_time/60:.1f} minutes...")
                time.sleep(wait_time)
                self.requests_count = 0
                self.last_request_time = time.time()
        else:
            self.requests_count = 0
            self.last_request_time = current_time
        
        self.requests_count += 1
    
    def exchange_code_for_token(self, code):
        """Échanger le code d'autorisation contre des tokens"""
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'grant_type': 'authorization_code'
        }
        
        response = requests.post(current_app.config['STRAVA_TOKEN_URL'], data=data)
        return response.json()
    
    def refresh_token(self, refresh_token):
        """Actualiser le token d'accès"""
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token'
        }
        
        response = requests.post(current_app.config['STRAVA_TOKEN_URL'], data=data)
        return response.json()
    
    def get_authenticated_athlete(self, access_token):
        """Récupérer les informations de l'athlète authentifié"""
        self.rate_limit_wait()
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(f'{self.base_url}/athlete', headers=headers)
        return response.json()
    
    def get_athlete_activities(self, access_token, page=1, per_page=200, before=None, after=None):
        """Récupérer les activités de l'athlète"""
        self.rate_limit_wait()
        headers = {'Authorization': f'Bearer {access_token}'}
        params = {
            'page': page,
            'per_page': per_page
        }
        
        if before:
            params['before'] = int(before.timestamp())
        if after:
            params['after'] = int(after.timestamp())
        
        response = requests.get(f'{self.base_url}/athlete/activities', 
                              headers=headers, params=params)
        return response.json()
    
    def sync_athlete_activities(self, athlete_id):
        """Synchroniser toutes les activités d'un athlète"""
        athlete = Athlete.query.get(athlete_id)
        if not athlete:
            return {'error': 'Athlete not found'}
        
        # Vérifier si le token est valide
        if athlete.token_expires_at and athlete.token_expires_at < datetime.utcnow():
            # Actualiser le token
            try:
                token_data = self.refresh_token(athlete.refresh_token)
                athlete.access_token = token_data.get('access_token')
                athlete.refresh_token = token_data.get('refresh_token')
                athlete.token_expires_at = datetime.utcnow() + timedelta(seconds=token_data.get('expires_in', 21600))
                db.session.commit()
            except Exception as e:
                return {'error': f'Failed to refresh token: {str(e)}'}
        
        # Récupérer la dernière activité synchronisée
        last_activity = ActivitySummary.query.filter_by(athlete_id=athlete_id)\
                                           .order_by(ActivitySummary.start_date.desc())\
                                           .first()
        
        after_date = last_activity.start_date if last_activity else None
        
        # Récupérer les nouvelles activités
        page = 1
        total_new_activities = 0
        
        while True:
            try:
                activities = self.get_athlete_activities(
                    athlete.access_token, 
                    page=page, 
                    after=after_date
                )
                
                if not activities or 'errors' in activities:
                    break
                
                for activity_data in activities:
                    if self.process_activity(activity_data, athlete_id):
                        total_new_activities += 1
                
                if len(activities) < 200:
                    break
                
                page += 1
                
            except Exception as e:
                print(f"Erreur lors de la synchronisation: {str(e)}")
                break
        
        return {'synchronized_activities': total_new_activities}
    
    def process_activity(self, strava_activity, athlete_id):
        """Traiter et enregistrer une activité"""
        try:
            # Vérifier si l'activité existe déjà
            existing = ActivitySummary.query.filter_by(strava_id=strava_activity['id']).first()
            if existing:
                return False
            
            # Calculer les métriques
            start_date_local = datetime.fromisoformat(strava_activity['start_date_local'].replace('Z', '+00:00'))
            moving_time_hours = strava_activity.get('moving_time', 0) / 3600
            elapsed_time_hours = strava_activity.get('elapsed_time', 0) / 3600
            
            # Noms des jours et mois en français
            day_names = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
            month_names = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                          'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
            
            activity = ActivitySummary(
                strava_id=strava_activity['id'],
                athlete_id=athlete_id,
                name=strava_activity.get('name', ''),
                type=strava_activity.get('type', ''),
                sport_type=strava_activity.get('sport_type', ''),
                start_date=datetime.fromisoformat(strava_activity['start_date'].replace('Z', '+00:00')),
                start_date_local=start_date_local,
                distance_km=strava_activity.get('distance', 0) / 1000,
                moving_time_seconds=strava_activity.get('moving_time', 0),
                elapsed_time_seconds=strava_activity.get('elapsed_time', 0),
                moving_time_hours=round(moving_time_hours, 2),
                elapsed_time_hours=round(elapsed_time_hours, 2),
                # Données temporelles détaillées
                year=start_date_local.year,
                month=start_date_local.month,
                day=start_date_local.day,
                week=start_date_local.isocalendar()[1],
                day_of_week=start_date_local.weekday(),
                day_name=day_names[start_date_local.weekday()],
                month_name=month_names[start_date_local.month - 1],
                average_speed=strava_activity.get('average_speed'),
                max_speed=strava_activity.get('max_speed'),
                total_elevation_gain=strava_activity.get('total_elevation_gain'),
                average_heartrate=strava_activity.get('average_heartrate'),
                max_heartrate=strava_activity.get('max_heartrate'),
                calories=strava_activity.get('calories')
            )
            
            db.session.add(activity)
            db.session.commit()
            return True
            
        except Exception as e:
            print(f"Erreur lors du traitement de l'activité {strava_activity.get('id', 'N/A')}: {str(e)}")
            db.session.rollback()
            return False