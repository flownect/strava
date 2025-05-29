-- Extension pour les fonctions avancées
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- ===================================================
-- NOUVELLE TABLE : MÉTRIQUES STRAVA NATIVES (PHASE 1)
-- ===================================================

-- 🏃‍♂️ MÉTRIQUES D'ENTRAÎNEMENT NATIVES STRAVA
CREATE TABLE IF NOT EXISTS activity_strava_metrics (
    id SERIAL PRIMARY KEY,
    activity_id INTEGER REFERENCES activity_summary(id) ON DELETE CASCADE,
    
    -- 💪 Données de puissance natives Strava
    average_watts DECIMAL(6,1),                 -- Puissance moyenne
    weighted_average_watts DECIMAL(6,1),        -- ✅ Normalized Power Strava
    max_watts DECIMAL(6,1),                     -- Puissance max
    device_watts BOOLEAN DEFAULT FALSE,         -- ✅ Capteur puissance réel vs estimé
    
    -- ❤️ Données FC natives Strava  
    average_heartrate DECIMAL(5,2),            -- FC moyenne
    max_heartrate DECIMAL(5,2),                -- FC max
    has_heartrate BOOLEAN DEFAULT FALSE,        -- ✅ Capteur FC présent
    
    -- 🎯 Métriques d'effort Strava
    suffer_score DECIMAL(6,1),                 -- ✅ TSS équivalent Strava
    perceived_exertion INTEGER,                -- RPE 1-10
    
    -- 🚴‍♂️ Données vélo spécifiques
    average_cadence DECIMAL(5,2),              -- Cadence moyenne
    average_temp DECIMAL(4,1),                 -- Température moyenne
    trainer BOOLEAN DEFAULT FALSE,             -- Home trainer
    commute BOOLEAN DEFAULT FALSE,             -- Trajet domicile-travail
    
    -- 🏃‍♂️ Données course spécifiques  
    average_speed_ms DECIMAL(8,4),             -- Vitesse moyenne (m/s)
    max_speed_ms DECIMAL(8,4),                 -- Vitesse max (m/s)
    
    -- 📍 Métadonnées
    gear_id VARCHAR(50),                       -- ID équipement Strava
    external_id VARCHAR(100),                  -- ID device externe
    upload_id BIGINT,                          -- ID upload Strava
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(activity_id)
);

-- ===================================================
-- PHASE 2 : CALCULS PERSONNALISÉS
-- ===================================================

-- Table pour les calculs personnalisés basés sur données Strava existantes
CREATE TABLE IF NOT EXISTS activity_custom_metrics (
    id BIGSERIAL PRIMARY KEY,
    activity_id INTEGER REFERENCES activity_summary(id) ON DELETE CASCADE,
    athlete_id INTEGER NOT NULL,
    
    -- Paramètres utilisés pour les calculs
    user_ftp INTEGER NOT NULL,           -- FTP utilisateur au moment du calcul
    user_weight DECIMAL(5,2),           -- Poids utilisateur (optionnel)
    
    -- TSS et intensité personnalisés (basés sur NP Strava + votre FTP)
    custom_tss DECIMAL(8,2),            -- TSS recalculé avec VOTRE FTP
    intensity_factor DECIMAL(5,4),      -- IF = NP_Strava / VOTRE_FTP
    training_load DECIMAL(8,2),         -- Charge d'entraînement personnalisée
    
    -- Records de puissance détectés (basés sur durée + puissance Strava)
    best_1min_power INTEGER,            -- Meilleure puissance 1min estimée
    best_5min_power INTEGER,            -- Meilleure puissance 5min estimée  
    best_20min_power INTEGER,           -- Meilleure puissance 20min estimée
    
    -- Records de distance (basés sur distance + temps existants)
    best_1km_time INTEGER,              -- Meilleur temps 1km (secondes)
    best_5km_time INTEGER,              -- Meilleur temps 5km (secondes)
    best_10km_time INTEGER,             -- Meilleur temps 10km (secondes)
    best_half_marathon_time INTEGER,    -- Meilleur temps 21.1km (secondes)
    best_marathon_time INTEGER,         -- Meilleur temps 42.2km (secondes)
    
    -- Métadonnées
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    calculation_method VARCHAR(50) DEFAULT 'strava_based', -- Méthode utilisée
    
    UNIQUE(activity_id, athlete_id)
);

