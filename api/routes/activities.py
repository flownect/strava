from flask import Blueprint, request, jsonify, make_response
from models.database import db, ActivitySummary, Athlete
from services.strava_service import StravaService
import csv
import io

activities_bp = Blueprint('activities', __name__)

@activities_bp.route('/athlete/<int:athlete_id>')
def get_activities(athlete_id):
    """Récupérer les activités d'un athlète"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    activity_type = request.args.get('type')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    
    # Vérifier que l'athlète existe
    athlete = Athlete.query.get(athlete_id)
    if not athlete:
        return jsonify({'error': 'Athlete not found'}), 404
    
    query = ActivitySummary.query.filter_by(athlete_id=athlete_id)
    
    # Filtres
    if activity_type:
        query = query.filter(ActivitySummary.type == activity_type)
    
    if start_date:
        query = query.filter(ActivitySummary.start_date_local >= start_date)
    
    if end_date:
        query = query.filter(ActivitySummary.start_date_local <= end_date)
    
    if year:
        query = query.filter(ActivitySummary.year == year)
    
    if month:
        query = query.filter(ActivitySummary.month == month)
    
    # Pagination
    activities = query.order_by(ActivitySummary.start_date_local.desc())\
                     .paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'athlete': {
            'id': athlete.id,
            'name': f"{athlete.firstname} {athlete.lastname}"
        },
        'activities': [activity.to_dict() for activity in activities.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': activities.total,
            'pages': activities.pages,
            'has_next': activities.has_next,
            'has_prev': activities.has_prev
        },
        'filters_applied': {
            'type': activity_type,
            'start_date': start_date,
            'end_date': end_date,
            'year': year,
            'month': month
        }
    })

@activities_bp.route('/athlete/<int:athlete_id>/sync')
def sync_activities(athlete_id):
    """Déclencher une synchronisation manuelle"""
    athlete = Athlete.query.get(athlete_id)
    if not athlete:
        return jsonify({'error': 'Athlete not found'}), 404
    
    try:
        strava_service = StravaService()
        result = strava_service.sync_athlete_activities(athlete_id)
        return jsonify({
            'message': 'Synchronisation terminée',
            'result': result,
            'athlete': f"{athlete.firstname} {athlete.lastname}"
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@activities_bp.route('/athlete/<int:athlete_id>/types')
def get_activity_types(athlete_id):
    """Récupérer les types d'activités disponibles pour cet athlète"""
    athlete = Athlete.query.get(athlete_id)
    if not athlete:
        return jsonify({'error': 'Athlete not found'}), 404
    
    types = db.session.query(
        ActivitySummary.type,
        ActivitySummary.sport_type,
        db.func.count(ActivitySummary.id).label('count')
    ).filter_by(athlete_id=athlete_id)\
     .group_by(ActivitySummary.type, ActivitySummary.sport_type)\
     .order_by(db.func.count(ActivitySummary.id).desc())\
     .all()
    
    return jsonify({
        'athlete_id': athlete_id,
        'activity_types': [
            {
                'type': t.type,
                'sport_type': t.sport_type,
                'count': t.count
            }
            for t in types if t.type
        ]
    })

