# Fichier: api/friends/auth.py
import requests
import os
from .models import save_friend_tokens

def exchange_strava_code(code):
    """Échanger le code d'autorisation contre les tokens Strava"""
    token_url = "https://www.strava.com/oauth/token"
    
    payload = {
        'client_id': os.getenv('STRAVA_CLIENT_ID'),
        'client_secret': os.getenv('STRAVA_CLIENT_SECRET'),
        'code': code,
        'grant_type': 'authorization_code'
    }
    
    response = requests.post(token_url, data=payload)
    
    if not response.ok:
        raise Exception(f"Erreur Strava: {response.status_code} - {response.text}")
        
    data = response.json()
    
    return {
        'access_token': data['access_token'],
        'refresh_token': data['refresh_token'],
        'expires_at': data['expires_at'],
        'athlete_id': data['athlete']['id'],
        'athlete_name': f"{data['athlete']['firstname']} {data['athlete']['lastname']}",
        'scopes': ','.join(data.get('scope', []))
    }

def process_friend_authorization(code):
    """Traiter l'autorisation complète d'un ami"""
    # Échanger le code
    token_data = exchange_strava_code(code)
    
    # Sauvegarder en base
    result = save_friend_tokens(token_data)
    
    return {
        'success': True,
        'athlete_id': token_data['athlete_id'],
        'athlete_name': token_data['athlete_name']
    }