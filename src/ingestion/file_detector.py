"""
File detector to identify CSV export format (Garmin vs Strava).
"""
import io
from typing import Tuple, List, Union
import pandas as pd

from src.models.activity import Activity
from src.ingestion.garmin_parser import GarminCSVParser
from src.ingestion.strava_parser import StravaCSVParser


def detect_and_parse_csv(file_content: Union[str, bytes, io.StringIO, io.BytesIO], filename: str = "") -> Tuple[str, List[Activity]]:
    """
    Detects whether the file is Garmin Connect CSV or Strava Archive CSV and parses it.
    Returns (source_type, list_of_activities).
    """
    # Read first few lines or full dataframe header
    if isinstance(file_content, bytes):
        try:
            text = file_content.decode("utf-8")
        except UnicodeDecodeError:
            text = file_content.decode("latin-1")
        buffer = io.StringIO(text)
    elif isinstance(file_content, io.BytesIO):
        try:
            text = file_content.read().decode("utf-8")
        except UnicodeDecodeError:
            file_content.seek(0)
            text = file_content.read().decode("latin-1")
        buffer = io.StringIO(text)
    elif isinstance(file_content, str):
        buffer = io.StringIO(file_content)
    else:
        buffer = file_content

    try:
        sample_df = pd.read_csv(buffer, nrows=5)
        cols = [str(c).strip().lower() for c in sample_df.columns]
    except Exception as e:
        return "unknown", []

    # Reset buffer position
    buffer.seek(0)

    # Check for Garmin indicators
    garmin_indicators = [
        "aerobic te", "anaerobic te", "avg run cadence", "total ascent",
        "avg stride length", "avg vertical ratio", "avg ground contact time",
        "training stress score®", "best pace"
    ]
    # Check for Strava indicators
    strava_indicators = [
        "activity id", "activity name", "activity date", "elapsed time",
        "moving time", "average speed", "max speed", "elevation gain",
        "relative effort", "perceived exertion", "commute", "gear"
    ]

    garmin_score = sum(1 for ind in garmin_indicators if any(ind in c for c in cols))
    strava_score = sum(1 for ind in strava_indicators if any(ind in c for c in cols))

    # Filename hints
    fn_lower = filename.lower()
    if "garmin" in fn_lower:
        garmin_score += 3
    elif "strava" in fn_lower:
        strava_score += 3

    if garmin_score >= strava_score and garmin_score > 0:
        activities = GarminCSVParser.parse(buffer)
        return "garmin", activities
    elif strava_score > 0:
        activities = StravaCSVParser.parse(buffer)
        return "strava", activities
    else:
        # Try Garmin first, if no activities try Strava
        activities = GarminCSVParser.parse(buffer)
        if activities:
            return "garmin", activities
        buffer.seek(0)
        activities = StravaCSVParser.parse(buffer)
        return "strava" if activities else "unknown", activities
