"""
Activity data models.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
import hashlib


@dataclass
class Activity:
    """Unified representation of an individual workout/activity."""
    id: str
    source: str  # 'garmin', 'strava', 'synthetic', 'manual'
    source_id: Optional[str] = None
    start_time: datetime = field(default_factory=datetime.now)
    sport_type: str = "run"  # 'run', 'trail_run', 'treadmill_run', 'cycling', 'other'
    title: str = "Running Activity"
    duration_seconds: float = 0.0
    moving_time_seconds: float = 0.0
    distance_meters: float = 0.0
    elevation_gain_m: float = 0.0
    elevation_loss_m: float = 0.0
    avg_hr: Optional[float] = None
    max_hr: Optional[float] = None
    avg_pace_sec_km: Optional[float] = None
    best_pace_sec_km: Optional[float] = None
    avg_cadence: Optional[float] = None  # Full SPM (steps/min), e.g. 170
    max_cadence: Optional[float] = None
    avg_power_watts: Optional[float] = None
    calories: Optional[float] = None
    aerobic_te: Optional[float] = None  # Aerobic Training Effect (0.0 - 5.0)
    anaerobic_te: Optional[float] = None  # Anaerobic Training Effect (0.0 - 5.0)
    stride_length_m: Optional[float] = None
    vertical_ratio: Optional[float] = None
    ground_contact_time_ms: Optional[float] = None
    temperature_c: Optional[float] = None
    feeling: Optional[int] = None  # 1-5 scale
    rpe: Optional[int] = None  # 1-10 scale
    notes: Optional[str] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)

    # Calculated Advanced Metrics
    trimp: Optional[float] = None
    tss: Optional[float] = None
    intensity_factor: Optional[float] = None
    efficiency_factor: Optional[float] = None  # Speed (m/min) / HR or (km/h)/HR
    aerobic_decoupling: Optional[float] = None  # Decoupling % drift (Pa:HR)
    vdot: Optional[float] = None  # Estimated Jack Daniels VDOT

    @property
    def distance_km(self) -> float:
        return self.distance_meters / 1000.0

    @property
    def distance_miles(self) -> float:
        return self.distance_meters / 1609.344

    @property
    def speed_m_s(self) -> float:
        if self.moving_time_seconds > 0:
            return self.distance_meters / self.moving_time_seconds
        elif self.duration_seconds > 0:
            return self.distance_meters / self.duration_seconds
        return 0.0

    @property
    def speed_kmh(self) -> float:
        return self.speed_m_s * 3.6

    @property
    def effective_pace_sec_km(self) -> float:
        """Returns avg_pace_sec_km or computes from moving time / distance."""
        if self.avg_pace_sec_km and self.avg_pace_sec_km > 0:
            return self.avg_pace_sec_km
        if self.distance_km > 0:
            t = self.moving_time_seconds if self.moving_time_seconds > 0 else self.duration_seconds
            return t / self.distance_km
        return 0.0

    @property
    def formatted_pace(self) -> str:
        """Returns pace formatted as mm:ss /km."""
        pace_sec = self.effective_pace_sec_km
        if pace_sec <= 0 or pace_sec > 1800:
            return "--:--"
        mins = int(pace_sec // 60)
        secs = int(pace_sec % 60)
        return f"{mins}:{secs:02d} /km"

    @property
    def formatted_duration(self) -> str:
        """Returns duration formatted as HH:MM:SS or MM:SS."""
        total_sec = int(self.duration_seconds)
        hours = total_sec // 3600
        minutes = (total_sec % 3600) // 60
        seconds = total_sec % 60
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

    @classmethod
    def generate_fingerprint_id(cls, start_time: datetime, distance_meters: float, duration_seconds: float) -> str:
        """Generates deterministic hash for deduplication."""
        time_str = start_time.strftime("%Y-%m-%d_%H:%M")
        # Round distance to nearest 50m and duration to nearest 30s to allow fuzzy match key
        dist_bucket = round(distance_meters / 50.0) * 50
        dur_bucket = round(duration_seconds / 30.0) * 30
        key = f"{time_str}_{dist_bucket}_{dur_bucket}"
        return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "source_id": self.source_id,
            "start_time": self.start_time.isoformat() if isinstance(self.start_time, datetime) else self.start_time,
            "sport_type": self.sport_type,
            "title": self.title,
            "duration_seconds": self.duration_seconds,
            "moving_time_seconds": self.moving_time_seconds,
            "distance_meters": self.distance_meters,
            "elevation_gain_m": self.elevation_gain_m,
            "elevation_loss_m": self.elevation_loss_m,
            "avg_hr": self.avg_hr,
            "max_hr": self.max_hr,
            "avg_pace_sec_km": self.avg_pace_sec_km,
            "best_pace_sec_km": self.best_pace_sec_km,
            "avg_cadence": self.avg_cadence,
            "max_cadence": self.max_cadence,
            "avg_power_watts": self.avg_power_watts,
            "calories": self.calories,
            "aerobic_te": self.aerobic_te,
            "anaerobic_te": self.anaerobic_te,
            "stride_length_m": self.stride_length_m,
            "vertical_ratio": self.vertical_ratio,
            "ground_contact_time_ms": self.ground_contact_time_ms,
            "temperature_c": self.temperature_c,
            "feeling": self.feeling,
            "rpe": self.rpe,
            "notes": self.notes,
            "trimp": self.trimp,
            "tss": self.tss,
            "intensity_factor": self.intensity_factor,
            "efficiency_factor": self.efficiency_factor,
            "aerobic_decoupling": self.aerobic_decoupling,
            "vdot": self.vdot,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Activity":
        start_time = d.get("start_time")
        if isinstance(start_time, str):
            try:
                start_time = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            except Exception:
                start_time = datetime.now()
        elif not isinstance(start_time, datetime):
            start_time = datetime.now()

        return cls(
            id=d.get("id", ""),
            source=d.get("source", "manual"),
            source_id=d.get("source_id"),
            start_time=start_time,
            sport_type=d.get("sport_type", "run"),
            title=d.get("title", "Workout"),
            duration_seconds=float(d.get("duration_seconds", 0.0) or 0.0),
            moving_time_seconds=float(d.get("moving_time_seconds", 0.0) or 0.0),
            distance_meters=float(d.get("distance_meters", 0.0) or 0.0),
            elevation_gain_m=float(d.get("elevation_gain_m", 0.0) or 0.0),
            elevation_loss_m=float(d.get("elevation_loss_m", 0.0) or 0.0),
            avg_hr=float(d["avg_hr"]) if d.get("avg_hr") is not None else None,
            max_hr=float(d["max_hr"]) if d.get("max_hr") is not None else None,
            avg_pace_sec_km=float(d["avg_pace_sec_km"]) if d.get("avg_pace_sec_km") is not None else None,
            best_pace_sec_km=float(d["best_pace_sec_km"]) if d.get("best_pace_sec_km") is not None else None,
            avg_cadence=float(d["avg_cadence"]) if d.get("avg_cadence") is not None else None,
            max_cadence=float(d["max_cadence"]) if d.get("max_cadence") is not None else None,
            avg_power_watts=float(d["avg_power_watts"]) if d.get("avg_power_watts") is not None else None,
            calories=float(d["calories"]) if d.get("calories") is not None else None,
            aerobic_te=float(d["aerobic_te"]) if d.get("aerobic_te") is not None else None,
            anaerobic_te=float(d["anaerobic_te"]) if d.get("anaerobic_te") is not None else None,
            stride_length_m=float(d["stride_length_m"]) if d.get("stride_length_m") is not None else None,
            vertical_ratio=float(d["vertical_ratio"]) if d.get("vertical_ratio") is not None else None,
            ground_contact_time_ms=float(d["ground_contact_time_ms"]) if d.get("ground_contact_time_ms") is not None else None,
            temperature_c=float(d["temperature_c"]) if d.get("temperature_c") is not None else None,
            feeling=int(d["feeling"]) if d.get("feeling") is not None else None,
            rpe=int(d["rpe"]) if d.get("rpe") is not None else None,
            notes=d.get("notes"),
            raw_data=d.get("raw_data", {}),
            trimp=float(d["trimp"]) if d.get("trimp") is not None else None,
            tss=float(d["tss"]) if d.get("tss") is not None else None,
            intensity_factor=float(d["intensity_factor"]) if d.get("intensity_factor") is not None else None,
            efficiency_factor=float(d["efficiency_factor"]) if d.get("efficiency_factor") is not None else None,
            aerobic_decoupling=float(d["aerobic_decoupling"]) if d.get("aerobic_decoupling") is not None else None,
            vdot=float(d["vdot"]) if d.get("vdot") is not None else None,
        )
