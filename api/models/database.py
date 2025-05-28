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
    
    # Relation avec les métriques Strava (sera disponible après import)
    # strava_metrics sera ajouté automatiquement par la relation dans ActivityStravaMetrics
    
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
            'year': self.year,
            'month': self.month,
            'day': self.day,
            'day_name': self.day_name,
            'month_name': self.month_name,
            'average_speed': float(self.average_speed) if self.average_speed else None,
            'total_elevation_gain': float(self.total_elevation_gain) if self.total_elevation_gain else None,
            'average_heartrate': float(self.average_heartrate) if self.average_heartrate else None,
            'calories': float(self.calories) if self.calories else None
        }