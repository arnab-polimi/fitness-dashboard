"""
Fitness Intelligence Narrative Engine: "What is happening to my fitness?"
Analyzes underlying trends, physiological shifts, and generates actionable, transparent insights.
"""
from typing import List, Optional
import numpy as np
import pandas as pd

from src.models.activity import Activity
from src.models.user_profile import UserProfile
from src.models.metrics import DailyLoad, FitnessInsight, RacePrediction, RiskReport
from src.analytics.running_metrics import RunningMetricsCalculator, format_pace_sec_km


class FitnessInsightsEngine:
    """Generates structured narrative insights from underlying data."""

    @classmethod
    def generate_all_insights(
        cls,
        activities: List[Activity],
        daily_loads: List[DailyLoad],
        user_profile: UserProfile,
        race_predictions: List[RacePrediction],
        risk_report: RiskReport,
    ) -> List[FitnessInsight]:
        """Synthesizes all metric streams into clear, categorized intelligence narratives."""
        insights: List[FitnessInsight] = []

        if not activities or not daily_loads:
            insights.append(
                FitnessInsight(
                    category="general",
                    title="No Training Data Available Yet",
                    explanation="Import your Garmin Connect or Strava activity CSV exports to unlock deep fitness intelligence and physiological trend analysis.",
                    metric_evidence="Activity count: 0",
                    action_item="Go to the Data Import tab and upload your CSV or load sample synthetic data.",
                    impact="neutral",
                    icon="ℹ️",
                )
            )
            return insights

        # 1. Aerobic Efficiency & Mitochondrial Adaptation
        ef_insight = cls._analyze_aerobic_efficiency(activities)
        if ef_insight:
            insights.append(ef_insight)

        # 2. Fitness / Fatigue / Form Dynamics (CTL, ATL, TSB)
        form_insight = cls._analyze_form_and_fitness(daily_loads)
        if form_insight:
            insights.append(form_insight)

        # 3. Training Volume & Ramp Trajectory
        volume_insight = cls._analyze_volume_and_mileage(activities, daily_loads)
        if volume_insight:
            insights.append(volume_insight)

        # 4. Aerobic Decoupling & Endurance Resilience
        decoupling_insight = cls._analyze_aerobic_decoupling(activities)
        if decoupling_insight:
            insights.append(decoupling_insight)

        # 5. Cadence & Biomechanics
        cadence_insight = cls._analyze_cadence_and_economy(activities)
        if cadence_insight:
            insights.append(cadence_insight)

        # 6. Race Readiness & Threshold Pacing
        race_insight = cls._analyze_race_readiness(activities, race_predictions, daily_loads[-1].ctl)
        if race_insight:
            insights.append(race_insight)

        # 7. Stress & Risk Alert (if elevated)
        if risk_report.composite_score >= 50:
            insights.insert(
                0,
                FitnessInsight(
                    category="risk",
                    title=f"Training Load Warning: {risk_report.overall_status}",
                    explanation=f"Your composite training stress indicator is {risk_report.composite_score:.0f}/100. " + " ".join(risk_report.key_takeaways[:2]),
                    metric_evidence=f"ACWR: {risk_report.acwr_value:.2f} | 7d Ramp Rate: +{risk_report.ramp_rate_7d:.1f} TSS/wk",
                    action_item=risk_report.actionable_guidance[0] if risk_report.actionable_guidance else "Schedule an easy recovery run or full rest day.",
                    impact="warning" if risk_report.composite_score < 75 else "critical",
                    icon="⚠️",
                )
            )

        return insights

    @classmethod
    def _analyze_aerobic_efficiency(cls, activities: List[Activity]) -> Optional[FitnessInsight]:
        """Compares Efficiency Factor (speed/HR) between recent 30 days and prior 30-60 days."""
        valid_runs = [
            a for a in sorted(activities, key=lambda a: a.start_time)
            if a.sport_type in ["run", "trail_run", "treadmill_run"] and a.efficiency_factor and a.avg_hr and a.distance_km >= 3.0
        ]
        if len(valid_runs) < 4:
            return None

        # Split into recent 40% vs baseline 60%
        split_idx = int(len(valid_runs) * 0.6)
        baseline_runs = valid_runs[:split_idx]
        recent_runs = valid_runs[split_idx:]

        if not baseline_runs or not recent_runs:
            return None

        base_ef = np.mean([r.efficiency_factor for r in baseline_runs])
        recent_ef = np.mean([r.efficiency_factor for r in recent_runs])

        delta_pct = ((recent_ef - base_ef) / base_ef) * 100.0 if base_ef > 0 else 0.0

        if delta_pct >= 2.0:
            return FitnessInsight(
                category="efficiency",
                title="Aerobic Efficiency is Improving (+{:.1f}%)".format(delta_pct),
                explanation=(
                    f"Your running speed per heartbeat has increased by {delta_pct:.1f}% over the recent training block. "
                    f"You are traveling {recent_ef:.2f} meters per beat compared to {base_ef:.2f} previously, "
                    "signaling improved stroke volume, capillary density, and mitochondrial aerobic efficiency."
                ),
                metric_evidence=f"Efficiency Factor: {base_ef:.2f} ➔ {recent_ef:.2f} (+{delta_pct:.1f}%)",
                action_item="Your aerobic base is solidifying. You can safely add tempo or threshold intervals to build top-end speed.",
                impact="positive",
                icon="🫀",
            )
        elif delta_pct <= -3.0:
            return FitnessInsight(
                category="efficiency",
                title="Aerobic Efficiency Dip ({:.1f}%)".format(delta_pct),
                explanation=(
                    f"Your speed-to-heart-rate ratio decreased by {abs(delta_pct):.1f}% recently. "
                    "This is commonly caused by accumulated residual fatigue, warmer training temperatures, dehydration, or running on hilly terrain."
                ),
                metric_evidence=f"Efficiency Factor: {base_ef:.2f} ➔ {recent_ef:.2f} ({delta_pct:.1f}%)",
                action_item="Ensure adequate sleep and nutrition. Keep easy runs at truly conversational effort (Zone 2) to facilitate recovery.",
                impact="warning",
                icon="📉",
            )
        else:
            return FitnessInsight(
                category="efficiency",
                title="Aerobic Efficiency is Stable",
                explanation="Your heart rate response relative to running velocity is steady and consistent across workouts.",
                metric_evidence=f"Current EF: {recent_ef:.2f} (Baseline: {base_ef:.2f})",
                action_item="Maintain consistent aerobic mileage to drive progressive cardiovascular adaptations.",
                impact="neutral",
                icon="📊",
            )

    @classmethod
    def _analyze_form_and_fitness(cls, daily_loads: List[DailyLoad]) -> Optional[FitnessInsight]:
        """Analyzes CTL (Fitness), ATL (Fatigue), and TSB (Form)."""
        if not daily_loads:
            return None
        curr = daily_loads[-1]
        ctl = curr.ctl
        atl = curr.atl
        tsb = curr.tsb

        past_ctl = daily_loads[-28].ctl if len(daily_loads) >= 28 else (daily_loads[0].ctl)
        ctl_change = ctl - past_ctl

        if tsb > 10:
            form_desc = f"Fresh & Rested (TSB +{tsb:.1f})"
            expl = (
                f"Your fatigue ({atl:.1f}) has subsided below your chronic fitness ({ctl:.1f}). "
                "You are primed for peak race performance, a time trial, or a breakthrough quality session."
            )
            act = "Optimal window for high-intensity race execution or key milestone workout."
            impact = "positive"
            icon = "⚡"
        elif -15 <= tsb <= 10:
            form_desc = f"Productive Training Zone (TSB {tsb:+.1f})"
            expl = (
                f"Your training stress is balanced. With a Chronic Training Load (CTL) of {ctl:.1f} "
                f"({'+' if ctl_change>=0 else ''}{ctl_change:.1f} over 4 weeks), you are absorbing workout stimuli effectively."
            )
            act = "Continue current training progression; balance quality intervals with aerobic mileage."
            impact = "positive"
            icon = "📈"
        elif -30 <= tsb < -15:
            form_desc = f"Accumulating Fatigue (TSB {tsb:.1f})"
            expl = (
                f"Acute fatigue ({atl:.1f}) is running ahead of your fitness baseline ({ctl:.1f}). "
                "This is expected during hard training build phases, but muscle adaptation happens during recovery."
            )
            act = "Plan 1-2 easy recovery days or an active mobility session to absorb the training block."
            impact = "neutral"
            icon = "🔋"
        else:
            form_desc = f"Deep Fatigue / Overreaching (TSB {tsb:.1f})"
            expl = (
                f"Fatigue ({atl:.1f}) is heavily exceeding chronic capacity ({ctl:.1f}). "
                "Prolonged exposure in this zone blunts fitness gains and increases soft tissue injury vulnerability."
            )
            act = "Mandatory 2 to 3 days of active recovery or rest to prevent non-functional overreaching."
            impact = "warning"
            icon = "🛑"

        return FitnessInsight(
            category="fatigue",
            title=f"Form Dynamics: {form_desc}",
            explanation=expl,
            metric_evidence=f"Fitness (CTL): {ctl:.1f} | Fatigue (ATL): {atl:.1f} | Form (TSB): {tsb:+.1f}",
            action_item=act,
            impact=impact,
            icon=icon,
        )

    @classmethod
    def _analyze_volume_and_mileage(cls, activities: List[Activity], daily_loads: List[DailyLoad]) -> Optional[FitnessInsight]:
        if len(daily_loads) < 14:
            return None

        last_7_dist = sum(d.distance_km for d in daily_loads[-7:])
        prev_7_dist = sum(d.distance_km for d in daily_loads[-14:-7])

        if prev_7_dist <= 0:
            return None

        delta_pct = ((last_7_dist - prev_7_dist) / prev_7_dist) * 100.0

        if delta_pct > 25.0 and last_7_dist > 25.0:
            return FitnessInsight(
                category="volume",
                title=f"Mileage Jumped +{delta_pct:.0f}% in Last 7 Days",
                explanation=(
                    f"You logged {last_7_dist:.1f} km this week compared to {prev_7_dist:.1f} km last week (+{delta_pct:.0f}%). "
                    "The general sports science guideline recommends capping weekly mileage increments to 10-15% to safeguard bones and tendons."
                ),
                metric_evidence=f"Weekly Distance: {prev_7_dist:.1f} km ➔ {last_7_dist:.1f} km",
                action_item="Hold mileage steady or schedule a slight de-load next week before increasing volume further.",
                impact="warning",
                icon="🏃",
            )
        elif -15.0 <= delta_pct <= 15.0:
            return FitnessInsight(
                category="volume",
                title="Consistent Weekly Volume Progression",
                explanation=f"Weekly distance ({last_7_dist:.1f} km) is within the ideal progression window relative to prior weeks.",
                metric_evidence=f"7-Day Volume: {last_7_dist:.1f} km (Previous: {prev_7_dist:.1f} km)",
                action_item="Excellent discipline. Consistency is the single strongest predictor of long-term endurance gains.",
                impact="positive",
                icon="🎯",
            )
        else:
            return FitnessInsight(
                category="volume",
                title=f"Recovery / De-load Week Logged ({delta_pct:.0f}%)",
                explanation=f"You reduced volume from {prev_7_dist:.1f} km down to {last_7_dist:.1f} km, allowing tissue recovery.",
                metric_evidence=f"7-Day Volume: {last_7_dist:.1f} km (Previous: {prev_7_dist:.1f} km)",
                action_item="Use this recovery valley to recharge before starting your next focused build block.",
                impact="neutral",
                icon="🛌",
            )

    @classmethod
    def _analyze_aerobic_decoupling(cls, activities: List[Activity]) -> Optional[FitnessInsight]:
        long_runs = [
            a for a in sorted(activities, key=lambda a: a.start_time, reverse=True)
            if a.sport_type in ["run", "trail_run"] and a.distance_km >= 10.0 and a.aerobic_decoupling is not None
        ]
        if not long_runs:
            return None

        recent_decoupling = [r.aerobic_decoupling for r in long_runs[:3]]
        avg_drift = float(np.mean(recent_decoupling))

        if avg_drift < 4.0:
            return FitnessInsight(
                category="adaptation",
                title="Superb Aerobic Coupling & Stamina",
                explanation=(
                    f"Your aerobic decoupling on recent long runs averages only {avg_drift:.1f}% (target: <5%). "
                    "This demonstrates that your cardiac output and heart rate remain locked with running pace without cardiac drift, "
                    "a hallmark of well-developed fat metabolism and mitochondrial density."
                ),
                metric_evidence=f"Recent Long Run Drift: {avg_drift:.1f}%",
                action_item="Your endurance engine is race-ready for long distance events.",
                impact="positive",
                icon="🛡️",
            )
        elif avg_drift > 7.5:
            return FitnessInsight(
                category="adaptation",
                title=f"Elevated Aerobic Decoupling ({avg_drift:.1f}%)",
                explanation=(
                    f"Your heart rate drifted upwards by {avg_drift:.1f}% relative to pace in the second half of recent long runs. "
                    "This indicates either cardiovascular fatigue, running slightly too fast for pure aerobic zone, or dehydration/heat."
                ),
                metric_evidence=f"Recent Long Run Drift: {avg_drift:.1f}% (Ideal: <5%)",
                action_item="Slow down long run starting paces by 15-20 sec/km and review on-run hydration/electrolyte intake.",
                impact="warning",
                icon="💧",
            )
        return None

    @classmethod
    def _analyze_cadence_and_economy(cls, activities: List[Activity]) -> Optional[FitnessInsight]:
        run_cadences = [
            a.avg_cadence for a in sorted(activities, key=lambda a: a.start_time, reverse=True)[:10]
            if a.sport_type in ["run", "trail_run", "treadmill_run"] and a.avg_cadence and a.avg_cadence > 120
        ]
        if not run_cadences:
            return None

        mean_cad = float(np.mean(run_cadences))
        if 170 <= mean_cad <= 186:
            return FitnessInsight(
                category="efficiency",
                title=f"Optimal Running Cadence ({mean_cad:.0f} SPM)",
                explanation=(
                    f"Your average step rate across recent runs is {mean_cad:.0f} strides per minute (spm). "
                    "This cadence range minimizes vertical oscillation, shortens ground contact time, and protects knee and hip joints."
                ),
                metric_evidence=f"Recent 10-run Avg Cadence: {mean_cad:.0f} spm",
                action_item="Maintain this smooth, rhythmic stride pattern across both easy and tempo paces.",
                impact="positive",
                icon="🦶",
            )
        elif mean_cad < 162:
            return FitnessInsight(
                category="efficiency",
                title=f"Low Step Cadence ({mean_cad:.0f} SPM) - Overstriding Risk",
                explanation=(
                    f"Your average cadence of {mean_cad:.0f} spm indicates longer, slower strides. "
                    "Lower cadences often lead to overstriding (landing ahead of the center of mass), which acts as a braking force and increases tibial impact stress."
                ),
                metric_evidence=f"Current Cadence: {mean_cad:.0f} spm (Target: 170-180 spm)",
                action_item="Try quickening foot turnover slightly (+5-7 spm) with short, light steps under your hips.",
                impact="neutral",
                icon="⏱️",
            )
        return None

    @classmethod
    def _analyze_race_readiness(
        cls,
        activities: List[Activity],
        predictions: List[RacePrediction],
        current_ctl: float,
    ) -> Optional[FitnessInsight]:
        if not predictions:
            return None

        pred_5k = next((p for p in predictions if p.distance_name == "5K"), None)
        pred_10k = next((p for p in predictions if p.distance_name == "10K"), None)
        pred_half = next((p for p in predictions if p.distance_name == "Half Marathon"), None)

        if not pred_5k or not pred_10k:
            return None

        return FitnessInsight(
            category="race_readiness",
            title="Current Race Fitness Projections",
            explanation=(
                f"Based on your recent peak VDOT performances and Chronic Training Load (CTL {current_ctl:.0f}), "
                f"your estimated 5K capability is {pred_5k.formatted_time} ({pred_5k.formatted_pace}) and "
                f"10K is {pred_10k.formatted_time} ({pred_10k.formatted_pace})"
                + (f", with Half Marathon at {pred_half.formatted_time}." if pred_half else ".")
            ),
            metric_evidence=f"5K: {pred_5k.formatted_time} | 10K: {pred_10k.formatted_time}" + (f" | 21.1K: {pred_half.formatted_time}" if pred_half else ""),
            action_item="Use these projected paces to calibrate your Threshold (T) and Interval (I) workout targets.",
            impact="positive",
            icon="🏆",
        )
