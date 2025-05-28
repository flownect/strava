import requests
from datetime import datetime, timedelta
import time
from flask import current_app
from models.database import db, Athlete, ActivitySummary
from models.strava_metrics import ActivityStravaMetrics

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
    
    def get_detailed_activity(self, activity_id, access_token):
        """Récupérer une activité avec tous les détails pour les métriques avancées"""
        self.rate_limit_wait()
        headers = {'Authorization': f'Bearer {access_token}'}
        
        try:
            response = requests.get(
                f'{self.base_url}/activities/{activity_id}',
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Erreur récupération activité détaillée {activity_id}: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Erreur récupération activité détaillée {activity_id}: {str(e)}")
            return None
    
    def sync_athlete_activities(self, athlete_id):
        """Synchroniser toutes les activités d'un athlète avec métriques enrichies"""
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
        total_enriched_activities = 0
        
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
                    # Traitement de base
                    if self.process_activity(activity_data, athlete_id):
                        total_new_activities += 1
                        
                        # Enrichissement avec métriques Strava avancées
                        if self.enrich_activity_with_strava_metrics(activity_data, athlete.access_token):
                            total_enriched_activities += 1
                
                if len(activities) < 200:
                    break
                
                page += 1
                
            except Exception as e:
                print(f"Erreur lors de la synchronisation: {str(e)}")
                break
        
        return {
            'synchronized_activities': total_new_activities,
            'enriched_activities': total_enriched_activities
        }
    
    def process_activity(self, strava_activity, athlete_id):
        """Traiter et enregistrer une activité (code existant)"""
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
    
    def enrich_activity_with_strava_metrics(self, strava_activity, access_token):
        """Enrichir une activité avec les métriques Strava avancées"""
        try:
            # Récupérer l'activité de la base
            activity_db = ActivitySummary.query.filter_by(
                strava_id=strava_activity['id']
            ).first()
            
            if not activity_db:
                print(f"Activité {strava_activity['id']} non trouvée en base")
                return False
            
            # Vérifier si les métriques existent déjà
            existing_metrics = ActivityStravaMetrics.query.filter_by(
                activity_id=activity_db.id
            ).first()
            
            if existing_metrics:
                print(f"Métriques déjà existantes pour activité {activity_db.id}")
                return False
            
            # Récupérer les détails complets si nécessaire
            detailed_activity = strava_activity
            
            # Si l'activité summary ne contient pas assez de détails, récupérer la version complète
            if not strava_activity.get('device_watts') and not strava_activity.get('suffer_score'):
                detailed_activity = self.get_detailed_activity(strava_activity['id'], access_token)
                if not detailed_activity:
                    detailed_activity = strava_activity
            
            # Créer les métriques Strava
            strava_metrics = ActivityStravaMetrics(
                activity_id=activity_db.id,
                
                # 💪 Données de puissance natives Strava
                average_watts=detailed_activity.get('average_watts'),
                weighted_average_watts=detailed_activity.get('weighted_average_watts'),
                max_watts=detailed_activity.get('max_watts'),
                device_watts=detailed_activity.get('device_watts', False),
                
                # ❤️ Données FC natives Strava
                average_heartrate=detailed_activity.get('average_heartrate'),
                max_heartrate=detailed_activity.get('max_heartrate'),
                has_heartrate=detailed_activity.get('has_heartrate', False),
                
                # 🎯 Métriques d'effort Strava
                suffer_score=detailed_activity.get('suffer_score'),
                perceived_exertion=detailed_activity.get('perceived_exertion'),
                
                # 🚴‍♂️ Données vélo spécifiques
                average_cadence=detailed_activity.get('average_cadence'),
                average_temp=detailed_activity.get('average_temp'),
                trainer=detailed_activity.get('trainer', False),
                commute=detailed_activity.get('commute', False),
                
                # 🏃‍♂️ Données course/vitesse
                average_speed_ms=detailed_activity.get('average_speed'),
                max_speed_ms=detailed_activity.get('max_speed'),
                
                # 📍 Métadonnées
                gear_id=detailed_activity.get('gear_id'),
                external_id=detailed_activity.get('external_id'),
                upload_id=detailed_activity.get('upload_id')
            )
            
            db.session.add(strava_metrics)
            db.session.commit()
            
            print(f"Métriques Strava ajoutées pour activité {activity_db.id} - "
                  f"Power: {strava_metrics.weighted_average_watts}W, "
                  f"Suffer: {strava_metrics.suffer_score}")
            
            return True
            
        except Exception as e:
            print(f"Erreur enrichissement métriques Strava pour activité {strava_activity.get('id', 'N/A')}: {str(e)}")
            db.session.rollback()
            return False
    
    def sync_single_activity_enhanced(self, activity_id, athlete_id):
        """Synchroniser une activité spécifique avec enrichissement complet"""
        athlete = Athlete.query.get(athlete_id)
        if not athlete:
            return {'error': 'Athlete not found'}
        
        try:
            # Récupérer l'activité détaillée depuis Strava
            detailed_activity = self.get_detailed_activity(activity_id, athlete.access_token)
            if not detailed_activity:
                return {'error': 'Activity not found on Strava'}
            
            # Traitement de base
            base_success = self.process_activity(detailed_activity, athlete_id)
            
            # Enrichissement avec métriques
            metrics_success = False
            if base_success:
                metrics_success = self.enrich_activity_with_strava_metrics(detailed_activity, athlete.access_token)
            
            return {
                'activity_id': activity_id,
                'base_sync': base_success,
                'metrics_sync': metrics_success,
                'status': 'success' if (base_success and metrics_success) else 'partial'
            }
            
        except Exception as e:
            return {'error': f'Failed to sync activity {activity_id}: {str(e)}'}
    
    def update_existing_activities_with_metrics(self, athlete_id, limit=50):
        """Mettre à jour les activités existantes sans métriques Strava"""
        athlete = Athlete.query.get(athlete_id)
        if not athlete:
            return {'error': 'Athlete not found'}
        
        # Récupérer les activités sans métriques Strava
        activities_without_metrics = db.session.query(ActivitySummary)\
            .outerjoin(ActivityStravaMetrics, ActivitySummary.id == ActivityStravaMetrics.activity_id)\
            .filter(ActivitySummary.athlete_id == athlete_id)\
            .filter(ActivityStravaMetrics.id.is_(None))\
            .order_by(ActivitySummary.start_date.desc())\
            .limit(limit).all()
        
        updated_count = 0
        
        for activity in activities_without_metrics:
            try:
                # Récupérer les détails depuis Strava
                detailed_activity = self.get_detailed_activity(activity.strava_id, athlete.access_token)
                if detailed_activity:
                    if self.enrich_activity_with_strava_metrics(detailed_activity, athlete.access_token):
                        updated_count += 1
                        
                # Respecter le rate limiting
                time.sleep(0.2)  # 200ms entre les requêtes
                
            except Exception as e:
                print(f"Erreur mise à jour activité {activity.id}: {str(e)}")
                continue
        
        return {
            'activities_updated': updated_count,
            'activities_processed': len(activities_without_metrics)
        }
    
    def get_athlete_training_summary(self, athlete_id, days=30):
        """Résumé d'entraînement enrichi pour un athlète"""
        try:
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Statistiques de base
            base_stats = db.session.query(ActivitySummary)\
                .filter(ActivitySummary.athlete_id == athlete_id)\
                .filter(ActivitySummary.start_date_local >= cutoff_date).all()
            
            # Statistiques avec métriques Strava
            metrics_stats = ActivityStravaMetrics.get_athlete_power_summary(athlete_id, days)
            
            # Activités récentes avec métriques
            recent_activities = db.session.query(ActivitySummary, ActivityStravaMetrics)\
                .outerjoin(ActivityStravaMetrics, ActivitySummary.id == ActivityStravaMetrics.activity_id)\
                .filter(ActivitySummary.athlete_id == athlete_id)\
                .filter(ActivitySummary.start_date_local >= cutoff_date)\
                .order_by(ActivitySummary.start_date_local.desc())\
                .limit(10).all()
            
            return {
                'period_days': days,
                'total_activities': len(base_stats),
                'total_distance_km': sum(float(a.distance_km) for a in base_stats),
                'total_time_hours': sum(float(a.moving_time_hours) for a in base_stats),
                'power_metrics': metrics_stats,
                'recent_activities': [
                    {
                        'activity': activity.to_dict(),
                        'strava_metrics': metrics.to_dict() if metrics else None
                    }
                    for activity, metrics in recent_activities
                ]
            }
            
        except Exception as e:
            print(f"Erreur résumé d'entraînement: {str(e)}")
            return {'error': str(e)}