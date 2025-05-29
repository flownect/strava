from models.database import db, ActivitySummary
from models.strava_metrics import ActivityStravaMetrics
from models.custom_metrics import ActivityCustomMetrics, AthleteSettings
from datetime import datetime
import math

class CustomCalculationsService:
    """
    Service pour calculs personnalisés basés sur données Strava existantes
    """
    
    def __init__(self):
        self.default_ftp = 245  # Votre FTP par défaut
    
    def calculate_custom_tss(self, normalized_power, duration_hours, user_ftp):
        """
        Calculer TSS personnalisé avec formule standard
        TSS = (durée_heures * NP * IF) / FTP * 100
        où IF = NP / FTP
        """
        if not normalized_power or not duration_hours or not user_ftp:
            return None
            
        if user_ftp <= 0 or duration_hours <= 0:
            return None
            
        # ✅ CORRECTION : Conversion en float pour éviter l'erreur Decimal
        np_float = float(normalized_power)
        duration_float = float(duration_hours)
        ftp_float = float(user_ftp)
        
        intensity_factor = np_float / ftp_float
        tss = (duration_float * np_float * intensity_factor) / ftp_float * 100
        
        return round(tss, 1)
    
    def calculate_intensity_factor(self, normalized_power, user_ftp):
        """Calculer l'Intensity Factor (IF = NP / FTP)"""
        if not normalized_power or not user_ftp or user_ftp <= 0:
            return None
        
        # ✅ CORRECTION : Conversion en float
        return round(float(normalized_power) / float(user_ftp), 4)
    
    def estimate_power_records(self, activity, strava_metrics):
        """
        Estimer les records de puissance basés sur la durée et NP
        AVEC FILTRES INTELLIGENTS pour éviter les données aberrantes
        """
        # ✅ FILTRE 1: Seulement activités avec puissance (vélo)
        if activity.type not in ['Ride', 'VirtualRide', 'EBikeRide']:
            return {
                'best_1min_power': None,
                'best_5min_power': None,
                'best_20min_power': None
            }
        
        if not strava_metrics or not strava_metrics.weighted_average_watts:
            return {
                'best_1min_power': None,
                'best_5min_power': None,
                'best_20min_power': None
            }
        
        np = float(strava_metrics.weighted_average_watts)
        duration_minutes = float(activity.moving_time_hours or 0) * 60
        
        # ✅ FILTRE 2: Ignorer puissances aberrantes
        # Plus de 600W soutenu = niveau pro/données suspectes
        if np > 600:
            return {
                'best_1min_power': None,
                'best_5min_power': None,
                'best_20min_power': None
            }
        
        # ✅ FILTRE 3: Ignorer puissances trop faibles (< 50W = erreur)
        if np < 50:
            return {
                'best_1min_power': None,
                'best_5min_power': None,
                'best_20min_power': None
            }
        
        # ✅ FILTRE 4: Ignorer activités sans durée
        if duration_minutes <= 0:
            return {
                'best_1min_power': None,
                'best_5min_power': None,
                'best_20min_power': None
            }
        
        # Facteurs d'estimation basés sur courbes de puissance typiques
        if duration_minutes >= 20:
            # Activité de 20+ min, NP est proche de la puissance 20min
            best_20min = int(np)
            best_5min = int(np * 1.15)   # ~15% plus élevé pour 5min
            best_1min = int(np * 1.35)   # ~35% plus élevé pour 1min
        elif duration_minutes >= 5:
            # Activité de 5-20min
            best_20min = int(np * 0.95)  # Légèrement en dessous
            best_5min = int(np)
            best_1min = int(np * 1.20)
        else:
            # Activité courte < 5min
            best_20min = int(np * 0.85)
            best_5min = int(np * 0.95)
            best_1min = int(np)
        
        # ✅ FILTRE 5: Vérification finale des valeurs
        return {
            'best_1min_power': best_1min if 100 <= best_1min <= 800 else None,
            'best_5min_power': best_5min if 100 <= best_5min <= 600 else None,
            'best_20min_power': best_20min if 100 <= best_20min <= 500 else None
        }
    
    def detect_distance_records(self, activity):
        """
        Détecter les records de distance basés sur distance exacte et temps
        AVEC FILTRES INTELLIGENTS pour éviter les données aberrantes
        """
        # ✅ FILTRE 1: Seulement course/marche pour les records de distance
        if activity.type not in ['Run', 'Walk']:
            return {
                'best_1km_time': None,
                'best_5km_time': None,
                'best_10km_time': None,
                'best_half_marathon_time': None,
                'best_marathon_time': None
            }
        
        distance_km = float(activity.distance_km or 0)
        time_seconds = activity.moving_time_seconds or 0
        
        # ✅ FILTRE 2: Ignorer distance nulle ou temps invalide
        if distance_km <= 0 or time_seconds <= 0:
            return {
                'best_1km_time': None,
                'best_5km_time': None,
                'best_10km_time': None,
                'best_half_marathon_time': None,
                'best_marathon_time': None
            }
        
        # ✅ FILTRE 3: Ignorer les allures aberrantes
        pace_per_km_seconds = time_seconds / distance_km
        # Plus rapide que 2:30/km = suspect (record mondial marathon ~2:55/km)
        if pace_per_km_seconds < 150:  # 2:30/km
            return {
                'best_1km_time': None,
                'best_5km_time': None,
                'best_10km_time': None,
                'best_half_marathon_time': None,
                'best_marathon_time': None
            }
        
        # ✅ FILTRE 4: Ignorer les allures trop lentes (marche très lente)
        # Plus lent que 12:00/km = probablement une erreur
        if pace_per_km_seconds > 720:  # 12:00/km
            return {
                'best_1km_time': None,
                'best_5km_time': None,
                'best_10km_time': None,
                'best_half_marathon_time': None,
                'best_marathon_time': None
            }
        
        # Vérifier les distances standard avec tolérance
        records = {}
        
        # 1km (0.8 - 1.2km)
        if 0.8 <= distance_km <= 1.2:
            records['best_1km_time'] = int(time_seconds * (1.0 / distance_km))
        
        # 5km (4.5 - 5.5km)
        elif 4.5 <= distance_km <= 5.5:
            records['best_5km_time'] = int(time_seconds * (5.0 / distance_km))
        
        # 10km (9.5 - 10.5km)
        elif 9.5 <= distance_km <= 10.5:
            records['best_10km_time'] = int(time_seconds * (10.0 / distance_km))
        
        # Semi-marathon (20 - 22km)
        elif 20.0 <= distance_km <= 22.0:
            records['best_half_marathon_time'] = int(time_seconds * (21.1 / distance_km))
        
        # Marathon (40 - 43km)
        elif 40.0 <= distance_km <= 43.0:
            records['best_marathon_time'] = int(time_seconds * (42.2 / distance_km))
        
        # Remplir les autres avec None
        for distance in ['best_1km_time', 'best_5km_time', 'best_10km_time', 
                        'best_half_marathon_time', 'best_marathon_time']:
            if distance not in records:
                records[distance] = None
                
        return records
    
    def calculate_activity_custom_metrics(self, activity_id, athlete_id, user_ftp=None):
        """
        Calculer toutes les métriques personnalisées pour une activité
        """
        # Récupérer l'activité et ses métriques Strava
        activity = ActivitySummary.query.get(activity_id)
        if not activity:
            return None
        
        strava_metrics = ActivityStravaMetrics.query.filter_by(activity_id=activity_id).first()
        
        # Récupérer ou utiliser FTP par défaut
        if not user_ftp:
            settings = AthleteSettings.query.get(athlete_id)
            user_ftp = settings.current_ftp if settings else self.default_ftp
        
        # Vérifier si calculs déjà existants
        existing = ActivityCustomMetrics.query.filter_by(
            activity_id=activity_id,
            athlete_id=athlete_id
        ).first()
        
        if existing:
            return existing
        
        # Calculs TSS personnalisés
        custom_tss = None
        intensity_factor = None
        
        if strava_metrics and strava_metrics.weighted_average_watts:
            np = float(strava_metrics.weighted_average_watts)
            # ✅ CORRECTION : Gestion des valeurs None
            duration_hours = float(activity.moving_time_hours or 0)
            
            custom_tss = self.calculate_custom_tss(np, duration_hours, user_ftp)
            intensity_factor = self.calculate_intensity_factor(np, user_ftp)
        
        # Records de puissance estimés
        power_records = self.estimate_power_records(activity, strava_metrics)
        
        # Records de distance
        distance_records = self.detect_distance_records(activity)
        
        # Créer l'enregistrement
        custom_metrics = ActivityCustomMetrics(
            activity_id=activity_id,
            athlete_id=athlete_id,
            user_ftp=user_ftp,
            
            # Calculs TSS
            custom_tss=custom_tss,
            intensity_factor=intensity_factor,
            training_load=custom_tss,  # Équivalent pour l'instant
            
            # Records de puissance
            best_1min_power=power_records['best_1min_power'],
            best_5min_power=power_records['best_5min_power'],
            best_20min_power=power_records['best_20min_power'],
            
            # Records de distance
            best_1km_time=distance_records['best_1km_time'],
            best_5km_time=distance_records['best_5km_time'],
            best_10km_time=distance_records['best_10km_time'],
            best_half_marathon_time=distance_records['best_half_marathon_time'],
            best_marathon_time=distance_records['best_marathon_time']
        )
        
        db.session.add(custom_metrics)
        db.session.commit()
        
        return custom_metrics
    
    def calculate_all_athlete_activities(self, athlete_id, user_ftp=None):
        """
        Calculer les métriques personnalisées pour toutes les activités d'un athlète
        """
        if not user_ftp:
            settings = AthleteSettings.get_or_create_for_athlete(athlete_id, self.default_ftp)
            user_ftp = settings.current_ftp
        
        # Récupérer toutes les activités de l'athlète
        activities = ActivitySummary.query.filter_by(athlete_id=athlete_id).all()
        
        calculated_count = 0
        skipped_count = 0
        error_count = 0
        
        for activity in activities:
            try:
                # Vérifier si déjà calculé
                existing = ActivityCustomMetrics.query.filter_by(
                    activity_id=activity.id,
                    athlete_id=athlete_id
                ).first()
                
                if existing:
                    skipped_count += 1
                    continue
                
                # Calculer
                result = self.calculate_activity_custom_metrics(
                    activity.id, 
                    athlete_id, 
                    user_ftp
                )
                
                if result:
                    calculated_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                print(f"Erreur calcul activité {activity.id}: {str(e)}")
                error_count += 1
                continue
        
        return {
            'calculated': calculated_count,
            'skipped': skipped_count,
            'errors': error_count,
            'total_activities': len(activities),
            'user_ftp': user_ftp
        }
    
    def get_athlete_records_summary(self, athlete_id):
        """
        Résumé des records personnels d'un athlète
        """
        records = db.session.query(
            db.func.max(ActivityCustomMetrics.best_1min_power).label('best_1min_power'),
            db.func.max(ActivityCustomMetrics.best_5min_power).label('best_5min_power'),
            db.func.max(ActivityCustomMetrics.best_20min_power).label('best_20min_power'),
            db.func.min(db.func.nullif(ActivityCustomMetrics.best_1km_time, 0)).label('best_1km_time'),
            db.func.min(db.func.nullif(ActivityCustomMetrics.best_5km_time, 0)).label('best_5km_time'),
            db.func.min(db.func.nullif(ActivityCustomMetrics.best_10km_time, 0)).label('best_10km_time'),
            db.func.min(db.func.nullif(ActivityCustomMetrics.best_half_marathon_time, 0)).label('best_half_marathon_time'),
            db.func.min(db.func.nullif(ActivityCustomMetrics.best_marathon_time, 0)).label('best_marathon_time'),
            db.func.avg(ActivityCustomMetrics.custom_tss).label('avg_tss'),
            db.func.max(ActivityCustomMetrics.custom_tss).label('max_tss'),
            db.func.avg(ActivityCustomMetrics.intensity_factor).label('avg_if'),
            db.func.count(ActivityCustomMetrics.id).label('total_activities')
        ).filter_by(athlete_id=athlete_id).first()
        
        if not records or not records.total_activities:
            return None
        
        return {
            'power_records': {
                'best_1min_power': records.best_1min_power,
                'best_5min_power': records.best_5min_power,
                'best_20min_power': records.best_20min_power,
                'estimated_ftp_from_20min': int(float(records.best_20min_power) * 0.95) if records.best_20min_power else None
            },
            'distance_records': {
                'best_1km_time': records.best_1km_time,
                'best_1km_pace': self.format_pace(records.best_1km_time, 1) if records.best_1km_time else None,
                'best_5km_time': records.best_5km_time,
                'best_5km_pace': self.format_pace(records.best_5km_time, 5) if records.best_5km_time else None,
                'best_10km_time': records.best_10km_time,
                'best_10km_pace': self.format_pace(records.best_10km_time, 10) if records.best_10km_time else None,
                'best_half_marathon_time': records.best_half_marathon_time,
                'best_half_marathon_pace': self.format_pace(records.best_half_marathon_time, 21.1) if records.best_half_marathon_time else None,
                'best_marathon_time': records.best_marathon_time,
                'best_marathon_pace': self.format_pace(records.best_marathon_time, 42.2) if records.best_marathon_time else None
            },
            'training_stats': {
                'avg_tss': round(float(records.avg_tss), 1) if records.avg_tss else None,
                'max_tss': round(float(records.max_tss), 1) if records.max_tss else None,
                'avg_intensity_factor': round(float(records.avg_if), 3) if records.avg_if else None,
                'total_activities_analyzed': records.total_activities
            }
        }
    
    def format_pace(self, time_seconds, distance_km):
        """Formater l'allure en min/km"""
        if not time_seconds or distance_km <= 0:
            return None
            
        # ✅ CORRECTION : Conversion en float
        pace_seconds_per_km = float(time_seconds) / float(distance_km)
        minutes = int(pace_seconds_per_km // 60)
        seconds = int(pace_seconds_per_km % 60)
        
        return f"{minutes}:{seconds:02d}/km"
    
    def get_training_load_analysis(self, athlete_id, days=30):
        """
        Analyse de la charge d'entraînement sur une période
        """
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Récupérer les activités avec métriques personnalisées
        activities = db.session.query(ActivitySummary, ActivityCustomMetrics)\
            .join(ActivityCustomMetrics, ActivitySummary.id == ActivityCustomMetrics.activity_id)\
            .filter(ActivitySummary.athlete_id == athlete_id)\
            .filter(ActivitySummary.start_date_local >= cutoff_date)\
            .order_by(ActivitySummary.start_date_local.desc()).all()
        
        if not activities:
            return None
        
        # Calculs agrégés avec conversions float
        total_tss = sum(float(cm.custom_tss or 0) for _, cm in activities if cm.custom_tss)
        avg_tss = total_tss / len(activities) if activities else 0
        max_tss = max((float(cm.custom_tss or 0) for _, cm in activities if cm.custom_tss), default=0)
        
        # ✅ CORRECTION : Gestion des divisions par zéro et conversions float
        intensity_factors = [float(cm.intensity_factor) for _, cm in activities if cm.intensity_factor]
        avg_if = sum(intensity_factors) / len(intensity_factors) if intensity_factors else 0
        
        # Classification par zones d'intensité
        zones = {'recovery': 0, 'endurance': 0, 'tempo': 0, 'threshold': 0, 'threshold_plus': 0}
        for _, cm in activities:
            if cm.intensity_factor:
                if_val = float(cm.intensity_factor)
                if if_val >= 1.05:
                    zones['threshold_plus'] += 1
                elif if_val >= 0.95:
                    zones['threshold'] += 1
                elif if_val >= 0.85:
                    zones['tempo'] += 1
                elif if_val >= 0.70:
                    zones['endurance'] += 1
                else:
                    zones['recovery'] += 1
        
        # TSS par semaine pour analyser la progression
        weekly_tss = {}
        for activity, cm in activities:
            if cm.custom_tss:
                week_key = activity.start_date_local.strftime('%Y-W%U')
                if week_key not in weekly_tss:
                    weekly_tss[week_key] = 0
                weekly_tss[week_key] += float(cm.custom_tss)
        
        return {
            'period_days': days,
            'total_activities': len(activities),
            'training_load': {
                'total_tss': round(total_tss, 1),
                'avg_tss_per_activity': round(avg_tss, 1),
                'max_tss_single': round(max_tss, 1),
                'avg_weekly_tss': round(sum(weekly_tss.values()) / len(weekly_tss), 1) if weekly_tss else 0
            },
            'intensity_distribution': {
                'avg_intensity_factor': round(avg_if, 3),
                'zones_count': zones,
                'zones_percentage': {
                    zone: round((count / len(activities)) * 100, 1) 
                    for zone, count in zones.items()
                }
            },
            'weekly_progression': [
                {'week': week, 'tss': round(tss, 1)} 
                for week, tss in sorted(weekly_tss.items())
            ]
        }
    
    def compare_with_strava_metrics(self, athlete_id, limit=20):
        """
        Comparer les TSS personnalisés avec les TSS Strava
        """
        # Récupérer activités avec les deux métriques
        comparisons = db.session.query(
            ActivitySummary, ActivityStravaMetrics, ActivityCustomMetrics
        ).join(
            ActivityStravaMetrics, ActivitySummary.id == ActivityStravaMetrics.activity_id
        ).join(
            ActivityCustomMetrics, ActivitySummary.id == ActivityCustomMetrics.activity_id
        ).filter(
            ActivitySummary.athlete_id == athlete_id
        ).filter(
            ActivityStravaMetrics.suffer_score.isnot(None)
        ).filter(
            ActivityCustomMetrics.custom_tss.isnot(None)
        ).order_by(
            ActivitySummary.start_date_local.desc()
        ).limit(limit).all()
        
        if not comparisons:
            return None
        
        results = []
        total_strava_tss = 0
        total_custom_tss = 0
        
        for activity, strava_metrics, custom_metrics in comparisons:
            strava_tss = float(strava_metrics.suffer_score)
            custom_tss = float(custom_metrics.custom_tss)
            difference = custom_tss - strava_tss
            
            total_strava_tss += strava_tss
            total_custom_tss += custom_tss
            
            results.append({
                'activity_name': activity.name,
                'date': activity.start_date_local.strftime('%Y-%m-%d'),
                'type': activity.type,
                'strava_tss': round(strava_tss, 1),
                'custom_tss': round(custom_tss, 1),
                'difference': round(difference, 1),
                'percentage_diff': round((difference / strava_tss) * 100, 1),
                'normalized_power': float(strava_metrics.weighted_average_watts) if strava_metrics.weighted_average_watts else None,
                'intensity_factor': float(custom_metrics.intensity_factor) if custom_metrics.intensity_factor else None
            })
        
        # Statistiques globales
        avg_strava = total_strava_tss / len(comparisons)
        avg_custom = total_custom_tss / len(comparisons)
        avg_difference = avg_custom - avg_strava
        
        return {
            'summary': {
                'activities_compared': len(comparisons),
                'avg_strava_tss': round(avg_strava, 1),
                'avg_custom_tss': round(avg_custom, 1),
                'avg_difference': round(avg_difference, 1),
                'avg_percentage_diff': round((avg_difference / avg_strava) * 100, 1),
                'user_ftp': custom_metrics.user_ftp if comparisons else None
            },
            'comparisons': results
        }
    
    def detect_ftp_tests(self, athlete_id, months=6):
        """
        Détecter les potentiels tests FTP dans les activités
        """
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=months * 30)
        
        # Rechercher activités de 20-30min avec IF élevé
        potential_tests = db.session.query(
            ActivitySummary, ActivityCustomMetrics
        ).join(
            ActivityCustomMetrics, ActivitySummary.id == ActivityCustomMetrics.activity_id
        ).filter(
            ActivitySummary.athlete_id == athlete_id
        ).filter(
            ActivitySummary.start_date_local >= cutoff_date
        ).filter(
            ActivitySummary.moving_time_seconds.between(1200, 1800)  # 20-30min
        ).filter(
            ActivityCustomMetrics.intensity_factor >= 0.95  # IF élevé
        ).order_by(
            ActivityCustomMetrics.intensity_factor.desc()
        ).limit(10).all()
        
        ftp_tests = []
        for activity, custom_metrics in potential_tests:
            estimated_ftp = None
            if custom_metrics.best_20min_power:
                estimated_ftp = int(float(custom_metrics.best_20min_power) * 0.95)
            
            ftp_tests.append({
                'activity_name': activity.name,
                'date': activity.start_date_local.strftime('%Y-%m-%d'),
                'duration_minutes': round(activity.moving_time_seconds / 60, 1),
                'intensity_factor': float(custom_metrics.intensity_factor),
                'estimated_20min_power': custom_metrics.best_20min_power,
                'estimated_ftp': estimated_ftp,
                'current_ftp': custom_metrics.user_ftp,
                'ftp_improvement': estimated_ftp - custom_metrics.user_ftp if estimated_ftp else None
            })
        
        return ftp_tests
    
    def get_power_curve_data(self, athlete_id):
        """
        Construire une courbe de puissance basée sur les records
        """
        records = db.session.query(
            ActivityCustomMetrics.best_1min_power,
            ActivityCustomMetrics.best_5min_power,
            ActivityCustomMetrics.best_20min_power
        ).filter_by(athlete_id=athlete_id)\
         .filter(ActivityCustomMetrics.best_1min_power.isnot(None)).all()
        
        if not records:
            return None
        
        # Extraire les meilleures valeurs
        best_1min = max((r.best_1min_power for r in records if r.best_1min_power), default=0)
        best_5min = max((r.best_5min_power for r in records if r.best_5min_power), default=0)
        best_20min = max((r.best_20min_power for r in records if r.best_20min_power), default=0)
        
        # Points de la courbe de puissance
        power_curve = [
            {'duration_seconds': 60, 'power': best_1min},
            {'duration_seconds': 300, 'power': best_5min},
            {'duration_seconds': 1200, 'power': best_20min}
        ]
        
        # Estimation FTP
        estimated_ftp = int(float(best_20min) * 0.95) if best_20min else None
        
        return {
            'power_curve': power_curve,
            'estimated_ftp': estimated_ftp,
            'peak_power_1min': best_1min,
            'peak_power_5min': best_5min,
            'peak_power_20min': best_20min
        }
    
    def analyze_training_patterns(self, athlete_id, days=90):
        """
        Analyser les patterns d'entraînement
        """
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        activities = db.session.query(ActivitySummary, ActivityCustomMetrics)\
            .join(ActivityCustomMetrics, ActivitySummary.id == ActivityCustomMetrics.activity_id)\
            .filter(ActivitySummary.athlete_id == athlete_id)\
            .filter(ActivitySummary.start_date_local >= cutoff_date).all()
        
        if not activities:
            return None
        
        # Analyse par jour de la semaine
        day_patterns = {}
        for activity, cm in activities:
            day_name = activity.day_name
            if day_name not in day_patterns:
                day_patterns[day_name] = {'count': 0, 'total_tss': 0, 'total_if': 0}
            
            day_patterns[day_name]['count'] += 1
            if cm.custom_tss:
                day_patterns[day_name]['total_tss'] += float(cm.custom_tss)
            if cm.intensity_factor:
                day_patterns[day_name]['total_if'] += float(cm.intensity_factor)
        
        # Calculer moyennes
        for day in day_patterns:
            count = day_patterns[day]['count']
            day_patterns[day]['avg_tss'] = round(day_patterns[day]['total_tss'] / count, 1) if count > 0 else 0
            day_patterns[day]['avg_if'] = round(day_patterns[day]['total_if'] / count, 3) if count > 0 else 0
        
        # Analyse par type d'activité
        type_patterns = {}
        for activity, cm in activities:
            activity_type = activity.type
            if activity_type not in type_patterns:
                type_patterns[activity_type] = {'count': 0, 'total_tss': 0, 'total_distance': 0}
            
            type_patterns[activity_type]['count'] += 1
            if cm.custom_tss:
                type_patterns[activity_type]['total_tss'] += float(cm.custom_tss)
            if activity.distance_km:
                type_patterns[activity_type]['total_distance'] += float(activity.distance_km)
        
        return {
            'analysis_period_days': days,
            'total_activities': len(activities),
            'day_of_week_patterns': day_patterns,
            'activity_type_patterns': type_patterns,
            'weekly_avg_activities': round(len(activities) / (days / 7), 1),
            'consistency_score': self.calculate_consistency_score(activities)
        }
    
    def calculate_consistency_score(self, activities):
        """
        Calculer un score de régularité d'entraînement (0-100)
        """
        if not activities:
            return 0
        
        # Analyser la distribution des activités par semaine
        weekly_counts = {}
        for activity, _ in activities:
            week_key = activity.start_date_local.strftime('%Y-W%U')
            weekly_counts[week_key] = weekly_counts.get(week_key, 0) + 1
        
        if len(weekly_counts) < 2:
            return 50  # Score moyen si pas assez de données
        
        # Calculer la variance des activités par semaine
        weekly_values = list(weekly_counts.values())
        mean_weekly = sum(weekly_values) / len(weekly_values)
        variance = sum((x - mean_weekly) ** 2 for x in weekly_values) / len(weekly_values)
        
        # Score basé sur la régularité (moins de variance = meilleur score)
        consistency_score = max(0, 100 - (variance * 10))
        
        return round(min(consistency_score, 100), 1)
    
    def get_activity_recommendations(self, athlete_id, recent_days=14):
        """
        Recommandations d'entraînement basées sur l'analyse récente
        """
        analysis = self.get_training_load_analysis(athlete_id, recent_days)
        
        if not analysis:
            return {
                'recommendations': ['Commencer par synchroniser vos activités avec calculs personnalisés'],
                'focus_areas': [],
                'next_workout_suggestion': None
            }
        
        recommendations = []
        focus_areas = []
        
        # Analyse de la charge récente
        avg_if = analysis['intensity_distribution']['avg_intensity_factor']
        total_tss = analysis['training_load']['total_tss']
        
        if avg_if < 0.70:
            recommendations.append("Augmenter l'intensité moyenne des entraînements")
            focus_areas.append("Inclure plus de travail en zones 3-4")
        elif avg_if > 0.90:
            recommendations.append("Inclure plus de récupération active")
            focus_areas.append("Sessions en zone 1-2 pour récupération")
        
        if total_tss < 200:
            recommendations.append("Augmenter le volume d'entraînement")
            focus_areas.append("Ajouter des sessions longues en endurance")
        elif total_tss > 500:
            recommendations.append("Prévoir une semaine de récupération")
            focus_areas.append("Réduire l'intensité et le volume")
        
        # Suggestion de prochaine séance
        next_workout = self.suggest_next_workout(analysis)
        
        return {
            'analysis_period': f"{recent_days} derniers jours",
            'recommendations': recommendations,
            'focus_areas': focus_areas,
            'next_workout_suggestion': next_workout,
            'current_form': self.assess_current_form(analysis)
        }
    
    def suggest_next_workout(self, analysis):
        """
        Suggérer le prochain entraînement basé sur l'analyse récente
        """
        avg_if = analysis['intensity_distribution']['avg_intensity_factor']
        zones = analysis['intensity_distribution']['zones_count']
        
        # Logique simple de suggestion
        if zones.get('recovery', 0) > zones.get('threshold', 0) * 2:
            return {
                'type': 'Entraînement d\'intensité',
                'target_if': '0.85-0.95',
                'duration': '60-90 minutes',
                'description': 'Session tempo ou seuil pour augmenter l\'intensité'
            }
        elif zones.get('threshold_plus', 0) > 2:
            return {
                'type': 'Récupération active',
                'target_if': '< 0.70',
                'duration': '45-60 minutes',
                'description': 'Session facile pour récupération'
            }
        else:
            return {
                'type': 'Entraînement équilibré',
                'target_if': '0.75-0.85',
                'duration': '75-90 minutes',
                'description': 'Session endurance avec quelques efforts'
            }
    
    def assess_current_form(self, analysis):
        """
        Évaluer la forme actuelle basée sur l'analyse
        """
        total_tss = analysis['training_load']['total_tss']
        avg_if = analysis['intensity_distribution']['avg_intensity_factor']
        
        if total_tss > 400 and avg_if > 0.80:
            return "Excellente forme - maintenir le niveau"
        elif total_tss > 300 and avg_if > 0.75:
            return "Bonne forme - possibilité d'augmenter légèrement"
        elif total_tss < 200 or avg_if < 0.65:
            return "Forme à développer - augmenter progressivement"
        else:
            return "Forme modérée - continuer la progression"