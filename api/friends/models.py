# Fichier: api/friends/models.py
import psycopg2
from contextlib import contextmanager
import os
import time

@contextmanager
def get_db_connection():
    """Gestionnaire de connexion à la base de données"""
    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=os.getenv('POSTGRES_PORT', 5433),
        database=os.getenv('POSTGRES_DB', 'strava_analytics_db'),
        user=os.getenv('POSTGRES_USER', 'strava_user'),
        password=os.getenv('POSTGRES_PASSWORD')
    )
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def save_friend_tokens(token_data):
    """Sauvegarder/mettre à jour les tokens d'un ami"""
    query = """
    INSERT INTO friends_auth (athlete_id, athlete_name, access_token, refresh_token, expires_at, scopes)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (athlete_id) 
    DO UPDATE SET
        access_token = EXCLUDED.access_token,
        refresh_token = EXCLUDED.refresh_token,
        expires_at = EXCLUDED.expires_at,
        updated_at = CURRENT_TIMESTAMP
    RETURNING athlete_id, athlete_name
    """
    
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (
                token_data['athlete_id'],
                token_data['athlete_name'],
                token_data['access_token'],
                token_data['refresh_token'],
                token_data['expires_at'],
                token_data.get('scopes', 'read_all,activity:read_all')
            ))
            return cursor.fetchone()

def get_friend_token(athlete_id):
    """Récupérer le token d'un ami"""
    query = """
    SELECT access_token, refresh_token, expires_at 
    FROM friends_auth 
    WHERE athlete_id = %s
    """
    
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (athlete_id,))
            result = cursor.fetchone()
            
            if not result:
                return None
                
            access_token, refresh_token, expires_at = result
            
            # Vérifier si le token a expiré
            if expires_at < time.time():
                # TODO: Implémenter le renouvellement
                return None
            
            return access_token

def get_all_friends():
    """Récupérer la liste de tous les amis"""
    query = """
    SELECT athlete_id, athlete_name, created_at, 
           (expires_at > %s) as token_valid
    FROM friends_auth 
    ORDER BY athlete_name
    """
    
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (time.time(),))
            return cursor.fetchall()