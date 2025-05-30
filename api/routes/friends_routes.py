# Fichier: api/routes/friends_routes.py
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin

friends_bp = Blueprint('friends', __name__)

@friends_bp.route('/auth/friends/exchange', methods=['POST', 'OPTIONS'])
@cross_origin(origins=['https://strava-jerome.web.app'])
def exchange_friend_code():
    """Endpoint pour échanger le code d'autorisation d'un ami"""
    
    # Gérer preflight OPTIONS
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        code = data.get('code') if data else None
        
        if not code:
            return jsonify({'error': 'Code manquant'}), 400
        
        # TODO: Implémenter l'échange de code
        # Pour l'instant, retourner une réponse de test
        
        return jsonify({
            'success': True,
            'message': 'Endpoint friends en cours de développement',
            'received_code': code[:10] + '...' if len(code) > 10 else code
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@friends_bp.route('/api/friends/list', methods=['GET'])
@cross_origin(origins=['https://strava-jerome.web.app'])
def list_friends():
    """Lister tous les amis autorisés (temporaire)"""
    try:
        return jsonify({
            'friends': [],
            'total': 0,
            'message': 'API friends en développement'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@friends_bp.route('/api/friends/status', methods=['GET'])
def friends_status():
    """Status de l'API friends"""
    return jsonify({
        'status': 'Friends API loaded',
        'version': '0.1.0',
        'endpoints': [
            '/auth/friends/exchange',
            '/api/friends/list',
            '/api/friends/status'
        ]
    })