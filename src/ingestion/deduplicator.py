"""
Activity deduplication and intelligent cross-source merging engine.
"""
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Any, Optional

from src.models.activity import Activity


class ActivityDeduplicator:
    """Deduplicates activities from Garmin, Strava, and manual uploads."""

    TIME_TOLERANCE_SECONDS = 900  # 15 minutes window
    DISTANCE_TOLERANCE_RATIO = 0.06  # 6% distance tolerance
    DURATION_TOLERANCE_RATIO = 0.06  # 6% duration tolerance

    @classmethod
    def are_activities_duplicate(cls, a1: Activity, a2: Activity) -> bool:
        """Determines if two activities represent the same physical workout."""
        # Exact ID match
        if a1.id == a2.id:
            return True

        # Time match
        time_diff = abs((a1.start_time - a2.start_time).total_seconds())
        if time_diff > cls.TIME_TOLERANCE_SECONDS:
            return False

        # Sport type compatibility
        run_types = {"run", "trail_run", "treadmill_run", "track_run"}
        if (a1.sport_type in run_types and a2.sport_type not in run_types) or \
           (a2.sport_type in run_types and a1.sport_type not in run_types):
            return False

        # Distance match (allow tiny absolute diff for short runs, ratio for longer)
        dist_diff = abs(a1.distance_meters - a2.distance_meters)
        max_dist = max(a1.distance_meters, a2.distance_meters, 1.0)
        dist_match = (dist_diff / max_dist <= cls.DISTANCE_TOLERANCE_RATIO) or (dist_diff < 250.0)
        if not dist_match:
            return False

        # Duration match
        dur_diff = abs(a1.duration_seconds - a2.duration_seconds)
        max_dur = max(a1.duration_seconds, a2.duration_seconds, 1.0)
        dur_match = (dur_diff / max_dur <= cls.DURATION_TOLERANCE_RATIO) or (dur_diff < 180.0)
        if not dur_match:
            return False

        return True

    @classmethod
    def merge_activities(cls, primary: Activity, secondary: Activity) -> Activity:
        """
        Merges two duplicate activities into a single canonical record with the best data from both.
        Garmin takes precedence for physiological & biomechanical metrics;
        Strava takes precedence for social titles, descriptions, and user notes.
        """
        # Determine base (Garmin preferred for core metrics)
        garmin_act = primary if primary.source == "garmin" else (secondary if secondary.source == "garmin" else None)
        strava_act = primary if primary.source == "strava" else (secondary if secondary.source == "strava" else None)

        base = primary

        # Build merged activity
        title = base.title
        if strava_act and strava_act.title and not strava_act.title.startswith("Strava Run"):
            # Use custom Strava title if user gave a custom name
            title = strava_act.title
        elif garmin_act and garmin_act.title and not garmin_act.title.startswith("Garmin"):
            title = garmin_act.title

        # Determine best metrics
        avg_hr = garmin_act.avg_hr if (garmin_act and garmin_act.avg_hr) else (secondary.avg_hr or primary.avg_hr)
        max_hr = garmin_act.max_hr if (garmin_act and garmin_act.max_hr) else (secondary.max_hr or primary.max_hr)
        avg_cadence = garmin_act.avg_cadence if (garmin_act and garmin_act.avg_cadence) else (secondary.avg_cadence or primary.avg_cadence)
        elev_gain = max(primary.elevation_gain_m, secondary.elevation_gain_m)

        aerobic_te = garmin_act.aerobic_te if garmin_act else (primary.aerobic_te or secondary.aerobic_te)
        anaerobic_te = garmin_act.anaerobic_te if garmin_act else (primary.anaerobic_te or secondary.anaerobic_te)
        stride_len = garmin_act.stride_length_m if garmin_act else (primary.stride_length_m or secondary.stride_length_m)
        vert_ratio = garmin_act.vertical_ratio if garmin_act else (primary.vertical_ratio or secondary.vertical_ratio)
        gct = garmin_act.ground_contact_time_ms if garmin_act else (primary.ground_contact_time_ms or secondary.ground_contact_time_ms)

        rpe = strava_act.rpe if (strava_act and strava_act.rpe) else (primary.rpe or secondary.rpe)
        notes = strava_act.notes if (strava_act and strava_act.notes) else (primary.notes or secondary.notes)

        merged_source = "garmin+strava" if (garmin_act and strava_act) else f"{primary.source}_merged"

        merged = Activity(
            id=primary.id,
            source=merged_source,
            source_id=f"{primary.source_id or ''}|{secondary.source_id or ''}".strip("|"),
            start_time=primary.start_time,
            sport_type=primary.sport_type,
            title=title,
            duration_seconds=max(primary.duration_seconds, secondary.duration_seconds),
            moving_time_seconds=max(primary.moving_time_seconds, secondary.moving_time_seconds),
            distance_meters=max(primary.distance_meters, secondary.distance_meters),
            elevation_gain_m=elev_gain,
            elevation_loss_m=max(primary.elevation_loss_m, secondary.elevation_loss_m),
            avg_hr=avg_hr,
            max_hr=max_hr,
            avg_pace_sec_km=primary.avg_pace_sec_km or secondary.avg_pace_sec_km,
            best_pace_sec_km=primary.best_pace_sec_km or secondary.best_pace_sec_km,
            avg_cadence=avg_cadence,
            max_cadence=garmin_act.max_cadence if garmin_act else (primary.max_cadence or secondary.max_cadence),
            avg_power_watts=primary.avg_power_watts or secondary.avg_power_watts,
            calories=max(primary.calories or 0, secondary.calories or 0) or None,
            aerobic_te=aerobic_te,
            anaerobic_te=anaerobic_te,
            stride_length_m=stride_len,
            vertical_ratio=vert_ratio,
            ground_contact_time_ms=gct,
            temperature_c=garmin_act.temperature_c if garmin_act else (primary.temperature_c or secondary.temperature_c),
            rpe=rpe,
            notes=notes,
            raw_data={**primary.raw_data, **secondary.raw_data},
        )
        return merged

    @classmethod
    def deduplicate_list(cls, activities: List[Activity], existing_activities: Optional[List[Activity]] = None) -> Tuple[List[Activity], Dict[str, Any]]:
        """
        Deduplicates a list of activities against each other and against an optional list of existing database activities.
        Returns (deduplicated_activities_to_save, summary_stats).
        """
        existing = existing_activities or []
        pool: List[Activity] = list(existing)
        duplicates_found = 0
        merged_count = 0
        new_unique = 0
        new_results: List[Activity] = []

        # Sort activities by start_time
        sorted_incoming = sorted(activities, key=lambda a: a.start_time)

        for incoming in sorted_incoming:
            matched_idx = -1
            for i, target in enumerate(pool):
                if cls.are_activities_duplicate(incoming, target):
                    matched_idx = i
                    break

            if matched_idx >= 0:
                duplicates_found += 1
                # Merge into existing target
                merged_act = cls.merge_activities(pool[matched_idx], incoming)
                pool[matched_idx] = merged_act
                merged_count += 1
                new_results.append(merged_act)
            else:
                pool.append(incoming)
                new_results.append(incoming)
                new_unique += 1

        stats = {
            "total_incoming": len(activities),
            "duplicates_found": duplicates_found,
            "merged_count": merged_count,
            "new_unique": new_unique,
            "total_canonical": len(pool),
        }
        return new_results, stats
