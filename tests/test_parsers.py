"""
Unit tests for Garmin and Strava CSV parsers and auto-detection.
"""
import io
import pytest
from datetime import datetime

from src.ingestion.garmin_parser import (
    GarminCSVParser,
    parse_duration_to_seconds,
    parse_pace_to_sec_km,
    parse_distance_meters,
)
from src.ingestion.strava_parser import StravaCSVParser
from src.ingestion.file_detector import detect_and_parse_csv


def test_garmin_duration_parser():
    assert parse_duration_to_seconds("01:20:30") == 4830.0
    assert parse_duration_to_seconds("45:15") == 2715.0
    assert parse_duration_to_seconds("1800") == 1800.0
    assert parse_duration_to_seconds("--") == 0.0
    assert parse_duration_to_seconds(None) == 0.0


def test_garmin_pace_parser():
    assert parse_pace_to_sec_km("4:30") == 270.0
    assert parse_pace_to_sec_km("04:30 /km") == 270.0
    # Miles pace conversion
    pace_mi = parse_pace_to_sec_km("7:14 /mi")
    assert pace_mi is not None
    assert 260.0 <= pace_mi <= 280.0


def test_garmin_distance_parser():
    assert parse_distance_meters("10.50") == 10500.0
    assert parse_distance_meters("10.50 km") == 10500.0
    assert parse_distance_meters("10,500") == 10500.0
    # Miles conversion
    dist_m = parse_distance_meters("6.2 mi")
    assert 9900.0 <= dist_m <= 10100.0


def test_garmin_csv_parsing():
    sample_csv = """Activity Type,Date,Title,Distance,Calories,Time,Avg HR,Max HR,Aerobic TE,Avg Run Cadence,Avg Pace
Running,2026-08-20 07:00:00,Morning Tempo,10.00,650,00:45:00,160,175,3.8,176,4:30
"""
    acts = GarminCSVParser.parse(sample_csv)
    assert len(acts) == 1
    act = acts[0]
    assert act.source == "garmin"
    assert act.sport_type == "run"
    assert act.distance_meters == 10000.0
    assert act.duration_seconds == 2700.0
    assert act.avg_hr == 160.0
    assert act.avg_cadence == 176.0
    assert act.aerobic_te == 3.8


def test_strava_csv_parsing():
    sample_csv = """Activity ID,Activity Date,Activity Name,Activity Type,Elapsed Time,Moving Time,Distance,Average Speed,Average Heart Rate,Average Cadence
123456789,"Aug 20, 2026, 07:00:00 AM",Community 10k,Run,2700,2650,10000,3.77,160,88
"""
    acts = StravaCSVParser.parse(sample_csv)
    assert len(acts) == 1
    act = acts[0]
    assert act.source == "strava"
    assert act.source_id == "123456789"
    assert act.title == "Community 10k"
    assert act.distance_meters == 10000.0
    assert act.avg_hr == 160.0
    # Single-leg cadence (88) converted to full SPM (176)
    assert act.avg_cadence == 176.0


def test_file_detector():
    garmin_content = "Activity Type,Date,Distance,Time,Avg HR,Aerobic TE\nRunning,2026-08-01,10,45:00,150,3.0"
    src_type, acts = detect_and_parse_csv(garmin_content, "Garmin_Export.csv")
    assert src_type == "garmin"
    assert len(acts) == 1

    strava_content = "Activity ID,Activity Date,Activity Name,Activity Type,Distance,Elapsed Time\n111,2026-08-01,Run,Run,10000,2700"
    src_type2, acts2 = detect_and_parse_csv(strava_content, "activities.csv")
    assert src_type2 == "strava"
    assert len(acts2) == 1