@activities_bp.route('/athlete/<int:athlete_id>/summary')
def get_athlete_summary(athlete_id):
    """Résumé rapide de l'athlète"""
    athlete = Athlete.query.get(athlete_id)
    if not athlete:
        return jsonify({'error': 'Athlete not found'}), 404
    
    # Statistiques globales
    total_stats = db.session.query(
        db.func.count(ActivitySummary.id).label('total_activities'),
        db.func.sum(ActivitySummary.distance_km).label('total_km'),
        db.func.sum(ActivitySummary.moving_time_hours).label('total_hours'),
        db.func.min(ActivitySummary.start_date_local).label('first_activity'),
        db.func.max(ActivitySummary.start_date_local).label('last_activity')
    ).filter_by(athlete_id=athlete_id).first()
    
    # Activité récente (30 derniers jours)
    from datetime import datetime, timedelta
    recent_date = datetime.now() - timedelta(days=30)
    
    recent_stats = db.session.query(
        db.func.count(ActivitySummary.id).label('recent_activities'),
        db.func.sum(ActivitySummary.distance_km).label('recent_km'),
        db.func.sum(ActivitySummary.moving_time_hours).label('recent_hours')
    ).filter(
        ActivitySummary.athlete_id == athlete_id,
        ActivitySummary.start_date_local >= recent_date
    ).first()
    
    return jsonify({
        'athlete': {
            'id': athlete.id,
            'name': f"{athlete.firstname} {athlete.lastname}",
            'username': athlete.username,
            'city': athlete.city,
            'country': athlete.country,
            'premium': athlete.premium
        },
        'total_stats': {
            'activities': total_stats.total_activities or 0,
            'distance_km': float(total_stats.total_km or 0),
            'hours': float(total_stats.total_hours or 0),
            'first_activity': total_stats.first_activity.isoformat() if total_stats.first_activity else None,
            'last_activity': total_stats.last_activity.isoformat() if total_stats.last_activity else None
        },
        'last_30_days': {
            'activities': recent_stats.recent_activities or 0,
            'distance_km': float(recent_stats.recent_km or 0),
            'hours': float(recent_stats.recent_hours or 0)
        }
    })

@activities_bp.route('/athlete/<int:athlete_id>/export')
def export_activities(athlete_id):
    """Exporter les activités en CSV"""
    athlete = Athlete.query.get(athlete_id)
    if not athlete:
        return jsonify({'error': 'Athlete not found'}), 404
    
    # Filtres optionnels
    year = request.args.get('year', type=int)
    activity_type = request.args.get('type')
    
    query = ActivitySummary.query.filter_by(athlete_id=athlete_id)
    
    if year:
        query = query.filter(ActivitySummary.year == year)
    
    if activity_type:
        query = query.filter(ActivitySummary.type == activity_type)
    
    activities = query.order_by(ActivitySummary.start_date_local.desc()).all()
    
    # Créer le CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # En-têtes
    writer.writerow([
        'Date', 'Nom', 'Type', 'Type Sport', 'Distance (km)', 'Temps (h)', 
        'Vitesse moyenne (km/h)', 'Dénivelé (m)', 'FC moyenne', 'FC max', 'Calories',
        'Jour semaine', 'Mois', 'Année'
    ])
    
    # Données
    for activity in activities:
        writer.writerow([
            activity.start_date_local.strftime('%Y-%m-%d %H:%M') if activity.start_date_local else '',
            activity.name or '',
            activity.type or '',
            activity.sport_type or '',
            float(activity.distance_km) if activity.distance_km else 0,
            float(activity.moving_time_hours) if activity.moving_time_hours else 0,
            round(float(activity.average_speed) * 3.6, 2) if activity.average_speed else '',  # m/s vers km/h
            float(activity.total_elevation_gain) if activity.total_elevation_gain else '',
            float(activity.average_heartrate) if activity.average_heartrate else '',
            activity.max_heartrate if activity.max_heartrate else '',
            float(activity.calories) if activity.calories else '',
            activity.day_name or '',
            activity.month_name or '',
            activity.year or ''
        ])
    
    # Préparer la réponse
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    
    filename = f'strava_activities_{athlete.firstname}_{athlete.lastname}'
    if year:
        filename += f'_{year}'
    if activity_type:
        filename += f'_{activity_type}'
    filename += '.csv'
    
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    
    return response

@activities_bp.route('/athlete/<int:athlete_id>/activity/<int:strava_id>')
def get_activity_detail(athlete_id, strava_id):
    """Récupérer les détails d'une activité spécifique"""
    activity = ActivitySummary.query.filter_by(
        athlete_id=athlete_id,
        strava_id=strava_id
    ).first()
    
    if not activity:
        return jsonify({'error': 'Activity not found'}), 404
    
    return jsonify({
        'activity': activity.to_dict(),
        'formatted': {
            'duration': f"{activity.moving_time_hours:.1f}h" if activity.moving_time_hours else "N/A",
            'pace_per_km': f"{60/activity.average_speed*3.6:.2f} min/km" if activity.average_speed and activity.type == 'Run' else None,
            'avg_speed_kmh': f"{activity.average_speed*3.6:.1f} km/h" if activity.average_speed else None
        }
    })