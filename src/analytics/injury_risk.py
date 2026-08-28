"""
Transparent Multi-Signal Training-Stress & Injury-Risk Assessment Engine.
Clearly labeled as a training-load risk indicator, NOT a medical prediction.
"""
from typing import List, Optional
import numpy as np

from src.models.activity import Activity
from src.models.metrics import DailyLoad, RiskSignal, RiskReport


class InjuryRiskEngine:
    """
    Evaluates physiological load distribution across multiple independent signals
    to calculate a transparent training stress & injury risk indicator.
    """

    @classmethod
    def evaluate(
        cls,
        daily_loads: List[DailyLoad],
        activities: List[Activity],
    ) -> RiskReport:
        """
        Computes composite training stress score and signal breakdowns.
        """
        if not daily_loads:
            return cls._default_empty_report()

        # Get latest daily metrics
        latest_day = daily_loads[-1]
        recent_7_days = daily_loads[-7:] if len(daily_loads) >= 7 else daily_loads
        recent_28_days = daily_loads[-28:] if len(daily_loads) >= 28 else daily_loads

        # 1. ACWR Signal (Weight: 30%)
        acwr_val = latest_day.acwr or 1.0
        acwr_signal = cls._evaluate_acwr(acwr_val)

        # 2. Ramp Rate Signal (Weight: 20%)
        ramp_rate = latest_day.ramp_rate_ctl or 0.0
        ramp_signal = cls._evaluate_ramp_rate(ramp_rate)

        # 3. Monotony & Strain Signal (Weight: 20%)
        monotony = latest_day.monotony or 1.0
        strain = latest_day.strain or 100.0
        monotony_signal = cls._evaluate_monotony(monotony, strain)

        # 4. Consecutive Hard Days Signal (Weight: 15%)
        consec_hard = cls._calculate_consecutive_hard_days(daily_loads)
        consec_signal = cls._evaluate_consecutive_hard_days(consec_hard)

        # 5. Biomechanical Cadence & Decoupling Anomaly Signal (Weight: 15%)
        biomech_signal = cls._evaluate_biomechanical_fatigue(activities)

        signals = [
            acwr_signal,
            ramp_signal,
            monotony_signal,
            consec_signal,
            biomech_signal,
        ]

        # Calculate composite score (0 to 100)
        composite_score = sum(s.score * s.weight for s in signals)
        composite_score = round(min(100.0, max(0.0, composite_score)), 1)

        # Determine overall status and color
        if composite_score < 25:
            overall_status = "Optimal Load / Low Stress"
            status_color = "#10B981"  # Neon Emerald
        elif composite_score < 50:
            overall_status = "Productive Build / Moderate Stress"
            status_color = "#4D71B2"  # Blue-slate
        elif composite_score < 75:
            overall_status = "Caution / Elevated Load Ramp"
            status_color = "#F59E0B"  # Amber
        else:
            overall_status = "High Stress / Overreaching Risk"
            status_color = "#EF4444"  # Red

        # Generate key takeaways & actionable guidance
        takeaways, guidance = cls._generate_takeaways_and_guidance(signals, composite_score)

        return RiskReport(
            composite_score=composite_score,
            overall_status=overall_status,
            status_color=status_color,
            acwr_value=acwr_val,
            ramp_rate_7d=ramp_rate,
            monotony_7d=monotony,
            strain_7d=strain,
            consecutive_hard_days=consec_hard,
            signals=signals,
            key_takeaways=takeaways,
            actionable_guidance=guidance,
        )

    @classmethod
    def _evaluate_acwr(cls, acwr: float) -> RiskSignal:
        weight = 0.30
        if 0.80 <= acwr <= 1.30:
            score = 10.0
            status = "Optimal"
            color = "#10B981"
            summary = f"ACWR is {acwr:.2f} (Within the 0.8–1.3 sweet spot)."
            evidence = "Your acute (7-day) workload is well-proportioned to your chronic (28-day) fitness base."
            rec = "Maintain current progressive overload structure."
        elif 1.30 < acwr <= 1.50:
            score = 55.0
            status = "Caution"
            color = "#F59E0B"
            summary = f"ACWR is {acwr:.2f} (Elevated training surge)."
            evidence = "Acute load has increased faster than the 28-day baseline, increasing soft-tissue vulnerability."
            rec = "Avoid stacking high-intensity speedwork; keep next runs at easy aerobic pace."
        elif acwr > 1.50:
            score = 90.0
            status = "High"
            color = "#EF4444"
            summary = f"ACWR is {acwr:.2f} (High spike in acute volume)."
            evidence = "Workload exceeds safe progression thresholds (>1.5), strongly correlated with overuse injuries."
            rec = "Implement an immediate recovery or de-load session to allow systemic adaptation."
        else:  # acwr < 0.80
            score = 25.0
            status = "Low Load"
            color = "#3B82F6"
            summary = f"ACWR is {acwr:.2f} (Training volume is decreasing or tapering)."
            evidence = "Acute load is lower than chronic base. Great for race tapering or recovery phases."
            rec = "If not tapering for a race, resume steady gradual volume increases."

        return RiskSignal(
            name="Acute:Chronic Workload Ratio (ACWR)",
            weight=weight,
            raw_value=acwr,
            score=score,
            status=status,
            status_color=color,
            summary=summary,
            detailed_evidence=evidence,
            recommendation=rec,
        )

    @classmethod
    def _evaluate_ramp_rate(cls, ramp_rate: float) -> RiskSignal:
        weight = 0.20
        if ramp_rate <= 4.0:
            score = 10.0
            status = "Optimal"
            color = "#10B981"
            summary = f"Weekly CTL gain is +{ramp_rate:.1f} TSS/week (Sustainable)."
            evidence = "Aerobic fitness accumulation is progressing within safe physiological adaptation limits (<5 TSS/wk)."
            rec = "Continue standard progressive overload."
        elif 4.0 < ramp_rate <= 7.5:
            score = 50.0
            status = "Caution"
            color = "#F59E0B"
            summary = f"Weekly CTL gain is +{ramp_rate:.1f} TSS/week (Aggressive)."
            evidence = "Fitness build is aggressive. While manageable short-term, prolonged ramps fatigue tendons and connective tissue."
            rec = "Plan a lighter recovery week within the next 7-10 days."
        else:
            score = 85.0
            status = "High"
            color = "#EF4444"
            summary = f"Weekly CTL gain is +{ramp_rate:.1f} TSS/week (Excessive spike)."
            evidence = "Ramp rate exceeds 8.0 TSS/week. Cardiovascular capacity often outpaces connective tissue adaptation."
            rec = "Cap weekly mileage jumps to 10% maximum to protect joints and tendons."

        return RiskSignal(
            name="7-Day Fitness Ramp Rate (CTL)",
            weight=weight,
            raw_value=ramp_rate,
            score=score,
            status=status,
            status_color=color,
            summary=summary,
            detailed_evidence=evidence,
            recommendation=rec,
        )

    @classmethod
    def _evaluate_monotony(cls, monotony: float, strain: float) -> RiskSignal:
        weight = 0.20
        if monotony < 1.5:
            score = 15.0
            status = "Optimal"
            color = "#10B981"
            summary = f"Training Monotony is {monotony:.2f} (Well polarized)."
            evidence = "Good daily variation between hard workout days, easy recovery runs, and rest days."
            rec = "Keep hard days hard and easy days genuinely easy."
        elif 1.5 <= monotony <= 2.0:
            score = 55.0
            status = "Caution"
            color = "#F59E0B"
            summary = f"Training Monotony is {monotony:.2f} (Repetitive daily load)."
            evidence = "Daily training stress is uniform. Without polarized easy/hard oscillation, recovery is compromised."
            rec = "Introduce a complete rest day or very light active recovery jog."
        else:
            score = 85.0
            status = "High"
            color = "#EF4444"
            summary = f"Training Monotony is {monotony:.2f} (Extreme uniformity)."
            evidence = "Monotony > 2.0 indicates chronic daily loading without restorative recovery valleys."
            rec = "Schedule immediate low-intensity recovery days to prevent systemic overreaching."

        return RiskSignal(
            name="Foster's Training Monotony & Strain",
            weight=weight,
            raw_value=monotony,
            score=score,
            status=status,
            status_color=color,
            summary=summary,
            detailed_evidence=evidence,
            recommendation=rec,
        )

    @classmethod
    def _calculate_consecutive_hard_days(cls, daily_loads: List[DailyLoad]) -> int:
        """Counts consecutive days prior to today with TSS >= 60."""
        count = 0
        for dl in reversed(daily_loads):
            if dl.total_tss >= 60.0:
                count += 1
            else:
                break
        return count

    @classmethod
    def _evaluate_consecutive_hard_days(cls, consec_days: int) -> RiskSignal:
        weight = 0.15
        if consec_days <= 1:
            score = 10.0
            status = "Optimal"
            color = "#10B981"
            summary = f"{consec_days} consecutive high-load day(s)."
            evidence = "High-stress sessions are properly spaced with recovery intervals."
            rec = "Ready for scheduled quality or long run workouts."
        elif consec_days == 2:
            score = 50.0
            status = "Caution"
            color = "#F59E0B"
            summary = f"2 consecutive hard training days."
            evidence = "Glycogen depletion and muscular micro-tears accumulate after back-to-back taxing sessions."
            rec = "Prioritize an easy Zone 1/2 run or active mobility session tomorrow."
        else:
            score = 90.0
            status = "High"
            color = "#EF4444"
            summary = f"{consec_days} consecutive hard training days without recovery."
            evidence = "3+ back-to-back demanding days dramatically elevate injury risk and blunt training adaptations."
            rec = "Mandatory full rest day or cross-training recovery recommended."

        return RiskSignal(
            name="Consecutive Hard Training Days",
            weight=weight,
            raw_value=float(consec_days),
            score=score,
            status=status,
            status_color=color,
            summary=summary,
            detailed_evidence=evidence,
            recommendation=rec,
        )

    @classmethod
    def _evaluate_biomechanical_fatigue(cls, activities: List[Activity]) -> RiskSignal:
        weight = 0.15
        recent_runs = [a for a in sorted(activities, key=lambda a: a.start_time, reverse=True) if a.sport_type in ["run", "trail_run"]][:10]

        if len(recent_runs) < 3:
            return RiskSignal(
                name="Biomechanical Cadence & Decoupling",
                weight=weight,
                raw_value=0.0,
                score=15.0,
                status="Optimal",
                status_color="#10B981",
                summary="Cadence and cardiovascular decoupling are stable.",
                detailed_evidence="No significant biomechanical breakdown detected in recent activities.",
                recommendation="Maintain focus on tall posture and light, quick cadence (~170-180 spm).",
            )

        cadences = [r.avg_cadence for r in recent_runs if r.avg_cadence and r.avg_cadence > 120]
        decouplings = [r.aerobic_decoupling for r in recent_runs if r.aerobic_decoupling is not None]

        high_decoupling_count = sum(1 for d in decouplings[:3] if d > 8.0)
        cadence_drop = False
        if len(cadences) >= 4:
            recent_avg_cad = np.mean(cadences[:2])
            baseline_cad = np.mean(cadences[2:])
            if baseline_cad > 0 and (baseline_cad - recent_avg_cad) / baseline_cad > 0.04:
                cadence_drop = True

        if high_decoupling_count >= 2 or (cadence_drop and high_decoupling_count >= 1):
            score = 75.0
            status = "Elevated"
            color = "#F59E0B"
            summary = "Elevated cardiovascular drift (>8%) or cadence drop detected."
            evidence = "Recent runs show signs of premature aerobic decoupling or subtle stride shortening under fatigue."
            rec = "Check hydration, sleep quality, and dial back pacing by 10-15 sec/km on easy runs."
        else:
            score = 15.0
            status = "Optimal"
            color = "#10B981"
            summary = "Stride cadence & aerobic coupling remain steady."
            evidence = "Cardiovascular and biomechanical metrics indicate positive running economy maintenance."
            rec = "Good form efficiency. Continue consistent pacing execution."

        return RiskSignal(
            name="Biomechanical Cadence & Decoupling",
            weight=weight,
            raw_value=float(score),
            score=score,
            status=status,
            status_color=color,
            summary=summary,
            detailed_evidence=evidence,
            recommendation=rec,
        )

    @classmethod
    def _generate_takeaways_and_guidance(cls, signals: List[RiskSignal], score: float) -> Tuple[List[str], List[str]]:
        takeaways = []
        guidance = []

        # Find signals with highest concern
        elevated = [s for s in signals if s.score >= 50]
        if not elevated:
            takeaways.append("All training load indicators are well within balanced physiological adaptation zones.")
            guidance.append("Continue standard scheduled training plan with regular progressive overload.")
        else:
            for s in elevated:
                takeaways.append(f"{s.name}: {s.summary}")
                guidance.append(s.recommendation)

        if score > 70:
            guidance.insert(0, " Primary Action: Consider reducing total weekly mileage by 20-30% for 3 to 5 days.")

        return takeaways, guidance

    @classmethod
    def _default_empty_report(cls) -> RiskReport:
        return RiskReport(
            composite_score=10.0,
            overall_status="No Data / Low Baseline",
            status_color="#10B981",
            acwr_value=1.0,
            ramp_rate_7d=0.0,
            monotony_7d=1.0,
            strain_7d=0.0,
            consecutive_hard_days=0,
            signals=[],
            key_takeaways=["Import activity data to activate real-time multi-signal training stress analysis."],
            actionable_guidance=["Upload your Garmin or Strava CSV export to begin tracking."],
        )
