from flask import Blueprint, request, jsonify

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/test')
def test():
    return jsonify({'message': 'Analytics route works', 'status': 'ok'})

@analytics_bp.route('/athlete/<int:athlete_id>/monthly')
def monthly_stats(athlete_id):
    """Statistiques mensuelles - Version simplifiée"""
    return jsonify({
        'athlete_id': athlete_id,
        'message': 'Monthly stats endpoint - TODO: implement with database',
        'status': 'ok'
    })

@analytics_bp.route('/athlete/<int:athlete_id>/dashboard')
def dashboard(athlete_id):
    """Dashboard simplifié"""
    return jsonify({
        'athlete_id': athlete_id,
        'message': 'Dashboard endpoint - TODO: implement with database',
        'status': 'ok'
    })