from flask import Blueprint, jsonify, request
from models.database import db, Athlete, ActivitySummary
from models.strava_metrics import ActivityStravaMetrics
from services.strava_service import StravaService
from sqlalchemy import and_, func, desc
from datetime import datetime, timedelta

activities_bp = Blueprint('activities', __name__)

@activities_bp.route('/athlete/<int:athlete_id>')
def get_athlete_activities(athlete_id):
    """Récupérer les activités d'un athlète avec métriques Strava enrichies"""
    try:
        # Paramètres de requête
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 200)
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        activity_type = request.args.get('type')
        
        # Requête de base avec jointure métriques Strava
        query = db.session.query(ActivitySummary, ActivityStravaMetrics)\
            .outerjoin(ActivityStravaMetrics, ActivitySummary.id == ActivityStravaMetrics.activity_id)\
            .filter(ActivitySummary.athlete_id == athlete_id)
        
        # Filtres
        if year:
            query = query.filter(ActivitySummary.year == year)
        if month:
            query = query.filter(ActivitySummary.month == month)
        if activity_type:
            query = query.filter(ActivitySummary.type == activity_type)
        
        # Pagination
        activities = query.order_by(desc(ActivitySummary.start_date_local))\
            .offset((page - 1) * per_page)\
            .limit(per_page).all()
        
        # Total pour pagination
        total = query.count()
        
        # Formatage des résultats enrichis
        result = []
        for activity, strava_metrics in activities:
            activity_data = activity.to_dict()
            
            # Ajouter les métriques Strava si disponibles
            if strava_metrics:
                activity_data['strava_metrics'] = strava_metrics.to_dict()
            else:
                activity_data['strava_metrics'] = None
            
            result.append(activity_data)
        
        return jsonify({
            'activities': result,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@activities_bp.route('/athlete/<int:athlete_id>/sync')
def sync_athlete_activities(athlete_id):
    """Synchronisation enrichie des activités avec métriques Strava"""
    athlete = Athlete.query.get(athlete_id)
    if not athlete:
        return jsonify({'error': 'Athlete not found'}), 404
    
    try:
        strava_service = StravaService()
        result = strava_service.sync_athlete_activities(athlete_id)
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify({
            'message': 'Synchronisation enrichie terminée',
            'synchronized_activities': result['synchronized_activities'],
            'enriched_activities': result.get('enriched_activities', 0),
            'athlete': f"{athlete.firstname} {athlete.lastname}"
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@activities_bp.route('/athlete/<int:athlete_id>/summary')
def get_athlete_summary(athlete_id):
    """Résumé complet d'un athlète avec métriques avancées"""
    try:
        athlete = Athlete.query.get(athlete_id)
        if not athlete:
            return jsonify({'error': 'Athlete not found'}), 404
        
        # Statistiques de base
        total_activities = ActivitySummary.query.filter_by(athlete_id=athlete_id).count()
        activities_with_metrics = db.session.query(ActivitySummary)\
            .join(ActivityStravaMetrics, ActivitySummary.id == ActivityStravaMetrics.activity_id)\
            .filter(ActivitySummary.athlete_id == athlete_id).count()
        
        summary = {
            'athlete': {
                'id': athlete.id,
                'name': f"{athlete.firstname} {athlete.lastname}",
                'strava_id': athlete.strava_id
            },
            'statistics': {
                'total_activities': total_activities,
                'activities_with_metrics': activities_with_metrics,
                'coverage_percentage': round((activities_with_metrics / total_activities) * 100, 1) if total_activities > 0 else 0
            }
        }
        
        return jsonify(summary)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@activities_bp.route('/athlete/<int:athlete_id>/metrics-status')
def get_metrics_status(athlete_id):
    """Statut des métriques Strava pour un athlète"""
    try:
        # Compter les activités avec et sans métriques
        total_activities = ActivitySummary.query.filter_by(athlete_id=athlete_id).count()
        
        activities_with_metrics = db.session.query(ActivitySummary)\
            .join(ActivityStravaMetrics, ActivitySummary.id == ActivityStravaMetrics.activity_id)\
            .filter(ActivitySummary.athlete_id == athlete_id).count()
        
        activities_without_metrics = total_activities - activities_with_metrics
        
        status = {
            'total_activities': total_activities,
            'activities_with_metrics': activities_with_metrics,
            'activities_without_metrics': activities_without_metrics,
            'coverage_percentage': round((activities_with_metrics / total_activities) * 100, 1) if total_activities > 0 else 0
        }
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@activities_bp.route('/athlete/<int:athlete_id>/export')
def export_activities_enhanced(athlete_id):
    """Export CSV enrichi avec métriques Strava"""
    try:
        # Paramètres d'export
        year = request.args.get('year', type=int)
        activity_type = request.args.get('type')
        
        # Requête de base
        query = db.session.query(ActivitySummary, ActivityStravaMetrics)\
            .outerjoin(ActivityStravaMetrics, ActivitySummary.id == ActivityStravaMetrics.activity_id)\
            .filter(ActivitySummary.athlete_id == athlete_id)
        
        # Filtres
        if year:
            query = query.filter(ActivitySummary.year == year)
        if activity_type:
            query = query.filter(ActivitySummary.type == activity_type)
        
        activities = query.order_by(desc(ActivitySummary.start_date_local)).all()
        
        # En-têtes CSV
        headers = [
            'Date', 'Nom', 'Type', 'Distance_km', 'Durée_heures', 
            'Vitesse_moyenne', 'Dénivelé', 'FC_moyenne', 'Calories',
            'Puissance_moyenne', 'Puissance_normalized', 'Suffer_Score'
        ]
        
        # Données CSV
        csv_data = [headers]
        
        for activity, metrics in activities:
            row = [
                activity.start_date_local.strftime('%Y-%m-%d %H:%M:%S'),
                activity.name,
                activity.type,
                float(activity.distance_km) if activity.distance_km else 0,
                float(activity.moving_time_hours) if activity.moving_time_hours else 0,
                float(activity.average_speed) if activity.average_speed else '',
                float(activity.total_elevation_gain) if activity.total_elevation_gain else '',
                float(activity.average_heartrate) if activity.average_heartrate else '',
                float(activity.calories) if activity.calories else '',
                float(metrics.average_watts) if metrics and metrics.average_watts else '',
                float(metrics.weighted_average_watts) if metrics and metrics.weighted_average_watts else '',
                float(metrics.suffer_score) if metrics and metrics.suffer_score else ''
            ]
            csv_data.append(row)
        
        # Générer le CSV
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerows(csv_data)
        csv_content = output.getvalue()
        output.close()
        
        # Nom du fichier
        filename = f"strava_activities_{athlete_id}"
        if year:
            filename += f"_{year}"
        if activity_type:
            filename += f"_{activity_type}"
        filename += "_enriched.csv"
        
        from flask import Response
        return Response(
            csv_content,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500