from flask import Blueprint, jsonify, request
from models.database import db, Athlete, ActivitySummary
from models.strava_metrics import ActivityStravaMetrics
from models.custom_metrics import ActivityCustomMetrics, AthleteSettings
from services.strava_service import StravaService
from services.custom_calculations import CustomCalculationsService
from sqlalchemy import and_, func, desc
from datetime import datetime, timedelta

activities_bp = Blueprint('activities', __name__)

# ========== FONCTION UTILITAIRE POUR CORRIGER LES DECIMAL ==========
def safe_float(value, default=0.0):
    """Convertit une valeur Decimal/None en float de manière sécurisée"""
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError, AttributeError):
        return default

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
            # Utiliser to_dict() mais corriger seulement les erreurs Decimal spécifiques
            try:
                activity_data = activity.to_dict()
            except TypeError as e:
                if "Decimal" in str(e):
                    # Conversion manuelle seulement si erreur Decimal
                    activity_data = {}
                    for column in activity.__table__.columns:
                        value = getattr(activity, column.name, None)
                        if value is not None and hasattr(value, 'to_eng_string'):  # Test si Decimal
                            activity_data[column.name] = float(value)
                        else:
                            activity_data[column.name] = value
                else:
                    raise e
            
            # Ajouter les métriques Strava si disponibles
            if strava_metrics:
                try:
                    activity_data['strava_metrics'] = strava_metrics.to_dict()
                except TypeError as e:
                    if "Decimal" in str(e):
                        # Conversion manuelle seulement si erreur Decimal
                        strava_data = {}
                        for column in strava_metrics.__table__.columns:
                            value = getattr(strava_metrics, column.name, None)
                            if value is not None and hasattr(value, 'to_eng_string'):  # Test si Decimal
                                strava_data[column.name] = float(value)
                            else:
                                strava_data[column.name] = value
                        activity_data['strava_metrics'] = strava_data
                    else:
                        raise e
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
        
        # Statistiques calculs personnalisés
        activities_with_custom = db.session.query(ActivitySummary)\
            .join(ActivityCustomMetrics, ActivitySummary.id == ActivityCustomMetrics.activity_id)\
            .filter(ActivitySummary.athlete_id == athlete_id).count()
        
        # Paramètres utilisateur
        settings = AthleteSettings.query.get(athlete_id)
        
        summary = {
            'athlete': {
                'id': athlete.id,
                'name': f"{athlete.firstname} {athlete.lastname}",
                'strava_id': athlete.strava_id
            },
            'statistics': {
                'total_activities': total_activities,
                'activities_with_strava_metrics': activities_with_metrics,
                'activities_with_custom_metrics': activities_with_custom,
                'strava_coverage_percentage': round((activities_with_metrics / total_activities) * 100, 1) if total_activities > 0 else 0,
                'custom_coverage_percentage': round((activities_with_custom / total_activities) * 100, 1) if total_activities > 0 else 0
            },
            'settings': settings.to_dict() if settings else None
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
        
        activities_with_custom = db.session.query(ActivitySummary)\
            .join(ActivityCustomMetrics, ActivitySummary.id == ActivityCustomMetrics.activity_id)\
            .filter(ActivitySummary.athlete_id == athlete_id).count()
        
        activities_without_metrics = total_activities - activities_with_metrics
        activities_without_custom = total_activities - activities_with_custom
        
        status = {
            'total_activities': total_activities,
            'strava_metrics': {
                'activities_with_metrics': activities_with_metrics,
                'activities_without_metrics': activities_without_metrics,
                'coverage_percentage': round((activities_with_metrics / total_activities) * 100, 1) if total_activities > 0 else 0
            },
            'custom_metrics': {
                'activities_with_metrics': activities_with_custom,
                'activities_without_metrics': activities_without_custom,
                'coverage_percentage': round((activities_with_custom / total_activities) * 100, 1) if total_activities > 0 else 0
            }
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
                safe_float(activity.distance_km),
                safe_float(activity.moving_time_hours),
                safe_float(activity.average_speed),
                safe_float(activity.total_elevation_gain),
                safe_float(activity.average_heartrate),
                safe_float(activity.calories),
                safe_float(metrics.average_watts) if metrics else '',
                safe_float(metrics.weighted_average_watts) if metrics else '',
                safe_float(metrics.suffer_score) if metrics else ''
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

# ===================================================
# PHASE 2 : ENDPOINTS CALCULS PERSONNALISÉS
# ===================================================

@activities_bp.route('/athlete/<int:athlete_id>/settings', methods=['GET'])
def get_athlete_settings(athlete_id):
    """Récupérer les paramètres personnels d'un athlète"""
    try:
        settings = AthleteSettings.query.get(athlete_id)
        if not settings:
            # Créer avec FTP par défaut si n'existe pas
            settings = AthleteSettings.get_or_create_for_athlete(athlete_id, 245)
        
        return jsonify(settings.to_dict())
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@activities_bp.route('/athlete/<int:athlete_id>/settings', methods=['POST'])
def set_athlete_settings(athlete_id):
    """Configurer les paramètres personnels d'un athlète"""
    try:
        data = request.get_json()
        
        if not data or 'ftp' not in data:
            return jsonify({'error': 'FTP requis'}), 400
        
        ftp = data.get('ftp')
        if not isinstance(ftp, int) or ftp <= 0:
            return jsonify({'error': 'FTP doit être un entier positif'}), 400
        
        # Récupérer ou créer les paramètres
        settings = AthleteSettings.query.get(athlete_id)
        if settings:
            settings.current_ftp = ftp
            settings.max_heartrate = data.get('max_heartrate')
            settings.resting_heartrate = data.get('resting_heartrate')
            settings.weight = data.get('weight')
            settings.updated_at = datetime.utcnow()
        else:
            settings = AthleteSettings(
                athlete_id=athlete_id,
                current_ftp=ftp,
                max_heartrate=data.get('max_heartrate'),
                resting_heartrate=data.get('resting_heartrate'),
                weight=data.get('weight')
            )
            db.session.add(settings)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Paramètres mis à jour',
            'settings': settings.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@activities_bp.route('/athlete/<int:athlete_id>/calculate-custom-metrics', methods=['POST'])
def calculate_custom_metrics(athlete_id):
    """Calculer les métriques personnalisées pour toutes les activités"""
    try:
        athlete = Athlete.query.get(athlete_id)
        if not athlete:
            return jsonify({'error': 'Athlete not found'}), 404
        
        # Récupérer FTP depuis paramètres ou requête
        data = request.get_json() if request.is_json else {}
        user_ftp = data.get('ftp')
        
        if not user_ftp:
            settings = AthleteSettings.query.get(athlete_id)
            user_ftp = settings.current_ftp if settings else 245
        
        # Lancer les calculs
        calc_service = CustomCalculationsService()
        result = calc_service.calculate_all_athlete_activities(athlete_id, user_ftp)
        
        return jsonify({
            'message': 'Calculs personnalisés terminés',
            'athlete': f"{athlete.firstname} {athlete.lastname}",
            'ftp_used': user_ftp,
            'results': result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@activities_bp.route('/athlete/<int:athlete_id>/custom-metrics')
def get_custom_metrics(athlete_id):
    """Récupérer les métriques personnalisées d'un athlète"""
    try:
        # Paramètres de requête
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 200)
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        
        # Requête avec jointures
        query = db.session.query(ActivitySummary, ActivityStravaMetrics, ActivityCustomMetrics)\
            .outerjoin(ActivityStravaMetrics, ActivitySummary.id == ActivityStravaMetrics.activity_id)\
            .join(ActivityCustomMetrics, ActivitySummary.id == ActivityCustomMetrics.activity_id)\
            .filter(ActivitySummary.athlete_id == athlete_id)
        
        # Filtres
        if year:
            query = query.filter(ActivitySummary.year == year)
        if month:
            query = query.filter(ActivitySummary.month == month)
        
        # Pagination
        activities = query.order_by(desc(ActivitySummary.start_date_local))\
            .offset((page - 1) * per_page)\
            .limit(per_page).all()
        
        total = query.count()
        
        # Formatage des résultats
        result = []
        for activity, strava_metrics, custom_metrics in activities:
            activity_data = activity.to_dict()
            activity_data['strava_metrics'] = strava_metrics.to_dict() if strava_metrics else None
            activity_data['custom_metrics'] = custom_metrics.to_dict() if custom_metrics else None
            
            # Comparaison TSS si disponible
            if strava_metrics and custom_metrics and strava_metrics.suffer_score:
                activity_data['tss_comparison'] = custom_metrics.get_comparison_vs_strava(
                    strava_metrics.suffer_score
                )
            
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

@activities_bp.route('/athlete/<int:athlete_id>/personal-records')
def get_personal_records(athlete_id):
    """Récupérer les records personnels d'un athlète"""
    try:
        calc_service = CustomCalculationsService()
        records = calc_service.get_athlete_records_summary(athlete_id)
        
        if not records:
            return jsonify({
                'message': 'Aucun record trouvé. Lancez d\'abord les calculs personnalisés.',
                'records': None
            })
        
        # Récupérer les paramètres actuels
        settings = AthleteSettings.query.get(athlete_id)
        
        return jsonify({
            'athlete_id': athlete_id,
            'current_ftp': settings.current_ftp if settings else None,
            'records': records,
            'generated_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@activities_bp.route('/athlete/<int:athlete_id>/training-summary-custom')
def get_training_summary_custom(athlete_id):
    """Résumé d'entraînement avec métriques personnalisées"""
    try:
        days = request.args.get('days', 30, type=int)
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Statistiques avec métriques personnalisées
        stats = db.session.query(
            func.count(ActivityCustomMetrics.id).label('activities_with_custom'),
            func.avg(ActivityCustomMetrics.custom_tss).label('avg_custom_tss'),
            func.sum(ActivityCustomMetrics.custom_tss).label('total_custom_tss'),
            func.max(ActivityCustomMetrics.custom_tss).label('max_custom_tss'),
            func.avg(ActivityCustomMetrics.intensity_factor).label('avg_if'),
            func.max(ActivityCustomMetrics.intensity_factor).label('max_if')
        ).join(ActivitySummary, ActivityCustomMetrics.activity_id == ActivitySummary.id)\
         .filter(ActivitySummary.athlete_id == athlete_id)\
         .filter(ActivitySummary.start_date_local >= cutoff_date).first()
        
        # Distribution par zones d'intensité
        zone_stats = db.session.query(
            ActivityCustomMetrics.intensity_factor,
            func.count().label('count')
        ).join(ActivitySummary, ActivityCustomMetrics.activity_id == ActivitySummary.id)\
         .filter(ActivitySummary.athlete_id == athlete_id)\
         .filter(ActivitySummary.start_date_local >= cutoff_date)\
         .filter(ActivityCustomMetrics.intensity_factor.isnot(None))\
         .all()
        
        # Classifier par zones
        zones = {'recovery': 0, 'endurance': 0, 'tempo': 0, 'threshold': 0, 'threshold_plus': 0}
        for if_value, count in zone_stats:
            if_val = float(if_value)
            if if_val >= 1.05:
                zones['threshold_plus'] += count
            elif if_val >= 0.95:
                zones['threshold'] += count
            elif if_val >= 0.85:
                zones['tempo'] += count
            elif if_val >= 0.70:
                zones['endurance'] += count
            else:
                zones['recovery'] += count
        
        return jsonify({
            'period_days': days,
            'training_load': {
                'activities_with_custom_metrics': stats.activities_with_custom or 0,
                'avg_custom_tss': round(float(stats.avg_custom_tss), 1) if stats.avg_custom_tss else None,
                'total_custom_tss': round(float(stats.total_custom_tss), 1) if stats.total_custom_tss else None,
                'max_custom_tss': round(float(stats.max_custom_tss), 1) if stats.max_custom_tss else None,
                'avg_intensity_factor': round(float(stats.avg_if), 3) if stats.avg_if else None,
                'max_intensity_factor': round(float(stats.max_if), 3) if stats.max_if else None
            },
            'intensity_zones': zones,
            'generated_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@activities_bp.route('/athlete/<int:athlete_id>/export-custom')
def export_custom_metrics(athlete_id):
    """Export CSV avec métriques personnalisées"""
    try:
        # Paramètres d'export
        year = request.args.get('year', type=int)
        activity_type = request.args.get('type')
        
        # Requête avec toutes les métriques
        query = db.session.query(ActivitySummary, ActivityStravaMetrics, ActivityCustomMetrics)\
            .outerjoin(ActivityStravaMetrics, ActivitySummary.id == ActivityStravaMetrics.activity_id)\
            .outerjoin(ActivityCustomMetrics, ActivitySummary.id == ActivityCustomMetrics.activity_id)\
            .filter(ActivitySummary.athlete_id == athlete_id)
        
        # Filtres
        if year:
            query = query.filter(ActivitySummary.year == year)
        if activity_type:
            query = query.filter(ActivitySummary.type == activity_type)
        
        activities = query.order_by(desc(ActivitySummary.start_date_local)).all()
        
        # En-têtes CSV enrichis
        headers = [
            'Date', 'Nom', 'Type', 'Distance_km', 'Durée_heures',
            'NP_Strava', 'TSS_Strava', 'TSS_Personnel', 'Différence_TSS', 'IF_Personnel',
            'Zone_Puissance', 'Record_1min', 'Record_5min', 'Record_20min',
            'Temps_1km', 'Temps_5km', 'Temps_10km', 'FTP_Utilisé'
        ]
        
        # Données CSV
        csv_data = [headers]
        
        for activity, strava_metrics, custom_metrics in activities:
            # Calculs de différence TSS
            tss_diff = None
            if (strava_metrics and custom_metrics and 
                strava_metrics.suffer_score and custom_metrics.custom_tss):
                tss_diff = round(float(custom_metrics.custom_tss) - float(strava_metrics.suffer_score), 1)
            
            row = [
                activity.start_date_local.strftime('%Y-%m-%d %H:%M:%S'),
                activity.name,
                activity.type,
                safe_float(activity.distance_km),  # ← CORRIGÉ
                safe_float(activity.moving_time_hours),  # ← CORRIGÉ
                float(strava_metrics.weighted_average_watts) if strava_metrics and strava_metrics.weighted_average_watts else '',
                float(strava_metrics.suffer_score) if strava_metrics and strava_metrics.suffer_score else '',
                float(custom_metrics.custom_tss) if custom_metrics and custom_metrics.custom_tss else '',
                tss_diff if tss_diff is not None else '',
                float(custom_metrics.intensity_factor) if custom_metrics and custom_metrics.intensity_factor else '',
                custom_metrics.get_power_zone() if custom_metrics else '',
                custom_metrics.best_1min_power if custom_metrics else '',
                custom_metrics.best_5min_power if custom_metrics else '',
                custom_metrics.best_20min_power if custom_metrics else '',
                custom_metrics.best_1km_time if custom_metrics else '',
                custom_metrics.best_5km_time if custom_metrics else '',
                custom_metrics.best_10km_time if custom_metrics else '',
                custom_metrics.user_ftp if custom_metrics else ''
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
        filename = f"strava_custom_metrics_{athlete_id}"
        if year:
            filename += f"_{year}"
        if activity_type:
            filename += f"_{activity_type}"
        filename += "_ftp245.csv"
        
        from flask import Response
        return Response(
            csv_content,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@activities_bp.route('/athlete/<int:athlete_id>/training-load-analysis')
def get_training_load_analysis(athlete_id):
    """Analyse détaillée de la charge d'entraînement"""
    try:
        days = request.args.get('days', 90, type=int)
        
        calc_service = CustomCalculationsService()
        analysis = calc_service.get_training_load_analysis(athlete_id, days)
        
        if not analysis:
            return jsonify({
                'message': 'Aucune donnée trouvée. Calculez d\'abord les métriques personnalisées.',
                'analysis': None
            })
        
        return jsonify(analysis)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@activities_bp.route('/athlete/<int:athlete_id>/compare-tss')
def compare_tss_metrics(athlete_id):
    """Comparer TSS personnel vs Strava"""
    try:
        limit = request.args.get('limit', 20, type=int)
        
        calc_service = CustomCalculationsService()
        comparison = calc_service.compare_with_strava_metrics(athlete_id, limit)
        
        if not comparison:
            return jsonify({
                'message': 'Pas assez de données pour comparaison',
                'comparison': None
            })
        
        return jsonify(comparison)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@activities_bp.route('/athlete/<int:athlete_id>/ftp-tests')
def detect_ftp_tests(athlete_id):
    """Détecter les potentiels tests FTP"""
    try:
        months = request.args.get('months', 6, type=int)
        
        calc_service = CustomCalculationsService()
        ftp_tests = calc_service.detect_ftp_tests(athlete_id, months)
        
        return jsonify({
            'potential_ftp_tests': ftp_tests,
            'analysis_period_months': months,
            'found_tests': len(ftp_tests)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@activities_bp.route('/athlete/<int:athlete_id>/power-curve')
def get_power_curve(athlete_id):
    """Courbe de puissance de l'athlète"""
    try:
        calc_service = CustomCalculationsService()
        power_curve = calc_service.get_power_curve_data(athlete_id)
        
        if not power_curve:
            return jsonify({
                'message': 'Pas assez de données de puissance',
                'power_curve': None
            })
        
        return jsonify(power_curve)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@activities_bp.route('/athlete/<int:athlete_id>/training-patterns')
def analyze_training_patterns(athlete_id):
    """Analyser les patterns d'entraînement"""
    try:
        days = request.args.get('days', 90, type=int)
        
        calc_service = CustomCalculationsService()
        patterns = calc_service.analyze_training_patterns(athlete_id, days)
        
        if not patterns:
            return jsonify({
                'message': 'Pas assez de données pour l\'analyse',
                'patterns': None
            })
        
        return jsonify(patterns)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@activities_bp.route('/athlete/<int:athlete_id>/recommendations')
def get_training_recommendations(athlete_id):
    """Recommandations d'entraînement personnalisées"""
    try:
        recent_days = request.args.get('days', 14, type=int)
        
        calc_service = CustomCalculationsService()
        recommendations = calc_service.get_activity_recommendations(athlete_id, recent_days)
        
        return jsonify(recommendations)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@activities_bp.route('/athlete/<int:athlete_id>/dashboard-custom')
def get_custom_dashboard(athlete_id):
    """Dashboard complet avec métriques personnalisées"""
    try:
        # Récupérer les paramètres
        settings = AthleteSettings.query.get(athlete_id)
        if not settings:
            return jsonify({
                'error': 'Paramètres non configurés. Définissez d\'abord votre FTP.',
                'setup_required': True
            }), 400
        
        calc_service = CustomCalculationsService()
        
        # Records personnels
        records = calc_service.get_athlete_records_summary(athlete_id)
        
        # Analyse charge récente (30 jours)
        load_analysis = calc_service.get_training_load_analysis(athlete_id, 30)
        
        # Comparaison TSS (10 dernières activités)
        tss_comparison = calc_service.compare_with_strava_metrics(athlete_id, 10)
        
        # Tests FTP potentiels
        ftp_tests = calc_service.detect_ftp_tests(athlete_id, 3)
        
        # Recommandations
        recommendations = calc_service.get_activity_recommendations(athlete_id, 14)
        
        dashboard = {
            'athlete_settings': settings.to_dict(),
            'personal_records': records,
            'recent_training_load': load_analysis,
            'tss_comparison_recent': tss_comparison,
            'potential_ftp_tests': ftp_tests[:3] if ftp_tests else [],  # Top 3
            'training_recommendations': recommendations,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        return jsonify(dashboard)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@activities_bp.route('/athlete/<int:athlete_id>/update-ftp', methods=['POST'])
def update_ftp_and_recalculate(athlete_id):
    """Mettre à jour le FTP et recalculer les métriques affectées"""
    try:
        data = request.get_json()
        new_ftp = data.get('new_ftp')
        
        if not new_ftp or not isinstance(new_ftp, int) or new_ftp <= 0:
            return jsonify({'error': 'FTP valide requis'}), 400
        
        # Mettre à jour les paramètres
        settings = AthleteSettings.get_or_create_for_athlete(athlete_id, new_ftp)
        old_ftp = settings.current_ftp
        settings.current_ftp = new_ftp
        settings.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Optionnel : recalculer les métriques récentes (30 derniers jours)
        recalculate = data.get('recalculate_recent', False)
        recalculated_count = 0
        
        if recalculate:
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            # Supprimer les calculs récents pour recalculer avec nouveau FTP
            recent_custom_metrics = db.session.query(ActivityCustomMetrics)\
                .join(ActivitySummary, ActivityCustomMetrics.activity_id == ActivitySummary.id)\
                .filter(ActivitySummary.athlete_id == athlete_id)\
                .filter(ActivitySummary.start_date_local >= cutoff_date).all()
            
            for metrics in recent_custom_metrics:
                db.session.delete(metrics)
            
            db.session.commit()
            
            # Recalculer avec nouveau FTP
            calc_service = CustomCalculationsService()
            recent_activities = ActivitySummary.query\
                .filter_by(athlete_id=athlete_id)\
                .filter(ActivitySummary.start_date_local >= cutoff_date).all()
            
            for activity in recent_activities:
                try:
                    calc_service.calculate_activity_custom_metrics(
                        activity.id, athlete_id, new_ftp
                    )
                    recalculated_count += 1
                except Exception as e:
                    continue
        
        return jsonify({
            'message': 'FTP mis à jour avec succès',
            'old_ftp': old_ftp,
            'new_ftp': new_ftp,
            'difference': new_ftp - old_ftp,
            'recalculated_activities': recalculated_count if recalculate else 0,
            'settings': settings.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500