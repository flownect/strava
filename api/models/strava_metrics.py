from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from models.database import db

class ActivityStravaMetrics(db.Model):
    """
    Métriques natives Strava enrichies - Phase 1
    Stocke toutes les données avancées directement disponibles dans l'API Strava
    sans calculs supplémentaires
    """
    __tablename__ = 'activity_strava_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    activity_id = db.Column(db.Integer, db.ForeignKey('activity_summary.id'), nullable=False)
    
    # 💪 Données de puissance natives Strava
    average_watts = db.Column(db.Numeric(6, 1))                 # Puissance moyenne
    weighted_average_watts = db.Column(db.Numeric(6, 1))        # Normalized Power Strava
    max_watts = db.Column(db.Numeric(6, 1))                     # Puissance max
    device_watts = db.Column(db.Boolean, default=False)         # Capteur puissance réel
    
    # ❤️ Données fréquence cardiaque natives Strava  
    average_heartrate = db.Column(db.Numeric(5, 2))            # FC moyenne
    max_heartrate = db.Column(db.Numeric(5, 2))                # FC max
    has_heartrate = db.Column(db.Boolean, default=False)        # Capteur FC présent
    
    # 🎯 Métriques d'effort Strava
    suffer_score = db.Column(db.Numeric(6, 1))                 # TSS équivalent Strava
    perceived_exertion = db.Column(db.Integer)                 # RPE 1-10
    
    # 🚴‍♂️ Données vélo spécifiques
    average_cadence = db.Column(db.Numeric(5, 2))              # Cadence moyenne
    average_temp = db.Column(db.Numeric(4, 1))                 # Température moyenne
    trainer = db.Column(db.Boolean, default=False)             # Home trainer
    commute = db.Column(db.Boolean, default=False)             # Trajet domicile-travail
    
    # 🏃‍♂️ Données course spécifiques  
    average_speed_ms = db.Column(db.Numeric(8, 4))             # Vitesse moyenne (m/s)
    max_speed_ms = db.Column(db.Numeric(8, 4))                 # Vitesse max (m/s)
    
    # 📍 Métadonnées
    gear_id = db.Column(db.String(50))                         # ID équipement Strava
    external_id = db.Column(db.String(100))                    # ID device externe
    upload_id = db.Column(db.BigInteger)                       # ID upload Strava
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    activity = db.relationship('ActivitySummary', backref='strava_metrics')
    
    def to_dict(self):
        """Convertir en dictionnaire pour JSON API"""
        return {
            'id': self.id,
            'activity_id': self.activity_id,
            
            # Données de puissance
            'average_watts': float(self.average_watts) if self.average_watts else None,
            'weighted_average_watts': float(self.weighted_average_watts) if self.weighted_average_watts else None,
            'max_watts': float(self.max_watts) if self.max_watts else None,
            'device_watts': self.device_watts,
            'power_source': 'power_meter' if self.device_watts else ('estimated' if self.average_watts else 'no_power'),
            
            # Données fréquence cardiaque
            'average_heartrate': float(self.average_heartrate) if self.average_heartrate else None,
            'max_heartrate': float(self.max_heartrate) if self.max_heartrate else None,
            'has_heartrate': self.has_heartrate,
            
            # Métriques d'effort
            'suffer_score': float(self.suffer_score) if self.suffer_score else None,
            'effort_level': self.get_effort_level(),
            'perceived_exertion': self.perceived_exertion,
            
            # Données contextuelles
            'average_cadence': float(self.average_cadence) if self.average_cadence else None,
            'average_temp': float(self.average_temp) if self.average_temp else None,
            'trainer': self.trainer,
            'commute': self.commute,
            'activity_context': self.get_activity_context(),
            
            # Vitesse
            'average_speed_ms': float(self.average_speed_ms) if self.average_speed_ms else None,
            'max_speed_ms': float(self.max_speed_ms) if self.max_speed_ms else None,
            'average_speed_kmh': float(self.average_speed_ms * 3.6) if self.average_speed_ms else None,
            
            # Métadonnées
            'gear_id': self.gear_id,
            'external_id': self.external_id,
            'upload_id': self.upload_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def get_effort_level(self):
        """Classifier le niveau d'effort basé sur le suffer score"""
        if not self.suffer_score:
            return 'unknown'
        
        score = float(self.suffer_score)
        if score >= 150:
            return 'very_hard'
        elif score >= 100:
            return 'hard'
        elif score >= 50:
            return 'moderate'
        else:
            return 'easy'
    
    def get_activity_context(self):
        """Déterminer le contexte de l'activité"""
        if self.trainer:
            return 'indoor'
        elif self.commute:
            return 'commute'
        else:
            return 'outdoor'
    
    def get_power_metrics_summary(self):
        """Résumé des métriques de puissance"""
        if not self.average_watts:
            return None
            
        return {
            'has_power_data': True,
            'is_real_power_meter': self.device_watts,
            'average_watts': float(self.average_watts),
            'normalized_power': float(self.weighted_average_watts) if self.weighted_average_watts else None,
            'max_watts': float(self.max_watts) if self.max_watts else None,
            'variability_index': self.calculate_variability_index(),
            'power_quality': 'excellent' if self.device_watts else 'estimated'
        }
    
    def get_heartrate_metrics_summary(self):
        """Résumé des métriques de fréquence cardiaque"""
        if not self.has_heartrate or not self.average_heartrate:
            return None
            
        return {
            'has_heartrate_data': True,
            'average_heartrate': float(self.average_heartrate),
            'max_heartrate': float(self.max_heartrate) if self.max_heartrate else None,
            'hr_reserve_used': self.calculate_hr_reserve_percentage(),
            'cardiac_efficiency': self.calculate_cardiac_efficiency()
        }
    
    def calculate_variability_index(self):
        """Calculer l'index de variabilité (VI = NP / Average Power)"""
        if not self.weighted_average_watts or not self.average_watts:
            return None
        
        if float(self.average_watts) == 0:
            return None
            
        return round(float(self.weighted_average_watts) / float(self.average_watts), 3)
    
    def calculate_hr_reserve_percentage(self, max_hr_estimate=190):
        """Calculer le pourcentage de réserve cardiaque utilisée"""
        if not self.average_heartrate:
            return None
            
        # Estimation simple (peut être personnalisée plus tard)
        resting_hr = 60  # Valeur par défaut
        hr_reserve = max_hr_estimate - resting_hr
        hr_used = float(self.average_heartrate) - resting_hr
        
        return round((hr_used / hr_reserve) * 100, 1) if hr_reserve > 0 else None
    
    def calculate_cardiac_efficiency(self):
        """Calculer l'efficacité cardiaque (Power/HR ratio si disponible)"""
        if not self.weighted_average_watts or not self.average_heartrate:
            return None
            
        if float(self.average_heartrate) == 0:
            return None
            
        return round(float(self.weighted_average_watts) / float(self.average_heartrate), 2)
    
    def is_quality_workout(self):
        """Déterminer si c'est un entraînement de qualité"""
        # Critères pour un entraînement de qualité
        quality_indicators = 0
        
        # Effort soutenu
        if self.suffer_score and float(self.suffer_score) >= 80:
            quality_indicators += 1
            
        # Puissance élevée (si capteur réel)
        if self.device_watts and self.weighted_average_watts and float(self.weighted_average_watts) >= 200:
            quality_indicators += 1
            
        # FC élevée
        if self.has_heartrate and self.average_heartrate and float(self.average_heartrate) >= 150:
            quality_indicators += 1
            
        # Au moins 2 critères sur 3
        return quality_indicators >= 2
    
    def get_training_zones_estimate(self, ftp=250, lthr=180):
        """Estimation rapide des zones d'entraînement"""
        zones = {
            'power_zones': None,
            'hr_zones': None
        }
        
        # Zones de puissance approximatives
        if self.weighted_average_watts:
            power = float(self.weighted_average_watts)
            intensity = power / ftp
            
            if intensity >= 1.05:
                zone = 'Zone 5+ (VO2 Max+)'
            elif intensity >= 0.91:
                zone = 'Zone 4 (Threshold)'
            elif intensity >= 0.76:
                zone = 'Zone 3 (Tempo)'
            elif intensity >= 0.56:
                zone = 'Zone 2 (Endurance)'
            else:
                zone = 'Zone 1 (Recovery)'
                
            zones['power_zones'] = {
                'primary_zone': zone,
                'intensity_factor': round(intensity, 3),
                'watts': power
            }
        
        # Zones FC approximatives
        if self.average_heartrate:
            hr = float(self.average_heartrate)
            hr_percentage = hr / lthr
            
            if hr_percentage >= 1.06:
                hr_zone = 'Zone 5 (Anaerobic)'
            elif hr_percentage >= 0.94:
                hr_zone = 'Zone 4 (Threshold)'
            elif hr_percentage >= 0.84:
                hr_zone = 'Zone 3 (Aerobic)'
            elif hr_percentage >= 0.70:
                hr_zone = 'Zone 2 (Aerobic Base)'
            else:
                hr_zone = 'Zone 1 (Recovery)'
                
            zones['hr_zones'] = {
                'primary_zone': hr_zone,
                'hr_percentage': round(hr_percentage * 100, 1),
                'bpm': hr
            }
        
        return zones
    
    @classmethod
    def get_athlete_power_summary(cls, athlete_id, days=30):
        """Résumé puissance pour un athlète sur une période"""
        from sqlalchemy import and_, func
        from models.database import ActivitySummary
        from datetime import timedelta, datetime
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = db.session.query(
            func.count(cls.id).label('total_activities'),
            func.count(cls.weighted_average_watts).label('power_activities'),
            func.avg(cls.weighted_average_watts).label('avg_normalized_power'),
            func.max(cls.weighted_average_watts).label('best_normalized_power'),
            func.avg(cls.suffer_score).label('avg_suffer_score'),
            func.sum(cls.suffer_score).label('total_training_load')
        ).join(ActivitySummary).filter(
            and_(
                ActivitySummary.athlete_id == athlete_id,
                ActivitySummary.start_date_local >= cutoff_date
            )
        ).first()
        
        return {
            'period_days': days,
            'total_activities': query.total_activities or 0,
            'power_activities': query.power_activities or 0,
            'avg_normalized_power': float(query.avg_normalized_power) if query.avg_normalized_power else None,
            'best_normalized_power': float(query.best_normalized_power) if query.best_normalized_power else None,
            'avg_suffer_score': float(query.avg_suffer_score) if query.avg_suffer_score else None,
            'total_training_load': float(query.total_training_load) if query.total_training_load else None,
            'power_coverage': round((query.power_activities / query.total_activities) * 100, 1) if query.total_activities > 0 else 0
        }
    
    def __repr__(self):
        return f'<ActivityStravaMetrics {self.id}: Activity {self.activity_id}, Power: {self.weighted_average_watts}W, Suffer: {self.suffer_score}>'