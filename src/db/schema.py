"""
Database Schema definitions for SQLite / DuckDB.
"""

ACTIVITIES_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS activities (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    source_id TEXT,
    start_time TIMESTAMP NOT NULL,
    sport_type TEXT NOT NULL,
    title TEXT,
    duration_seconds REAL DEFAULT 0.0,
    moving_time_seconds REAL DEFAULT 0.0,
    distance_meters REAL DEFAULT 0.0,
    elevation_gain_m REAL DEFAULT 0.0,
    elevation_loss_m REAL DEFAULT 0.0,
    avg_hr REAL,
    max_hr REAL,
    avg_pace_sec_km REAL,
    best_pace_sec_km REAL,
    avg_cadence REAL,
    max_cadence REAL,
    avg_power_watts REAL,
    calories REAL,
    aerobic_te REAL,
    anaerobic_te REAL,
    stride_length_m REAL,
    vertical_ratio REAL,
    ground_contact_time_ms REAL,
    temperature_c REAL,
    feeling INTEGER,
    rpe INTEGER,
    notes TEXT,
    trimp REAL,
    tss REAL,
    intensity_factor REAL,
    efficiency_factor REAL,
    aerobic_decoupling REAL,
    vdot REAL,
    raw_data TEXT
);
"""

ACTIVITIES_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_activities_start_time ON activities(start_time);",
    "CREATE INDEX IF NOT EXISTS idx_activities_sport_type ON activities(sport_type);",
    "CREATE INDEX IF NOT EXISTS idx_activities_source ON activities(source);",
]

USER_PROFILE_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id TEXT PRIMARY KEY,
    name TEXT,
    gender TEXT,
    age INTEGER,
    weight_kg REAL,
    resting_hr INTEGER,
    max_hr INTEGER,
    lthr INTEGER,
    threshold_pace_sec_km REAL,
    ftp_watts REAL,
    units TEXT,
    target_race_distance_km REAL,
    target_race_date TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

DAILY_METRICS_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS daily_metrics (
    date DATE PRIMARY KEY,
    distance_meters REAL,
    duration_seconds REAL,
    activity_count INTEGER,
    total_tss REAL,
    total_trimp REAL,
    ctl REAL,
    atl REAL,
    tsb REAL,
    acwr REAL,
    ramp_rate_ctl REAL,
    monotony REAL,
    strain REAL,
    efficiency_factor REAL
);
"""

DAILY_HEALTH_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS daily_health (
    date DATE PRIMARY KEY,
    resting_hr REAL,
    hr_min REAL,
    hr_max REAL,
    stress_avg REAL,
    steps INTEGER,
    sleep_duration_seconds REAL,
    deep_sleep_seconds REAL,
    light_sleep_seconds REAL,
    rem_sleep_seconds REAL,
    sleep_score REAL,
    weight_kg REAL,
    calories_total REAL
);
"""
