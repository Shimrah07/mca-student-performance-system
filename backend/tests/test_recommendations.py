"""
backend/tests/test_recommendations.py

Automated test suite verifying the rule-based academic support recommendations:
- Category-level summary generation
- Factor-based rule triggers for studytime, absences, failures, schoolsup, and G1
- Handling of missing, None, and partial inputs without crashing or fabricating rules
- Demographic feature isolation (demographic attributes never trigger recommendations)
- Strict leakage safeguard: G2 and G3 are never evaluated
- Rejection of invalid predicted categories with ValueError
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
import pandas as pd

from ml.src.recommendations import generate_recommendations
from ml.src.preprocessing import PERFORMANCE_CATEGORIES


def test_needs_improvement_recommendations():
    """Verify that a struggling student receives targeted academic intervention advice."""
    student = {
        "studytime": 1,
        "absences": 14,
        "failures": 2,
        "schoolsup": "no",
        "higher": "yes",
    }
    rec = generate_recommendations(student, predicted_category="Needs Improvement")

    assert rec["predicted_category"] == "Needs Improvement"
    assert "foundational concept mastery" in rec["summary"]

    recs_text = " ".join(rec["actionable_recommendations"])
    assert "independent study time" in recs_text
    assert "Attendance Alert" in recs_text
    assert "remedial study sessions" in recs_text

    # Strength from higher education
    assert any("higher education" in s for s in rec["strengths_identified"])
    assert "studytime" in rec["evaluated_factors"]
    assert "absences" in rec["evaluated_factors"]


def test_excellent_student_recommendations():
    """Verify that a top-performing student receives commendations and enrichment guidance."""
    student = {
        "studytime": 4,
        "absences": 2,
        "failures": 0,
        "higher": "yes",
    }
    rec = generate_recommendations(student, predicted_category="Excellent")

    assert rec["predicted_category"] == "Excellent"
    assert "outstanding performance trajectory" in rec["summary"]

    strengths_text = " ".join(rec["strengths_identified"])
    assert "Commendable self-study dedication" in strengths_text
    assert "Excellent attendance" in strengths_text
    assert "no prior subject failures" in strengths_text


def test_scenario_b_g1_evaluations():
    """Verify that first-period grade (G1) triggers appropriate diagnostic guidance."""
    # Struggling G1
    rec_low = generate_recommendations({"G1": 7}, predicted_category="Needs Improvement")
    assert any("First-period assessment (7.0/20) was below the passing mark" in r for r in rec_low["actionable_recommendations"])

    # High G1
    rec_high = generate_recommendations({"G1": 16}, predicted_category="Good")
    assert any("Strong first-period exam foundation (16.0/20)" in s for s in rec_high["strengths_identified"])


def test_missing_and_partial_inputs():
    """Verify that missing or None features do not cause crashes or fabricate false advice."""
    student_partial = {
        "studytime": 2,
        "absences": None,
        # 'failures' and 'schoolsup' omitted entirely
    }
    rec = generate_recommendations(student_partial, predicted_category="Average")

    assert rec["predicted_category"] == "Average"
    assert "absences" not in rec["evaluated_factors"]
    assert "failures" not in rec["evaluated_factors"]
    # Does not fabricate an attendance alert
    assert not any("Attendance Alert" in r for r in rec["actionable_recommendations"])


def test_empty_input_fallback():
    """Verify that an empty dictionary falls back to general academic advice without crashing."""
    rec = generate_recommendations({}, predicted_category="Average")
    assert rec["predicted_category"] == "Average"
    assert len(rec["actionable_recommendations"]) == 1
    assert "Maintain a consistent weekly study timetable" in rec["actionable_recommendations"][0]


def test_demographic_attributes_never_trigger_rules():
    """Verify that household, demographic, and personal attributes are completely ignored."""
    student_demo = {
        "sex": "F",
        "address": "R",
        "Mjob": "at_home",
        "Fjob": "other",
        "Pstatus": "A",
        "romantic": "yes",
        "famrel": 1,
    }
    rec = generate_recommendations(student_demo, predicted_category="Good")

    # None of the demographic keys should appear in evaluated_factors
    for k in ["sex", "address", "Mjob", "Fjob", "Pstatus", "romantic", "famrel"]:
        assert k not in rec["evaluated_factors"]

    # Recommendations should not comment on personal/family variables
    all_text = " ".join(rec["actionable_recommendations"] + rec["strengths_identified"])
    for forbidden in ["female", "rural", "mother", "father", "romantic", "divorce"]:
        assert forbidden not in all_text.lower()


def test_g2_g3_leakage_safeguard():
    """Verify that if G2 or G3 are inadvertently provided, they are excluded from evaluation."""
    student = {
        "G2": 18,
        "G3": 19,
        "studytime": 3,
    }
    rec = generate_recommendations(student, predicted_category="Good")

    assert "G2" not in rec["evaluated_factors"]
    assert "G3" not in rec["evaluated_factors"]


def test_invalid_predicted_category_raises_error():
    """Verify that unsupported category names raise ValueError."""
    with pytest.raises(ValueError):
        generate_recommendations({}, predicted_category="Distinction")

    with pytest.raises(ValueError):
        generate_recommendations({}, predicted_category="Pass")


def test_accepts_pandas_series():
    """Verify that generate_recommendations works seamlessly when passed a pandas Series."""
    series = pd.Series({"studytime": 3, "absences": 4, "failures": 0})
    rec = generate_recommendations(series, predicted_category="Good")
    assert rec["predicted_category"] == "Good"
    assert "studytime" in rec["evaluated_factors"]
