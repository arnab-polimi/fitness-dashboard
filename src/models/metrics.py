"""
Metric data models for training load, risk assessment, and fitness insights.
"""
from dataclasses import dataclass, field
from datetime import date
from typing import List, Dict, Any, Optional


@dataclass
class DailyLoad:
    """Daily aggregated training load and fitness metrics."""
    date: date
    distance_meters: float = 0.0
    duration_seconds: float = 0.0
    activity_count: int = 0
    total_tss: float = 0.0
    total_trimp: float = 0.0
    ctl: float = 0.0  # Chronic Training Load (Fitness - 42d EWMA)
    atl: float = 0.0  # Acute Training Load (Fatigue - 7d EWMA)
    tsb: float = 0.0  # Training Stress Balance (Form = CTL - ATL)
    acwr: Optional[float] = None  # Acute:Chronic Workload Ratio (7d vs 28d)
    ramp_rate_ctl: Optional[float] = None  # 7-day change in CTL
    monotony: Optional[float] = None  # Foster's Monotony
    strain: Optional[float] = None  # Foster's Strain
    efficiency_factor: Optional[float] = None

    @property
    def distance_km(self) -> float:
        return self.distance_meters / 1000.0

    @property
    def form_state(self) -> str:
        """Form classification based on TSB."""
        if self.tsb > 25:
            return "Transition / Loss of Fitness"
        elif 10 <= self.tsb <= 25:
            return "Fresh / Race Ready"
        elif -10 <= self.tsb < 10:
            return "Neutral / Productive"
        elif -30 <= self.tsb < -10:
            return "Optimal Training / Fatigue"
        else:
            return "High Fatigue / Overreaching"

    @property
    def form_color(self) -> str:
        if self.tsb > 25:
            return "#3B82F6"  # Blue
        elif 10 <= self.tsb <= 25:
            return "#10B981"  # Emerald Green
        elif -10 <= self.tsb < 10:
            return "#4D71B2"  # Blue-slate
        elif -30 <= self.tsb < -10:
            return "#F59E0B"  # Amber
        else:
            return "#EF4444"  # Red


@dataclass
class RiskSignal:
    """Individual signal contributing to the multi-signal injury risk evaluation."""
    name: str
    weight: float  # e.g., 0.25
    raw_value: float
    score: float  # 0 to 100 (0 = low stress, 100 = extreme stress)
    status: str  # 'Optimal', 'Caution', 'Elevated', 'High'
    status_color: str  # Hex color
    summary: str
    detailed_evidence: str
    recommendation: str


@dataclass
class RiskReport:
    """Multi-signal composite Training Stress & Injury Risk Assessment."""
    composite_score: float  # 0 to 100
    overall_status: str  # 'Low / Optimal', 'Moderate Load', 'Elevated Strain', 'High Injury Risk'
    status_color: str
    acwr_value: float
    ramp_rate_7d: float
    monotony_7d: float
    strain_7d: float
    consecutive_hard_days: int
    signals: List[RiskSignal] = field(default_factory=list)
    key_takeaways: List[str] = field(default_factory=list)
    actionable_guidance: List[str] = field(default_factory=list)
    disclaimer: str = (
        " DISCLAIMER: This Training Stress & Injury-Risk Indicator is an algorithmic analysis "
        "of physiological training load, biomechanical variance, and fatigue patterns. It is NOT "
        "a medical diagnostic tool or clinical prediction. Always listen to your body and consult "
        "a sports medicine professional or coach for pain or medical advice."
    )


@dataclass
class RacePrediction:
    """Projected race time and pace for target distance."""
    distance_name: str  # '5K', '10K', 'Half Marathon', 'Marathon'
    distance_km: float
    predicted_time_seconds: float
    predicted_pace_sec_km: float
    confidence_level: str  # 'High', 'Moderate', 'Preliminary'
    basis: str  # 'VDOT Peak + CTL Adjusted'

    @property
    def formatted_time(self) -> str:
        sec = int(self.predicted_time_seconds)
        h = sec // 3600
        m = (sec % 3600) // 60
        s = sec % 60
        if h > 0:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m}:{s:02d}"

    @property
    def formatted_pace(self) -> str:
        mins = int(self.predicted_pace_sec_km // 60)
        secs = int(self.predicted_pace_sec_km % 60)
        return f"{mins}:{secs:02d} /km"


@dataclass
class FitnessInsight:
    """Narrative insight explaining fitness and load changes."""
    category: str  # 'adaptation', 'fatigue', 'efficiency', 'volume', 'race_readiness', 'risk'
    title: str
    explanation: str
    metric_evidence: str
    action_item: str
    impact: str  # 'positive', 'neutral', 'warning', 'critical'
    icon: str = ""
