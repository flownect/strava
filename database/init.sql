-- Extension pour les fonctions avancées
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Index optimisés pour les requêtes temporelles
CREATE INDEX IF NOT EXISTS idx_activity_summary_athlete_date 
ON activity_summary(athlete_id, start_date_local);

CREATE INDEX IF NOT EXISTS idx_activity_summary_type_date 
ON activity_summary(type, start_date_local);

CREATE INDEX IF NOT EXISTS idx_activity_summary_year_month 
ON activity_summary(athlete_id, year, month);

CREATE INDEX IF NOT EXISTS idx_activity_summary_week 
ON activity_summary(athlete_id, year, week);

CREATE INDEX IF NOT EXISTS idx_activity_summary_day_of_week 
ON activity_summary(athlete_id, day_of_week);

CREATE INDEX IF NOT EXISTS idx_activity_summary_day_month_year 
ON activity_summary(athlete_id, day, month, year);

CREATE INDEX IF NOT EXISTS idx_activity_summary_strava_id 
ON activity_summary(strava_id);

-- Index composite pour les requêtes de filtrage
CREATE INDEX IF NOT EXISTS idx_activity_summary_athlete_type_date 
ON activity_summary(athlete_id, type, start_date_local);

-- Vues utiles pour les analyses
CREATE OR REPLACE VIEW monthly_activity_stats AS
SELECT 
    athlete_id,
    year,
    month,
    month_name,
    type,
    COUNT(*) as activity_count,
    ROUND(SUM(distance_km), 2) as total_km,
    ROUND(SUM(moving_time_hours), 2) as total_hours,
    ROUND(AVG(distance_km), 2) as avg_distance,
    ROUND(AVG(moving_time_hours), 2) as avg_duration
FROM activity_summary
GROUP BY athlete_id, year, month, month_name, type;

CREATE OR REPLACE VIEW weekly_activity_stats AS
SELECT 
    athlete_id,
    year,
    week,
    COUNT(*) as activity_count,
    ROUND(SUM(distance_km), 2) as total_km,
    ROUND(SUM(moving_time_hours), 2) as total_hours
FROM activity_summary
GROUP BY athlete_id, year, week;

CREATE OR REPLACE VIEW daily_activity_stats AS
SELECT 
    athlete_id,
    day_name,
    day_of_week,
    COUNT(*) as activity_count,
    ROUND(SUM(distance_km), 2) as total_km,
    ROUND(SUM(moving_time_hours), 2) as total_hours,
    ROUND(AVG(distance_km), 2) as avg_distance
FROM activity_summary
GROUP BY athlete_id, day_name, day_of_week;

-- Vue pour le calendrier des activités
CREATE OR REPLACE VIEW calendar_view AS
SELECT 
    athlete_id,
    start_date_local::date as activity_date,
    year,
    month,
    month_name,
    day,
    day_name,
    COUNT(*) as daily_count,
    ROUND(SUM(distance_km), 2) as daily_km,
    ROUND(SUM(moving_time_hours), 2) as daily_hours,
    string_agg(name, ' | ' ORDER BY start_date_local) as activity_names,
    string_agg(DISTINCT type, ', ') as activity_types
FROM activity_summary
GROUP BY athlete_id, start_date_local::date, year, month, month_name, day, day_name;

-- Vue pour les records personnels
CREATE OR REPLACE VIEW personal_records AS
SELECT 
    athlete_id,
    type,
    MAX(distance_km) as longest_distance,
    MAX(moving_time_hours) as longest_duration,
    MIN(CASE WHEN distance_km > 0 THEN moving_time_hours/distance_km ELSE NULL END) as best_time_per_km,
    MAX(average_speed) as max_speed,
    MAX(total_elevation_gain) as max_elevation,
    COUNT(*) as total_activities
FROM activity_summary
GROUP BY athlete_id, type;

-- Fonction pour calculer la semaine ISO
CREATE OR REPLACE FUNCTION iso_week(date_input DATE)
RETURNS INTEGER
LANGUAGE SQL
IMMUTABLE
AS $$
    SELECT EXTRACT(week FROM date_input)::INTEGER;
$$;

-- Fonction pour obtenir le nom du mois en français
CREATE OR REPLACE FUNCTION french_month_name(month_num INTEGER)
RETURNS TEXT
LANGUAGE SQL
IMMUTABLE
AS $$
    SELECT CASE month_num
        WHEN 1 THEN 'Janvier'
        WHEN 2 THEN 'Février'
        WHEN 3 THEN 'Mars'
        WHEN 4 THEN 'Avril'
        WHEN 5 THEN 'Mai'
        WHEN 6 THEN 'Juin'
        WHEN 7 THEN 'Juillet'
        WHEN 8 THEN 'Août'
        WHEN 9 THEN 'Septembre'
        WHEN 10 THEN 'Octobre'
        WHEN 11 THEN 'Novembre'
        WHEN 12 THEN 'Décembre'
        ELSE 'Inconnu'
    END;
$$;

-- Fonction pour obtenir le nom du jour en français
CREATE OR REPLACE FUNCTION french_day_name(day_num INTEGER)
RETURNS TEXT
LANGUAGE SQL
IMMUTABLE
AS $$
    SELECT CASE day_num
        WHEN 0 THEN 'Lundi'
        WHEN 1 THEN 'Mardi'
        WHEN 2 THEN 'Mercredi'
        WHEN 3 THEN 'Jeudi'
        WHEN 4 THEN 'Vendredi'
        WHEN 5 THEN 'Samedi'
        WHEN 6 THEN 'Dimanche'
        ELSE 'Inconnu'
    END;
$$;

-- Trigger pour mettre à jour automatiquement les noms français
CREATE OR REPLACE FUNCTION update_french_names()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.month_name := french_month_name(NEW.month);
    NEW.day_name := french_day_name(NEW.day_of_week);
    RETURN NEW;
END;
$$;

-- Commentaires sur les tables et colonnes pour documentation
COMMENT ON TABLE activity_summary IS 'Table principale contenant le résumé de toutes les activités Strava';
COMMENT ON COLUMN activity_summary.day_of_week IS '0=Lundi, 1=Mardi, ..., 6=Dimanche';
COMMENT ON COLUMN activity_summary.distance_km IS 'Distance en kilomètres';
COMMENT ON COLUMN activity_summary.moving_time_hours IS 'Temps en mouvement en heures';
COMMENT ON COLUMN activity_summary.day_name IS 'Nom du jour en français (Lundi, Mardi, etc.)';
COMMENT ON COLUMN activity_summary.month_name IS 'Nom du mois en français (Janvier, Février, etc.)';

-- Statistiques pour l'optimiseur de requêtes
CREATE STATISTICS IF NOT EXISTS activity_summary_stats 
ON athlete_id, type, year, month 
FROM activity_summary;