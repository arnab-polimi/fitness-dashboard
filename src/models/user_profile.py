"""
User Profile and physiological configuration models.
"""
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class UserProfile:
    """User physiological profile for personalized training metrics calculation."""
    user_id: str = "default_user"
    name: str = "Runner"
    gender: str = "male"  # 'male' or 'female' (influences Banister TRIMP exponent)
    age: int = 30
    weight_kg: float = 70.0
    resting_hr: int = 50
    max_hr: int = 190
    lthr: int = 168  # Lactate Threshold Heart Rate
    threshold_pace_sec_km: float = 270.0  # 4:30 min/km (Threshold / vVO2max pace)
    ftp_watts: Optional[float] = 250.0  # Optional running power FTP
    units: str = "metric"  # 'metric' (km, min/km) or 'imperial' (miles, min/mile)
    target_race_distance_km: Optional[float] = 21.0975  # e.g., Half Marathon
    target_race_date: Optional[str] = None

    # Heart rate zones (expressed as % of Max HR or HR Reserve / Karvonen)
    hr_zones: Dict[str, tuple] = field(default_factory=lambda: {
        "Zone 1 (Recovery)": (0.50, 0.60),
        "Zone 2 (Aerobic Base)": (0.60, 0.70),
        "Zone 3 (Tempo)": (0.70, 0.80),
        "Zone 4 (Threshold)": (0.80, 0.90),
        "Zone 5 (Anaerobic/VO2max)": (0.90, 1.00),
    })

    def get_hr_reserve(self) -> int:
        """Heart Rate Reserve (HRR) = Max HR - Resting HR."""
        return max(1, self.max_hr - self.resting_hr)

    def get_hr_at_intensity(self, fractional_intensity: float) -> float:
        """Karvonen Heart Rate = Resting HR + (HRR * intensity)."""
        return self.resting_hr + (self.get_hr_reserve() * fractional_intensity)

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "name": self.name,
            "gender": self.gender,
            "age": self.age,
            "weight_kg": self.weight_kg,
            "resting_hr": self.resting_hr,
            "max_hr": self.max_hr,
            "lthr": self.lthr,
            "threshold_pace_sec_km": self.threshold_pace_sec_km,
            "ftp_watts": self.ftp_watts,
            "units": self.units,
            "target_race_distance_km": self.target_race_distance_km,
            "target_race_date": self.target_race_date,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UserProfile":
        return cls(
            user_id=data.get("user_id", "default_user"),
            name=data.get("name", "Runner"),
            gender=data.get("gender", "male"),
            age=int(data.get("age", 30)),
            weight_kg=float(data.get("weight_kg", 70.0)),
            resting_hr=int(data.get("resting_hr", 50)),
            max_hr=int(data.get("max_hr", 190)),
            lthr=int(data.get("lthr", 168)),
            threshold_pace_sec_km=float(data.get("threshold_pace_sec_km", 270.0)),
            ftp_watts=float(data["ftp_watts"]) if data.get("ftp_watts") is not None else 250.0,
            units=data.get("units", "metric"),
            target_race_distance_km=float(data["target_race_distance_km"]) if data.get("target_race_distance_km") is not None else None,
            target_race_date=data.get("target_race_date"),
        )