-- Table paramètres athlète (vos seuils personnels)
CREATE TABLE IF NOT EXISTS athlete_settings (
    athlete_id INTEGER PRIMARY KEY REFERENCES athletes(id),
    
    -- Seuils physiologiques
    current_ftp INTEGER NOT NULL,       -- Votre FTP actuel
    max_heartrate INTEGER,              -- FC max (optionnel)
    resting_heartrate INTEGER,          -- FC repos (optionnel)
    weight DECIMAL(5,2),               -- Poids actuel (optionnel)
    
    -- Paramètres de calcul
    auto_update_ftp BOOLEAN DEFAULT TRUE,        -- Mise à jour auto FTP basée sur performances
    ftp_test_detection BOOLEAN DEFAULT TRUE,     -- Détection auto tests FTP
    
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index optimisés pour les nouvelles données
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

-- ===================================================
-- INDEX POUR LES NOUVELLES MÉTRIQUES STRAVA
-- ===================================================

CREATE INDEX IF NOT EXISTS idx_strava_metrics_activity ON activity_strava_metrics(activity_id);
CREATE INDEX IF NOT EXISTS idx_strava_metrics_watts ON activity_strava_metrics(weighted_average_watts);
CREATE INDEX IF NOT EXISTS idx_strava_metrics_device ON activity_strava_metrics(device_watts);
CREATE INDEX IF NOT EXISTS idx_strava_metrics_suffer ON activity_strava_metrics(suffer_score);
CREATE INDEX IF NOT EXISTS idx_strava_metrics_hr ON activity_strava_metrics(has_heartrate);

-- Index pour performances Phase 2
CREATE INDEX IF NOT EXISTS idx_custom_metrics_activity ON activity_custom_metrics(activity_id);
CREATE INDEX IF NOT EXISTS idx_custom_metrics_athlete ON activity_custom_metrics(athlete_id);
CREATE INDEX IF NOT EXISTS idx_custom_metrics_tss ON activity_custom_metrics(custom_tss);
CREATE INDEX IF NOT EXISTS idx_custom_metrics_if ON activity_custom_metrics(intensity_factor);

-- ===================================================
-- VUES ENRICHIES AVEC MÉTRIQUES STRAVA ET PERSONNALISÉES
-- ===================================================

-- Vue enrichie avec métriques Strava
CREATE OR REPLACE VIEW activity_with_strava_metrics AS
SELECT 
    a.*,
    -- Métriques Strava natives
    sm.weighted_average_watts,
    sm.average_watts,
    sm.max_watts,
    sm.suffer_score,
    sm.device_watts,
    sm.has_heartrate,
    sm.average_heartrate as strava_avg_hr,
    sm.max_heartrate as strava_max_hr,
    sm.average_cadence,
    sm.trainer,
    sm.commute,
    sm.gear_id,
    sm.perceived_exertion,
    
    -- Calculs enrichis immédiats
    CASE 
        WHEN sm.device_watts = TRUE THEN 'power_meter'
        WHEN sm.average_watts IS NOT NULL THEN 'estimated'  
        ELSE 'no_power'
    END as power_source,
    
    CASE
        WHEN sm.suffer_score >= 150 THEN 'very_hard'
        WHEN sm.suffer_score >= 100 THEN 'hard'
        WHEN sm.suffer_score >= 50 THEN 'moderate'
        WHEN sm.suffer_score IS NOT NULL THEN 'easy'
        ELSE 'unknown'
    END as effort_level,
    
    CASE 
        WHEN sm.weighted_average_watts IS NOT NULL AND sm.device_watts = TRUE 
        THEN ROUND(sm.weighted_average_watts::numeric, 0)
        ELSE NULL 
    END as normalized_power,
    
    CASE
        WHEN sm.trainer = TRUE THEN 'indoor'
        WHEN sm.commute = TRUE THEN 'commute'
        ELSE 'outdoor'
    END as activity_context
    
FROM activity_summary a
LEFT JOIN activity_strava_metrics sm ON a.id = sm.activity_id;

-- Vue enrichie avec calculs personnalisés
CREATE OR REPLACE VIEW activity_with_custom_metrics AS
SELECT 
    a.*,
    sm.weighted_average_watts,
    sm.suffer_score,
    sm.device_watts,
    sm.has_heartrate,
    sm.trainer,
    sm.commute,
    
    -- Calculs personnalisés
    cm.custom_tss,
    cm.intensity_factor,
    cm.user_ftp,
    
    -- Comparaison Strava vs Personnel
    CASE 
        WHEN sm.suffer_score IS NOT NULL AND cm.custom_tss IS NOT NULL 
        THEN ROUND(cm.custom_tss - sm.suffer_score, 1)
        ELSE NULL 
    END as tss_difference,
    
    CASE
        WHEN cm.intensity_factor >= 1.05 THEN 'threshold_plus'
        WHEN cm.intensity_factor >= 0.95 THEN 'threshold'
        WHEN cm.intensity_factor >= 0.85 THEN 'tempo'
        WHEN cm.intensity_factor >= 0.70 THEN 'endurance'
        WHEN cm.intensity_factor IS NOT NULL THEN 'recovery'
        ELSE 'unknown'
    END as power_zone,
    
    -- Records
    cm.best_1min_power,
    cm.best_5min_power,
    cm.best_20min_power,
    cm.best_1km_time,
    cm.best_5km_time,
    cm.best_10km_time
    
FROM activity_summary a
LEFT JOIN activity_strava_metrics sm ON a.id = sm.activity_id
LEFT JOIN activity_custom_metrics cm ON a.id = cm.activity_id;

-- Vue résumé records personnels
CREATE OR REPLACE VIEW athlete_personal_records AS
SELECT 
    athlete_id,
    
    -- Records de puissance
    MAX(best_1min_power) as all_time_1min_power,
    MAX(best_5min_power) as all_time_5min_power,  
    MAX(best_20min_power) as all_time_20min_power,
    
    -- Records de distance (meilleurs temps)
    MIN(NULLIF(best_1km_time, 0)) as best_1km_time,
    MIN(NULLIF(best_5km_time, 0)) as best_5km_time,
    MIN(NULLIF(best_10km_time, 0)) as best_10km_time,
    MIN(NULLIF(best_half_marathon_time, 0)) as best_half_marathon_time,
    MIN(NULLIF(best_marathon_time, 0)) as best_marathon_time,
    
    -- Statistiques de charge
    AVG(custom_tss) as avg_custom_tss,
    MAX(custom_tss) as max_custom_tss,
    AVG(intensity_factor) as avg_intensity_factor,
    MAX(intensity_factor) as max_intensity_factor,
    
    COUNT(*) as activities_with_custom_metrics
    
FROM activity_custom_metrics
GROUP BY athlete_id;

-- Vues utiles pour les analyses (existantes + enrichies)
CREATE OR REPLACE VIEW monthly_activity_stats AS
SELECT 
    a.athlete_id,
    a.year,
    a.month,
    a.month_name,
    a.type,
    COUNT(*) as activity_count,
    ROUND(SUM(a.distance_km), 2) as total_km,
    ROUND(SUM(a.moving_time_hours), 2) as total_hours,
    ROUND(AVG(a.distance_km), 2) as avg_distance,
    ROUND(AVG(a.moving_time_hours), 2) as avg_duration,
    -- Nouvelles métriques agrégées
    ROUND(AVG(sm.weighted_average_watts), 1) as avg_normalized_power,
    ROUND(AVG(sm.suffer_score), 1) as avg_suffer_score,
    ROUND(SUM(sm.suffer_score), 1) as total_suffer_score,
    COUNT(CASE WHEN sm.device_watts = TRUE THEN 1 END) as power_meter_activities,
    COUNT(CASE WHEN sm.has_heartrate = TRUE THEN 1 END) as hr_activities,
    -- Métriques personnalisées
    ROUND(AVG(cm.custom_tss), 1) as avg_custom_tss,
    ROUND(SUM(cm.custom_tss), 1) as total_custom_tss,
    ROUND(AVG(cm.intensity_factor), 3) as avg_intensity_factor
FROM activity_summary a
LEFT JOIN activity_strava_metrics sm ON a.id = sm.activity_id
LEFT JOIN activity_custom_metrics cm ON a.id = cm.activity_id
GROUP BY a.athlete_id, a.year, a.month, a.month_name, a.type;

CREATE OR REPLACE VIEW weekly_activity_stats AS
SELECT 
    a.athlete_id,
    a.year,
    a.week,
    COUNT(*) as activity_count,
    ROUND(SUM(a.distance_km), 2) as total_km,
    ROUND(SUM(a.moving_time_hours), 2) as total_hours,
    -- Charge d'entraînement hebdomadaire
    ROUND(SUM(sm.suffer_score), 1) as weekly_training_load,
    ROUND(AVG(sm.weighted_average_watts), 1) as avg_power_week,
    COUNT(CASE WHEN sm.device_watts = TRUE THEN 1 END) as power_activities,
    -- Charge personnalisée
    ROUND(SUM(cm.custom_tss), 1) as weekly_custom_tss,
    ROUND(AVG(cm.intensity_factor), 3) as avg_weekly_if
FROM activity_summary a
LEFT JOIN activity_strava_metrics sm ON a.id = sm.activity_id
LEFT JOIN activity_custom_metrics cm ON a.id = cm.activity_id
GROUP BY a.athlete_id, a.year, a.week;

CREATE OR REPLACE VIEW daily_activity_stats AS
SELECT 
    a.athlete_id,
    a.day_name,
    a.day_of_week,
    COUNT(*) as activity_count,
    ROUND(SUM(a.distance_km), 2) as total_km,
    ROUND(SUM(a.moving_time_hours), 2) as total_hours,
    ROUND(AVG(a.distance_km), 2) as avg_distance,
    -- Patterns d'entraînement par jour
    ROUND(AVG(sm.suffer_score), 1) as avg_suffer_score_day,
    COUNT(CASE WHEN sm.trainer = TRUE THEN 1 END) as indoor_activities,
    COUNT(CASE WHEN sm.commute = TRUE THEN 1 END) as commute_activities,
    -- Patterns personnalisés
    ROUND(AVG(cm.custom_tss), 1) as avg_custom_tss_day,
    ROUND(AVG(cm.intensity_factor), 3) as avg_if_day
FROM activity_summary a
LEFT JOIN activity_strava_metrics sm ON a.id = sm.activity_id
LEFT JOIN activity_custom_metrics cm ON a.id = cm.activity_id
GROUP BY a.athlete_id, a.day_name, a.day_of_week;

-- Vue pour le calendrier des activités enrichie
CREATE OR REPLACE VIEW calendar_view AS
SELECT 
    a.athlete_id,
    a.start_date_local::date as activity_date,
    a.year,
    a.month,
    a.month_name,
    a.day,
    a.day_name,
    COUNT(*) as daily_count,
    ROUND(SUM(a.distance_km), 2) as daily_km,
    ROUND(SUM(a.moving_time_hours), 2) as daily_hours,
    string_agg(a.name, ' | ' ORDER BY a.start_date_local) as activity_names,
    string_agg(DISTINCT a.type, ', ') as activity_types,
    -- Charge d'entraînement quotidienne
    ROUND(SUM(sm.suffer_score), 1) as daily_training_load,
    MAX(sm.weighted_average_watts) as best_power_day,
    COUNT(CASE WHEN sm.device_watts = TRUE THEN 1 END) as power_meter_count,
    -- Charge personnalisée quotidienne
    ROUND(SUM(cm.custom_tss), 1) as daily_custom_tss,
    MAX(cm.intensity_factor) as max_if_day
FROM activity_summary a
LEFT JOIN activity_strava_metrics sm ON a.id = sm.activity_id
LEFT JOIN activity_custom_metrics cm ON a.id = cm.activity_id
GROUP BY a.athlete_id, a.start_date_local::date, a.year, a.month, a.month_name, a.day, a.day_name;

-- Vue pour les records personnels enrichie
CREATE OR REPLACE VIEW personal_records AS
SELECT 
    a.athlete_id,
    a.type,
    MAX(a.distance_km) as longest_distance,
    MAX(a.moving_time_hours) as longest_duration,
    MIN(CASE WHEN a.distance_km > 0 THEN a.moving_time_hours/a.distance_km ELSE NULL END) as best_time_per_km,
    MAX(a.average_speed) as max_speed,
    MAX(a.total_elevation_gain) as max_elevation,
    COUNT(*) as total_activities,
    -- Records de puissance
    MAX(sm.weighted_average_watts) as best_normalized_power,
    MAX(sm.max_watts) as peak_power,
    MAX(sm.suffer_score) as highest_suffer_score,
    COUNT(CASE WHEN sm.device_watts = TRUE THEN 1 END) as power_meter_activities,
    -- Moyennes de performance
    ROUND(AVG(sm.weighted_average_watts), 1) as avg_normalized_power,
    ROUND(AVG(sm.suffer_score), 1) as avg_suffer_score,
    -- Records personnalisés
    MAX(cm.best_1min_power) as best_1min_power_record,
    MAX(cm.best_5min_power) as best_5min_power_record,
    MAX(cm.best_20min_power) as best_20min_power_record,
    MIN(NULLIF(cm.best_1km_time, 0)) as best_1km_time_record,
    MIN(NULLIF(cm.best_5km_time, 0)) as best_5km_time_record,
    MIN(NULLIF(cm.best_10km_time, 0)) as best_10km_time_record,
    ROUND(AVG(cm.custom_tss), 1) as avg_custom_tss,
    MAX(cm.custom_tss) as max_custom_tss
FROM activity_summary a
LEFT JOIN activity_strava_metrics sm ON a.id = sm.activity_id
LEFT JOIN activity_custom_metrics cm ON a.id = cm.activity_id
GROUP BY a.athlete_id, a.type;

-- ===================================================
-- FONCTIONS UTILITAIRES
-- ===================================================

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

-- Fonction pour convertir secondes en format lisible
CREATE OR REPLACE FUNCTION format_time_duration(seconds INTEGER)
RETURNS TEXT
LANGUAGE SQL
IMMUTABLE
AS $$
    SELECT CASE 
        WHEN seconds IS NULL OR seconds <= 0 THEN '--'
        WHEN seconds < 60 THEN seconds || 's'
        WHEN seconds < 3600 THEN 
            FLOOR(seconds / 60) || 'min ' || 
            LPAD((seconds % 60)::text, 2, '0') || 's'
        ELSE 
            FLOOR(seconds / 3600) || 'h ' ||
            LPAD(FLOOR((seconds % 3600) / 60)::text, 2, '0') || 'min ' ||
            LPAD((seconds % 60)::text, 2, '0') || 's'
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

-- ===================================================
-- COMMENTAIRES DOCUMENTATION
-- ===================================================

-- Commentaires sur les tables et colonnes pour documentation
COMMENT ON TABLE activity_summary IS 'Table principale contenant le résumé de toutes les activités Strava';
COMMENT ON TABLE activity_strava_metrics IS 'Métriques natives Strava enrichies - Phase 1 implementation';
COMMENT ON TABLE activity_custom_metrics IS 'Calculs personnalisés basés sur métriques Strava existantes et FTP utilisateur - Phase 2';
COMMENT ON TABLE athlete_settings IS 'Paramètres personnels de l''athlète (FTP, seuils, poids) - Phase 2';

COMMENT ON COLUMN activity_summary.day_of_week IS '0=Lundi, 1=Mardi, ..., 6=Dimanche';
COMMENT ON COLUMN activity_summary.distance_km IS 'Distance en kilomètres';
COMMENT ON COLUMN activity_summary.moving_time_hours IS 'Temps en mouvement en heures';
COMMENT ON COLUMN activity_summary.day_name IS 'Nom du jour en français (Lundi, Mardi, etc.)';
COMMENT ON COLUMN activity_summary.month_name IS 'Nom du mois en français (Janvier, Février, etc.)';

COMMENT ON COLUMN activity_strava_metrics.weighted_average_watts IS 'Normalized Power natif Strava (équivalent NP)';
COMMENT ON COLUMN activity_strava_metrics.suffer_score IS 'Training Stress Score Strava (équivalent TSS, échelle 0-500+)';
COMMENT ON COLUMN activity_strava_metrics.device_watts IS 'TRUE = capteur puissance réel, FALSE = estimation Strava';
COMMENT ON COLUMN activity_strava_metrics.has_heartrate IS 'TRUE = données fréquence cardiaque disponibles';
COMMENT ON COLUMN activity_strava_metrics.trainer IS 'TRUE = activité sur home trainer indoor';
COMMENT ON COLUMN activity_strava_metrics.commute IS 'TRUE = trajet domicile-travail';

COMMENT ON COLUMN activity_custom_metrics.custom_tss IS 'TSS recalculé avec FTP utilisateur au lieu de estimation Strava';
COMMENT ON COLUMN activity_custom_metrics.intensity_factor IS 'IF = Normalized Power Strava / FTP utilisateur';
COMMENT ON COLUMN activity_custom_metrics.best_1min_power IS 'Estimation meilleure puissance 1min basée sur NP et durée';
COMMENT ON COLUMN activity_custom_metrics.best_1km_time IS 'Temps détecté pour distance 1km si activité correspond';

-- Statistiques pour l'optimiseur de requêtes
CREATE STATISTICS IF NOT EXISTS activity_summary_stats 
ON athlete_id, type, year, month 
FROM activity_summary;

CREATE STATISTICS IF NOT EXISTS activity_strava_metrics_stats
ON activity_id, device_watts, has_heartrate, weighted_average_watts
FROM activity_strava_metrics;

CREATE STATISTICS IF NOT EXISTS activity_custom_metrics_stats
ON athlete_id, custom_tss, intensity_factor, user_ftp
FROM activity_custom_metrics;