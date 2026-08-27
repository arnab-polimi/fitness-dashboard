"""
Realistic Synthetic Development Data Generator.
Clearly marked and labeled as [SYNTHETIC DEV DATA] for testing, onboarding, and local development.
"""
import os
import random
import io
from datetime import datetime, timedelta, date
from typing import List, Tuple
import pandas as pd

from src.models.activity import Activity
from src.models.user_profile import UserProfile
from src.analytics.training_load import compute_activity_load


def generate_synthetic_training_history(
    days: int = 180,
    user_profile: Optional[UserProfile] = None,
    seed: int = 42,
) -> List[Activity]:
    """
    Generates a realistic 6-month progressive training periodization:
    - Base Building phase (Weeks 1-8)
    - Build & Tempo phase (Weeks 9-16)
    - Peak & Race simulation (Weeks 17-22)
    - Taper & Recovery (Weeks 23-26)
    """
    random.seed(seed)
    profile = user_profile or UserProfile()

    activities: List[Activity] = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    current_date = start_date

    # Athlete baseline capabilities
    base_easy_pace = 330.0  # 5:30 min/km
    base_tempo_pace = 270.0  # 4:30 min/km
    base_interval_pace = 240.0  # 4:00 min/km
    base_easy_hr = 142.0

    day_idx = 0

    while current_date <= end_date:
        weekday = current_date.weekday()  # 0=Monday, 6=Sunday
        day_idx += 1

        # Fitness adaptation factor (gradually gets faster and more efficient over 180 days)
        fitness_progress = (day_idx / float(days)) * 0.08  # ~8% improvement
        current_easy_pace = base_easy_pace * (1.0 - fitness_progress)
        current_tempo_pace = base_tempo_pace * (1.0 - fitness_progress)
        current_interval_pace = base_interval_pace * (1.0 - fitness_progress)

        # Weekly Periodization Schedule:
        # Monday: Rest or very light recovery jog (3-5km)
        # Tuesday: Interval workout (8-11km)
        # Wednesday: Easy aerobic run (8-12km)
        # Thursday: Tempo / Threshold run (9-13km)
        # Friday: Rest or Easy jog (5-7km)
        # Saturday: Long Run (16-26km)
        # Sunday: Easy recovery run (6-10km)

        session_type = None
        dist_km = 0.0
        target_pace = current_easy_pace
        target_hr = base_easy_hr
        target_cadence = 174.0

        if weekday == 0:  # Mon
            if random.random() < 0.6:
                # Full Rest day
                current_date += timedelta(days=1)
                continue
            else:
                session_type = "Easy Recovery Run"
                dist_km = random.uniform(4.0, 6.0)
                target_pace = current_easy_pace + 20.0
                target_hr = 132.0 + random.uniform(-3, 3)
                target_cadence = 168.0

        elif weekday == 1:  # Tue - Intervals
            session_type = "Track / VO2max Intervals"
            dist_km = random.uniform(8.0, 11.5)
            target_pace = current_interval_pace + random.uniform(-5, 5)
            target_hr = 168.0 + random.uniform(-2, 4)
            target_cadence = 182.0 + random.uniform(-2, 3)

        elif weekday == 2:  # Wed - Easy Aerobic
            session_type = "Aerobic Base Run"
            dist_km = random.uniform(8.0, 12.0)
            target_pace = current_easy_pace + random.uniform(-8, 8)
            target_hr = 140.0 + random.uniform(-4, 4)
            target_cadence = 173.0

        elif weekday == 3:  # Thu - Tempo / Threshold
            session_type = "Threshold Tempo Workout"
            dist_km = random.uniform(9.0, 13.0)
            target_pace = current_tempo_pace + random.uniform(-5, 5)
            target_hr = 162.0 + random.uniform(-3, 3)
            target_cadence = 178.0

        elif weekday == 4:  # Fri - Rest / Easy
            if random.random() < 0.5:
                # Rest day
                current_date += timedelta(days=1)
                continue
            else:
                session_type = "Easy Shakeout Run"
                dist_km = random.uniform(5.0, 7.5)
                target_pace = current_easy_pace + 15.0
                target_hr = 135.0
                target_cadence = 170.0

        elif weekday == 5:  # Sat - Long Run
            session_type = "Aerobic Long Run"
            dist_km = random.uniform(16.0, 24.0)
            target_pace = current_easy_pace + random.uniform(-3, 10)
            target_hr = 145.0 + random.uniform(-3, 4)
            target_cadence = 174.0

        elif weekday == 6:  # Sun - Recovery
            session_type = "Sunday Recovery Run"
            dist_km = random.uniform(6.0, 9.0)
            target_pace = current_easy_pace + 18.0
            target_hr = 134.0
            target_cadence = 170.0

        if dist_km > 0:
            duration_sec = dist_km * target_pace
            start_hour = 6 if weekday in [5, 6] else 7
            start_time = current_date.replace(hour=start_hour, minute=random.randint(5, 45), second=0)

            # Physiological metrics
            elev_gain = round(dist_km * random.uniform(4.0, 12.0), 1)
            calories = round(dist_km * profile.weight_kg * 0.95, 0)
            aerobic_te = round(min(5.0, max(1.5, (duration_sec / 3600.0) * (target_hr / 140.0) * 2.8)), 1)
            anaerobic_te = 2.8 if "Interval" in session_type else (1.2 if "Threshold" in session_type else 0.1)

            # Ground contact & vertical ratio
            gct = round(240.0 - (target_cadence - 170) * 1.5 + random.uniform(-5, 5), 1)
            vert_ratio = round(7.2 + random.uniform(-0.4, 0.4), 1)
            stride_len = round(1000.0 / (target_cadence * (target_pace / 60.0)), 2)

            act_id = f"synth_{start_time.strftime('%Y%m%d_%H%M')}"
            title = f"[SYNTHETIC DEV DATA] {session_type}"

            act = Activity(
                id=act_id,
                source="synthetic",
                source_id=f"sim_{day_idx}",
                start_time=start_time,
                sport_type="run",
                title=title,
                duration_seconds=round(duration_sec, 1),
                moving_time_seconds=round(duration_sec * 0.98, 1),
                distance_meters=round(dist_km * 1000.0, 1),
                elevation_gain_m=elev_gain,
                elevation_loss_m=elev_gain,
                avg_hr=round(target_hr, 1),
                max_hr=round(target_hr + random.uniform(14, 22), 1),
                avg_pace_sec_km=round(target_pace, 1),
                best_pace_sec_km=round(target_pace * 0.85, 1),
                avg_cadence=round(target_cadence, 1),
                max_cadence=round(target_cadence + 12.0, 1),
                calories=calories,
                aerobic_te=aerobic_te,
                anaerobic_te=anaerobic_te,
                stride_length_m=stride_len,
                vertical_ratio=vert_ratio,
                ground_contact_time_ms=gct,
                temperature_c=round(16.0 + random.uniform(-5, 8), 1),
            )
            act = compute_activity_load(act, profile)
            activities.append(act)

        current_date += timedelta(days=1)

    return activities


