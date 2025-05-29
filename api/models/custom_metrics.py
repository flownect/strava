from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from models.database import db

class ActivityCustomMetrics(db.Model):
    """
    Calculs personnalisés basés sur données Strava existantes + FTP utilisateur
    Phase 2 : Métriques précises avec paramètres personnels
    """
    __tablename__ = 'activity_custom_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    activity_id = db.Column(db.Integer, db.ForeignKey('activity_summary.id'), nullable=False)
    athlete_id = db.Column(db.Integer, nullable=False)
    
    # Paramètres utilisés pour les calculs
    user_ftp = db.Column(db.Integer, nullable=False)
    user_weight = db.Column(db.Numeric(5, 2))
    
    # TSS et intensité personnalisés
    custom_tss = db.Column(db.Numeric(8, 2))
    intensity_factor = db.Column(db.Numeric(5, 4))
    training_load = db.Column(db.Numeric(8, 2))
    
    # Records de puissance estimés
    best_1min_power = db.Column(db.Integer)
    best_5min_power = db.Column(db.Integer)
    best_20min_power = db.Column(db.Integer)
    
    # Records de distance (temps en secondes)
    best_1km_time = db.Column(db.Integer)
    best_5km_time = db.Column(db.Integer)
    best_10km_time = db.Column(db.Integer)
    best_half_marathon_time = db.Column(db.Integer)
    best_marathon_time = db.Column(db.Integer)
    
    # Métadonnées
    calculated_at = db.Column(db.DateTime, default=datetime.utcnow)
    calculation_method = db.Column(db.String(50), default='strava_based')
    
    # Relations
    activity = db.relationship('ActivitySummary', backref='custom_metrics')
    
    def to_dict(self):
        """Convertir en dictionnaire pour JSON API"""
        return {
            'id': self.id,
            'activity_id': self.activity_id,
            'athlete_id': self.athlete_id,
            
            # Paramètres
            'user_ftp': self.user_ftp,
            'user_weight': float(self.user_weight) if self.user_weight else None,
            
            # Calculs personnalisés
            'custom_tss': float(self.custom_tss) if self.custom_tss else None,
            'intensity_factor': float(self.intensity_factor) if self.intensity_factor else None,
            'training_load': float(self.training_load) if self.training_load else None,
            'power_zone': self.get_power_zone(),
            
            # Records de puissance
            'best_1min_power': self.best_1min_power,
            'best_5min_power': self.best_5min_power,
            'best_20min_power': self.best_20min_power,
            
            # Records de distance
            'best_1km_time': self.best_1km_time,
            'best_1km_pace': self.format_pace(self.best_1km_time, 1) if self.best_1km_time else None,
            'best_5km_time': self.best_5km_time,
            'best_5km_pace': self.format_pace(self.best_5km_time, 5) if self.best_5km_time else None,
            'best_10km_time': self.best_10km_time,
            'best_10km_pace': self.format_pace(self.best_10km_time, 10) if self.best_10km_time else None,
            'best_half_marathon_time': self.best_half_marathon_time,
            'best_half_marathon_pace': self.format_pace(self.best_half_marathon_time, 21.1) if self.best_half_marathon_time else None,
            'best_marathon_time': self.best_marathon_time,
            'best_marathon_pace': self.format_pace(self.best_marathon_time, 42.2) if self.best_marathon_time else None,
            
            # Métadonnées
            'calculated_at': self.calculated_at.isoformat() if self.calculated_at else None,
            'calculation_method': self.calculation_method
        }
    
    def get_power_zone(self):
        """Déterminer la zone de puissance basée sur l'IF"""
        if not self.intensity_factor:
            return 'unknown'
        
        if_value = float(self.intensity_factor)
        if if_value >= 1.05:
            return 'threshold_plus'  # Zone 5+ (VO2 Max+)
        elif if_value >= 0.95:
            return 'threshold'       # Zone 4 (Seuil)
        elif if_value >= 0.85:
            return 'tempo'          # Zone 3 (Tempo)
        elif if_value >= 0.70:
            return 'endurance'      # Zone 2 (Endurance)
        else:
            return 'recovery'       # Zone 1 (Récupération)
    
    def format_pace(self, time_seconds, distance_km):
        """Formater l'allure en min/km"""
        if not time_seconds or distance_km <= 0:
            return None
            
        pace_seconds_per_km = time_seconds / distance_km
        minutes = int(pace_seconds_per_km // 60)
        seconds = int(pace_seconds_per_km % 60)
        
        return f"{minutes}:{seconds:02d}/km"
    
    def get_comparison_vs_strava(self, strava_suffer_score):
        """Comparaison TSS personnel vs Strava"""
        if not self.custom_tss or not strava_suffer_score:
            return None
            
        difference = float(self.custom_tss) - float(strava_suffer_score)
        percentage_diff = (difference / float(strava_suffer_score)) * 100
        
        return {
            'strava_tss': float(strava_suffer_score),
            'custom_tss': float(self.custom_tss),
            'difference': round(difference, 1),
            'percentage_difference': round(percentage_diff, 1),
            'explanation': self.explain_tss_difference(difference)
        }
    
    def explain_tss_difference(self, difference):
        """Explication de la différence TSS"""
        if abs(difference) < 5:
            return "TSS similaires - FTP estimé par Strava proche du vôtre"
        elif difference > 0:
            return f"Votre TSS +{difference:.1f} - Strava sous-estime votre effort (FTP Strava > {self.user_ftp}W)"
        else:
            return f"Votre TSS {difference:.1f} - Strava sur-estime votre effort (FTP Strava < {self.user_ftp}W)"
    
    def get_performance_summary(self):
        """Résumé de performance pour cette activité"""
        summary = {
            'tss_info': {
                'custom_tss': float(self.custom_tss) if self.custom_tss else None,
                'intensity_factor': float(self.intensity_factor) if self.intensity_factor else None,
                'power_zone': self.get_power_zone(),
                'ftp_used': self.user_ftp
            },
            'power_records': {},
            'distance_records': {}
        }
        
        # Records de puissance
        if self.best_1min_power or self.best_5min_power or self.best_20min_power:
            summary['power_records'] = {
                'best_1min_power': self.best_1min_power,
                'best_5min_power': self.best_5min_power,
                'best_20min_power': self.best_20min_power,
                'estimated_ftp': self.best_20min_power * 0.95 if self.best_20min_power else None
            }
        
        # Records de distance
        distance_records = {}
        if self.best_1km_time:
            distance_records['1km'] = {
                'time_seconds': self.best_1km_time,
                'pace': self.format_pace(self.best_1km_time, 1)
            }
        if self.best_5km_time:
            distance_records['5km'] = {
                'time_seconds': self.best_5km_time,
                'pace': self.format_pace(self.best_5km_time, 5)
            }
        if self.best_10km_time:
            distance_records['10km'] = {
                'time_seconds': self.best_10km_time,
                'pace': self.format_pace(self.best_10km_time, 10)
            }
        
        if distance_records:
            summary['distance_records'] = distance_records
        
        return summary


class AthleteSettings(db.Model):
    """
    Paramètres personnels de l'athlète pour calculs précis
    """
    __tablename__ = 'athlete_settings'
    
    athlete_id = db.Column(db.Integer, primary_key=True)
    
    # Seuils physiologiques
    current_ftp = db.Column(db.Integer, nullable=False)
    max_heartrate = db.Column(db.Integer)
    resting_heartrate = db.Column(db.Integer)
    weight = db.Column(db.Numeric(5, 2))
    
    # Paramètres de calcul
    auto_update_ftp = db.Column(db.Boolean, default=True)
    ftp_test_detection = db.Column(db.Boolean, default=True)
    
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'athlete_id': self.athlete_id,
            'current_ftp': self.current_ftp,
            'max_heartrate': self.max_heartrate,
            'resting_heartrate': self.resting_heartrate,
            'weight': float(self.weight) if self.weight else None,
            'auto_update_ftp': self.auto_update_ftp,
            'ftp_test_detection': self.ftp_test_detection,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_zones_configuration(self):
        """Configuration des zones basées sur les seuils personnels"""
        zones_config = {
            'power_zones': {
                'ftp_base': self.current_ftp,
                'zone_1_recovery': f"< {int(self.current_ftp * 0.55)}W (< 55% FTP)",
                'zone_2_endurance': f"{int(self.current_ftp * 0.55)}-{int(self.current_ftp * 0.75)}W (55-75% FTP)",
                'zone_3_tempo': f"{int(self.current_ftp * 0.75)}-{int(self.current_ftp * 0.90)}W (75-90% FTP)",
                'zone_4_threshold': f"{int(self.current_ftp * 0.90)}-{int(self.current_ftp * 1.05)}W (90-105% FTP)",
                'zone_5_vo2max': f"> {int(self.current_ftp * 1.05)}W (> 105% FTP)"
            }
        }
        
        if self.max_heartrate:
            zones_config['heart_rate_zones'] = {
                'max_hr_base': self.max_heartrate,
                'zone_1_recovery': f"< {int(self.max_heartrate * 0.68)} bpm (< 68% FC max)",
                'zone_2_aerobic': f"{int(self.max_heartrate * 0.68)}-{int(self.max_heartrate * 0.83)} bpm (68-83% FC max)",
                'zone_3_aerobic': f"{int(self.max_heartrate * 0.83)}-{int(self.max_heartrate * 0.94)} bpm (83-94% FC max)",
                'zone_4_threshold': f"{int(self.max_heartrate * 0.94)}-{int(self.max_heartrate * 1.05)} bpm (94-105% FC max)",
                'zone_5_anaerobic': f"> {int(self.max_heartrate * 1.05)} bpm (> 105% FC max)"
            }
        
        return zones_config
    
    def estimate_ftp_from_performances(self, best_20min_power):
        """Estimer un nouveau FTP basé sur performances récentes"""
        if not best_20min_power:
            return self.current_ftp
            
        # FTP estimé = 95% de la puissance 20min
        estimated_ftp = int(best_20min_power * 0.95)
        
        # Ne proposer une mise à jour que si la différence est significative (> 5W)
        if abs(estimated_ftp - self.current_ftp) > 5:
            return {
                'current_ftp': self.current_ftp,
                'estimated_ftp': estimated_ftp,
                'difference': estimated_ftp - self.current_ftp,
                'recommendation': 'update' if abs(estimated_ftp - self.current_ftp) > 10 else 'consider',
                'based_on': f"Meilleure puissance 20min: {best_20min_power}W"
            }
        
        return None
    
    @classmethod
    def get_or_create_for_athlete(cls, athlete_id, default_ftp=245):
        """Récupérer ou créer les paramètres pour un athlète"""
        settings = cls.query.get(athlete_id)
        if not settings:
            settings = cls(
                athlete_id=athlete_id,
                current_ftp=default_ftp
            )
            db.session.add(settings)
            db.session.commit()
        return settings
    
    def update_settings(self, **kwargs):
        """Mettre à jour les paramètres"""
        for key, value in kwargs.items():
            if hasattr(self, key) and value is not None:
                setattr(self, key, value)
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
        return self
    
    def get_training_recommendations(self, recent_avg_if=None, recent_total_tss=None):
        """Recommandations d'entraînement basées sur les performances récentes"""
        recommendations = {
            'ftp_status': 'current',
            'training_focus': [],
            'intensity_guidance': []
        }
        
        if recent_avg_if:
            if recent_avg_if < 0.70:
                recommendations['training_focus'].append("Augmenter l'intensité générale des entraînements")
                recommendations['intensity_guidance'].append("Viser IF 0.70-0.85 pour entraînements aérobies")
            elif recent_avg_if > 0.90:
                recommendations['training_focus'].append("Inclure plus de récupération active")
                recommendations['intensity_guidance'].append("Alterner avec sessions IF < 0.70")
        
        if recent_total_tss:
            if recent_total_tss < 200:  # TSS hebdomadaire faible
                recommendations['training_focus'].append("Augmenter le volume d'entraînement")
            elif recent_total_tss > 600:  # TSS hebdomadaire élevé
                recommendations['training_focus'].append("Prévoir semaine de récupération")
        
        return recommendations
    
    def __repr__(self):
        return f'<AthleteSettings {self.athlete_id}: FTP={self.current_ftp}W>'