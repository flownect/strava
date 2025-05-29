from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Athlete(db.Model):
    __tablename__ = 'athletes'
    
    id = db.Column(db.Integer, primary_key=True)
    strava_id = db.Column(db.BigInteger, unique=True, nullable=False)
    username = db.Column(db.String(255))
    firstname = db.Column(db.String(255))
    lastname = db.Column(db.String(255))
    city = db.Column(db.String(255))
    state = db.Column(db.String(255))
    country = db.Column(db.String(255))
    sex = db.Column(db.String(1))
    premium = db.Column(db.Boolean, default=False)
    profile_medium = db.Column(db.String(500))
    profile = db.Column(db.String(500))
    
    # Tokens d'authentification
    access_token = db.Column(db.Text)
    refresh_token = db.Column(db.Text)
    token_expires_at = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    activities = db.relationship('ActivitySummary', backref='athlete', lazy=True)
    # settings relation will be added automatically by backref in AthleteSettings

class ActivitySummary(db.Model):
    __tablename__ = 'activity_summary'
    
    id = db.Column(db.Integer, primary_key=True)
    strava_id = db.Column(db.BigInteger, unique=True, nullable=False)
    athlete_id = db.Column(db.Integer, db.ForeignKey('athletes.id'), nullable=False)
    
    name = db.Column(db.String(255))
    type = db.Column(db.String(50))
    sport_type = db.Column(db.String(50))
    
    start_date = db.Column(db.DateTime, nullable=False)
    start_date_local = db.Column(db.DateTime, nullable=False)
    
    distance_km = db.Column(db.Numeric(8, 2), nullable=False)
    moving_time_seconds = db.Column(db.Integer, nullable=False)
    elapsed_time_seconds = db.Column(db.Integer, nullable=False)
    moving_time_hours = db.Column(db.Numeric(6, 2))
    elapsed_time_hours = db.Column(db.Numeric(6, 2))
    
    # Données temporelles pré-calculées
    year = db.Column(db.Integer)
    month = db.Column(db.Integer)
    day = db.Column(db.Integer)
    week = db.Column(db.Integer)
    day_of_week = db.Column(db.Integer)
    day_name = db.Column(db.String(10))
    month_name = db.Column(db.String(15))
    
    # Métriques supplémentaires
    average_speed = db.Column(db.Numeric(8, 4))
    max_speed = db.Column(db.Numeric(8, 4))
    total_elevation_gain = db.Column(db.Numeric(8, 2))
    average_heartrate = db.Column(db.Numeric(5, 2))
    max_heartrate = db.Column(db.Integer)
    calories = db.Column(db.Numeric(8, 2))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations avec métriques (seront disponibles après imports)
    # strava_metrics et custom_metrics sont ajoutés automatiquement par les relations
    
    def to_dict(self):
        return {
            'id': self.id,
            'strava_id': self.strava_id,
            'name': self.name,
            'type': self.type,
            'sport_type': self.sport_type,
            'start_date': self.start_date_local.isoformat() if self.start_date_local else None,
            'distance_km': float(self.distance_km) if self.distance_km else 0,
            'moving_time_hours': float(self.moving_time_hours) if self.moving_time_hours else 0,
            'moving_time_seconds': self.moving_time_seconds,
            'year': self.year,
            'month': self.month,
            'day': self.day,
            'week': self.week,
            'day_name': self.day_name,
            'month_name': self.month_name,
            'average_speed': float(self.average_speed) if self.average_speed else None,
            'max_speed': float(self.max_speed) if self.max_speed else None,
            'total_elevation_gain': float(self.total_elevation_gain) if self.total_elevation_gain else None,
            'average_heartrate': float(self.average_heartrate) if self.average_heartrate else None,
            'max_heartrate': self.max_heartrate,
            'calories': float(self.calories) if self.calories else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def get_duration_formatted(self):
        """Retourner la durée formatée en heures:minutes"""
        if not self.moving_time_seconds:
            return "0:00"
        
        hours = self.moving_time_seconds // 3600
        minutes = (self.moving_time_seconds % 3600) // 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}"
        else:
            return f"0:{minutes:02d}"
    
    def get_pace_per_km(self):
        """Calculer l'allure en min/km pour la course"""
        if not self.distance_km or not self.moving_time_seconds or self.distance_km <= 0:
            return None
        
        if self.type not in ['Run', 'Walk']:
            return None
        
        seconds_per_km = self.moving_time_seconds / float(self.distance_km)
        minutes = int(seconds_per_km // 60)
        seconds = int(seconds_per_km % 60)
        
        return f"{minutes}:{seconds:02d}/km"
    
    def get_speed_kmh(self):
        """Calculer la vitesse en km/h"""
        if not self.average_speed:
            return None
        
        # average_speed est en m/s, convertir en km/h
        return round(float(self.average_speed) * 3.6, 1)
    
    def is_recent(self, days=7):
        """Vérifier si l'activité est récente"""
        if not self.start_date_local:
            return False
        
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)
        return self.start_date_local >= cutoff
    
    def get_activity_summary(self):
        """Résumé rapide de l'activité"""
        summary = {
            'name': self.name,
            'type': self.type,
            'date': self.start_date_local.strftime('%Y-%m-%d') if self.start_date_local else None,
            'distance_km': float(self.distance_km) if self.distance_km else 0,
            'duration': self.get_duration_formatted(),
            'day_name': self.day_name
        }
        
        # Ajouter la vitesse selon le type
        if self.type in ['Run', 'Walk']:
            summary['pace'] = self.get_pace_per_km()
        else:
            summary['speed_kmh'] = self.get_speed_kmh()
        
        return summary
    
    def __repr__(self):
        return f'<ActivitySummary {self.id}: {self.name} ({self.type}) - {self.distance_km}km>'