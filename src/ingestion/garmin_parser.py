"""
Parser for Garmin Connect Activity CSV exports.
"""
import io
import re
from datetime import datetime
from typing import List, Union, Optional
import pandas as pd

from src.models.activity import Activity


def parse_duration_to_seconds(val: Union[str, float, int]) -> float:
    """Converts duration string (e.g., '01:23:45', '45:12.3', '45:12', '3600') into seconds."""
    if pd.isna(val) or val is None or val == "--" or val == "":
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    val_str = str(val).strip()
    # Remove decimal seconds if present in MM:SS.s
    parts = val_str.split(":")
    try:
        if len(parts) == 3:
            h = float(parts[0])
            m = float(parts[1])
            s = float(parts[2])
            return h * 3600 + m * 60 + s
        elif len(parts) == 2:
            m = float(parts[0])
            s = float(parts[1])
            return m * 60 + s
        elif len(parts) == 1:
            return float(parts[0])
    except Exception:
        pass
    return 0.0


def parse_pace_to_sec_km(val: Union[str, float, int]) -> Optional[float]:
    """Converts pace string (e.g., '4:45', '04:45 /km', '4:45 min/km', '7:35 /mi') to seconds per km."""
    if pd.isna(val) or val is None or val == "--" or val == "":
        return None
    if isinstance(val, (int, float)):
        return float(val)

    val_str = str(val).strip().lower()
    is_mile = "mi" in val_str or "/mi" in val_str

    # Extract mm:ss
    match = re.search(r"(\d+):(\d+(?:\.\d+)?)", val_str)
    if match:
        mins = float(match.group(1))
        secs = float(match.group(2))
        total_sec = mins * 60.0 + secs
        if is_mile:
            total_sec = total_sec / 1.609344  # convert sec/mi to sec/km
        return total_sec

    # Or pure float
    clean_num = re.sub(r"[^\d.]", "", val_str)
    if clean_num:
        try:
            return float(clean_num)
        except Exception:
            return None
    return None


def parse_distance_meters(val: Union[str, float, int]) -> float:
    """Converts distance string (e.g., '10.55', '10.55 km', '6.55 mi', '10,550 m') to meters."""
    if pd.isna(val) or val is None or val == "--" or val == "":
        return 0.0
    if isinstance(val, (int, float)):
        # If > 100, assume meters, else assume km
        v = float(val)
        return v if v > 100 else v * 1000.0

    val_str = str(val).strip().lower().replace(",", "")
    is_mile = "mi" in val_str

    clean_num = re.sub(r"[^\d.]", "", val_str)
    if not clean_num:
        return 0.0
    try:
        num = float(clean_num)
        if is_mile:
            return num * 1609.344
        if "km" in val_str or num < 100:  # standard km
            return num * 1000.0
        return num
    except Exception:
        return 0.0


def parse_clean_float(val: Any) -> Optional[float]:
    """Cleans numeric strings with commas/units into float."""
    if pd.isna(val) or val is None or val == "--" or val == "":
        return None
    if isinstance(val, (int, float)):
        return float(val)
    val_str = str(val).replace(",", "").strip()
    match = re.search(r"[-+]?\d*\.?\d+", val_str)
    if match:
        try:
            return float(match.group(0))
        except Exception:
            return None
    return None


def normalize_sport_type(raw_type: str) -> str:
    """Normalizes sport string to standard category."""
    if not raw_type:
        return "run"
    s = str(raw_type).strip().lower()
    if "trail" in s:
        return "trail_run"
    elif "treadmill" in s or "indoor" in s:
        return "treadmill_run"
    elif "run" in s or "track" in s:
        return "run"
    elif "cycl" in s or "bike" in s or "ride" in s:
        return "cycling"
    elif "walk" in s or "hike" in s:
        return "walking"
    elif "swim" in s:
        return "swimming"
    return "other"


def parse_datetime(val: Any) -> datetime:
    """Robust datetime parser for various Garmin date formats."""
    if isinstance(val, datetime):
        return val
    if pd.isna(val) or val is None:
        return datetime.now()

    val_str = str(val).strip()
    # Common Garmin formats
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%b %d, %Y %I:%M:%S %p",
        "%b %d, %Y %I:%M %p",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%m/%d/%Y %I:%M:%S %p",
        "%m/%d/%Y %H:%M:%S",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(val_str, fmt)
        except ValueError:
            pass

    try:
        return pd.to_datetime(val_str).to_pydatetime()
    except Exception:
        return datetime.now()


