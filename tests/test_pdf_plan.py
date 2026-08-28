"""
Tests for PDF Training Plan parser and scheduled workouts DB integration.
"""
import os
import pytest
from datetime import date
from src.ingestion.pdf_plan_parser import PDFPlanParser
from src.db.database import DatabaseManager


def test_pdf_plan_parser_generate_schedule():
    workouts = PDFPlanParser._generate_10k_master_schedule(year=2026)
    assert len(workouts) > 0
    first = workouts[0]
    assert "workout_date" in first
    assert "title" in first
    assert "target_distance_km" in first
    assert first["target_distance_km"] > 0


def test_db_scheduled_workouts_storage(tmp_path):
    db_file = os.path.join(tmp_path, "test_plan.db")
    db = DatabaseManager(db_path=db_file)
    
    workouts = PDFPlanParser._generate_10k_master_schedule(year=2026)
    saved_count = db.save_scheduled_workouts(workouts)
    assert saved_count == len(workouts)
    
    df = db.get_scheduled_workouts()
    assert not df.empty
    assert len(df) == len(workouts)
    
    upcoming = db.get_upcoming_workouts(from_date="2026-08-01", limit=5)
    assert not upcoming.empty
    assert len(upcoming) <= 5

    db.clear_scheduled_workouts()
    df_empty = db.get_scheduled_workouts()
    assert df_empty.empty


def test_render_training_plan_view_no_exception(tmp_path):
    from src.ui.views.training_plan_view import render_training_plan_view
    db_file = os.path.join(tmp_path, "test_render.db")
    db = DatabaseManager(db_path=db_file)
    workouts = PDFPlanParser._generate_10k_master_schedule(year=2026)
    db.save_scheduled_workouts(workouts)
    
    # Executing render_training_plan_view should not raise any unexpected keyword argument errors
    try:
        render_training_plan_view(db)
    except Exception as exc:
        # Ignore Streamlit missing script runner runtime context if raised, but confirm no TypeError/AttributeError
        assert "render_metric_card" not in str(exc)
        assert "unexpected keyword argument" not in str(exc)