def generate_sample_garmin_and_strava_csvs(output_dir: str) -> Tuple[str, str]:
    """Generates realistic Garmin and Strava sample CSV files for testing file import."""
    os.makedirs(output_dir, exist_ok=True)
    garmin_path = os.path.join(output_dir, "sample_garmin_activities.csv")
    strava_path = os.path.join(output_dir, "sample_strava_activities.csv")

    activities = generate_synthetic_training_history(days=90)

    # 1. Garmin CSV Export Format
    garmin_rows = []
    for a in activities:
        # Garmin time format: HH:MM:SS
        dur_str = a.formatted_duration
        pace_mins = int(a.effective_pace_sec_km // 60)
        pace_secs = int(a.effective_pace_sec_km % 60)
        pace_str = f"{pace_mins}:{pace_secs:02d}"

        garmin_rows.append({
            "Activity Type": "Running",
            "Date": a.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "Favorite": "false",
            "Title": f"[SYNTHETIC DEV DATA] Garmin Run - {a.distance_km:.1f}k",
            "Distance": f"{a.distance_km:.2f}",
            "Calories": int(a.calories or 500),
            "Time": dur_str,
            "Avg HR": int(a.avg_hr or 145),
            "Max HR": int(a.max_hr or 170),
            "Aerobic TE": a.aerobic_te or 2.5,
            "Anaerobic TE": a.anaerobic_te or 0.2,
            "Avg Run Cadence": int(a.avg_cadence or 172),
            "Max Run Cadence": int(a.max_cadence or 185),
            "Avg Pace": pace_str,
            "Best Pace": "3:45",
            "Total Ascent": int(a.elevation_gain_m),
            "Total Descent": int(a.elevation_loss_m),
            "Avg Stride Length": a.stride_length_m or 1.20,
            "Avg Vertical Ratio": a.vertical_ratio or 7.5,
            "Avg Ground Contact Time": int(a.ground_contact_time_ms or 235),
            "Training Stress Score®": int(a.tss or 50),
        })
    pd.DataFrame(garmin_rows).to_csv(garmin_path, index=False)

    # 2. Strava CSV Export Format (includes some overlapping runs + custom titles)
    strava_rows = []
    for i, a in enumerate(activities):
        # Introduce slight timestamp or distance variation to test deduplication
        is_dup = (i % 2 == 0)
        st_date = a.start_time if is_dup else (a.start_time + timedelta(minutes=2))
        dist_m = a.distance_meters if is_dup else (a.distance_meters + random.uniform(-50, 50))
        speed_m_s = dist_m / a.duration_seconds if a.duration_seconds > 0 else 3.2

        strava_rows.append({
            "Activity ID": 1000000000 + i,
            "Activity Date": st_date.strftime("%b %d, %Y, %I:%M:%S %p"),
            "Activity Name": f"[SYNTHETIC DEV DATA] Morning {a.distance_km:.1f}K Community Session",
            "Activity Type": "Run",
            "Activity Description": "Controlled aerobic effort, felt smooth throughout.",
            "Elapsed Time": int(a.duration_seconds),
            "Moving Time": int(a.moving_time_seconds),
            "Distance": round(dist_m, 1),
            "Max Speed": round(speed_m_s * 1.25, 2),
            "Average Speed": round(speed_m_s, 2),
            "Elevation Gain": round(a.elevation_gain_m, 1),
            "Elevation Loss": round(a.elevation_loss_m, 1),
            "Average Heart Rate": round(a.avg_hr or 145, 1),
            "Max Heart Rate": round(a.max_hr or 170, 1),
            "Average Cadence": round((a.avg_cadence or 172) / 2.0, 1),  # single-leg RPM
            "Average Watts": round(a.avg_power_watts or 230, 0),
            "Calories": round(a.calories or 500, 0),
            "Relative Effort": round(a.tss or 50, 0),
            "Perceived Exertion": 5,
        })
    pd.DataFrame(strava_rows).to_csv(strava_path, index=False)

    return garmin_path, strava_path