class GarminCSVParser:
    """Parser for Garmin Connect exported CSV files."""

    @staticmethod
    def parse(file_content: Union[str, bytes, io.StringIO, io.BytesIO]) -> List[Activity]:
        """Parses Garmin CSV content into a list of Activity objects."""
        if isinstance(file_content, bytes):
            # Try utf-8 first, fallback to latin-1
            try:
                text = file_content.decode("utf-8")
            except UnicodeDecodeError:
                text = file_content.decode("latin-1")
            df = pd.read_csv(io.StringIO(text))
        elif isinstance(file_content, str):
            df = pd.read_csv(io.StringIO(file_content))
        elif isinstance(file_content, io.BytesIO):
            try:
                text = file_content.read().decode("utf-8")
            except UnicodeDecodeError:
                file_content.seek(0)
                text = file_content.read().decode("latin-1")
            df = pd.read_csv(io.StringIO(text))
        else:
            df = pd.read_csv(file_content)

        # Normalize column names: lowercase, strip, replace spaces/underscores
        col_map = {c: c.strip().lower() for c in df.columns}
        df_norm = df.rename(columns=col_map)

        activities: List[Activity] = []

        for _, row in df_norm.iterrows():
            try:
                # Find matching columns flexibly
                sport_raw = GarminCSVParser._get_val(row, ["activity type", "type", "sport"])
                sport_type = normalize_sport_type(sport_raw or "run")

                date_val = GarminCSVParser._get_val(row, ["date", "start time", "start_time", "activity date"])
                start_time = parse_datetime(date_val)

                title = GarminCSVParser._get_val(row, ["title", "activity name", "name"]) or f"Garmin {sport_type.capitalize()}"

                distance_raw = GarminCSVParser._get_val(row, ["distance", "total distance", "dist"])
                distance_meters = parse_distance_meters(distance_raw)

                time_raw = GarminCSVParser._get_val(row, ["time", "duration", "elapsed time", "total time"])
                duration_seconds = parse_duration_to_seconds(time_raw)

                moving_time_raw = GarminCSVParser._get_val(row, ["moving time", "moving_time"])
                moving_time_seconds = parse_duration_to_seconds(moving_time_raw) if moving_time_raw else duration_seconds

                avg_hr = parse_clean_float(GarminCSVParser._get_val(row, ["avg hr", "average heart rate", "avg heart rate", "hr"]))
                max_hr = parse_clean_float(GarminCSVParser._get_val(row, ["max hr", "max heart rate", "maximum heart rate"]))

                pace_raw = GarminCSVParser._get_val(row, ["avg pace", "average pace", "pace"])
                avg_pace = parse_pace_to_sec_km(pace_raw)

                best_pace_raw = GarminCSVParser._get_val(row, ["best pace", "max pace"])
                best_pace = parse_pace_to_sec_km(best_pace_raw)

                # Cadence (Garmin sometimes gives steps/min for 1 leg or 2 legs)
                cadence_raw = parse_clean_float(GarminCSVParser._get_val(row, ["avg run cadence", "avg cadence", "cadence", "run cadence"]))
                avg_cadence = None
                if cadence_raw:
                    # If single-leg cadence (< 120), double it to full SPM
                    avg_cadence = cadence_raw * 2 if cadence_raw < 120 else cadence_raw

                max_cadence_raw = parse_clean_float(GarminCSVParser._get_val(row, ["max run cadence", "max cadence"]))
                max_cadence = (max_cadence_raw * 2 if max_cadence_raw < 120 else max_cadence_raw) if max_cadence_raw else None

                elev_gain = parse_clean_float(GarminCSVParser._get_val(row, ["total ascent", "elevation gain", "ascent", "gain"])) or 0.0
                elev_loss = parse_clean_float(GarminCSVParser._get_val(row, ["total descent", "elevation loss", "descent", "loss"])) or 0.0
                calories = parse_clean_float(GarminCSVParser._get_val(row, ["calories", "total calories", "kcal"]))
                aerobic_te = parse_clean_float(GarminCSVParser._get_val(row, ["aerobic te", "aerobic training effect", "training effect"]))
                anaerobic_te = parse_clean_float(GarminCSVParser._get_val(row, ["anaerobic te", "anaerobic training effect"]))
                stride_length = parse_clean_float(GarminCSVParser._get_val(row, ["avg stride length", "stride length"]))
                vert_ratio = parse_clean_float(GarminCSVParser._get_val(row, ["avg vertical ratio", "vertical ratio"]))
                ground_contact = parse_clean_float(GarminCSVParser._get_val(row, ["avg ground contact time", "ground contact time", "gct"]))
                temp = parse_clean_float(GarminCSVParser._get_val(row, ["avg temp", "temperature", "temp"]))
                tss = parse_clean_float(GarminCSVParser._get_val(row, ["training stress score®", "tss", "training stress score"]))

                # Generate unique ID
                activity_id = Activity.generate_fingerprint_id(start_time, distance_meters, duration_seconds)

                act = Activity(
                    id=f"garmin_{activity_id}",
                    source="garmin",
                    source_id=str(GarminCSVParser._get_val(row, ["activity id", "id"]) or ""),
                    start_time=start_time,
                    sport_type=sport_type,
                    title=str(title),
                    duration_seconds=duration_seconds,
                    moving_time_seconds=moving_time_seconds,
                    distance_meters=distance_meters,
                    elevation_gain_m=elev_gain,
                    elevation_loss_m=elev_loss,
                    avg_hr=avg_hr,
                    max_hr=max_hr,
                    avg_pace_sec_km=avg_pace,
                    best_pace_sec_km=best_pace,
                    avg_cadence=avg_cadence,
                    max_cadence=max_cadence,
                    calories=calories,
                    aerobic_te=aerobic_te,
                    anaerobic_te=anaerobic_te,
                    stride_length_m=stride_length,
                    vertical_ratio=vert_ratio,
                    ground_contact_time_ms=ground_contact,
                    temperature_c=temp,
                    tss=tss,
                    raw_data={k: v for k, v in row.to_dict().items() if pd.notna(v)},
                )
                activities.append(act)
            except Exception as e:
                # Log or skip malformed row
                continue

        return activities

    @staticmethod
    def _get_val(row: pd.Series, possible_keys: List[str]) -> Any:
        for k in possible_keys:
            if k in row.index and pd.notna(row[k]):
                return row[k]
        return None
