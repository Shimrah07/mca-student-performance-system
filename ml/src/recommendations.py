"""
ml/src/recommendations.py

Rule-based academic support recommendation engine for the AI-Based Student
Performance Prediction System.

This module translates model predictions and student academic habits into
constructive, non-judgmental guidance.

Design Safeguards:
- Uses only features supported by the UCI dataset (studytime, absences, failures,
  schoolsup, and G1 when available).
- Strictly ignores and excludes G2 and G3 to prevent data leakage.
- Never diagnoses personal, family, or psychological issues from demographic variables.
- Does not claim topic-level syllabus diagnosis (which the data cannot support).
- Transparently frames all output as supportive guidance and model estimates.
- Safely handles missing, partial, or invalid inputs.
"""

from typing import Dict, Any, List, Union
import pandas as pd
from ml.src.preprocessing import PERFORMANCE_CATEGORIES

# Explicitly disallowed attributes (never evaluated for recommendations)
LEAKAGE_AND_DEMOGRAPHIC_KEYS = {
    "G2", "G3", "sex", "address", "famsize", "Pstatus", "Mjob", "Fjob",
    "reason", "guardian", "nursery", "romantic", "famrel"
}


def generate_recommendations(
    student_data: Union[Dict[str, Any], pd.Series],
    predicted_category: str,
) -> Dict[str, Any]:
    """
    Generate supportive, rule-based academic recommendations based on
    a student's reported habits and predicted performance tier.

    Parameters:
      student_data: Dictionary or pandas Series containing input features.
      predicted_category: One of ['Needs Improvement', 'Average', 'Good', 'Excellent'].

    Returns:
      Dictionary containing summary, actionable recommendations, identified
      strengths, evaluated factors, and pedagogical disclaimer.
    """
    # 1. Validate category
    if predicted_category not in PERFORMANCE_CATEGORIES:
        raise ValueError(
            f"Invalid predicted_category '{predicted_category}'. "
            f"Expected one of: {PERFORMANCE_CATEGORIES}"
        )

    # Convert to dict if pandas Series
    data = student_data.to_dict() if isinstance(student_data, pd.Series) else dict(student_data)

    actionable_recs: List[str] = []
    strengths: List[str] = []
    evaluated_factors: Dict[str, Any] = {}

    # 2. Category-Level Strategic Summary
    category_summaries = {
        "Needs Improvement": (
            "The model indicates that foundational concept mastery requires timely reinforcement. "
            "Proactive engagement with structured study routines and faculty support will help build academic momentum."
        ),
        "Average": (
            "The model indicates steady academic engagement with clear potential for advancement. "
            "Targeted revisions and increased weekly study hours will help progress toward the 'Good' performance tier."
        ),
        "Good": (
            "The model indicates strong academic performance. Sustaining disciplined revision blocks "
            "and active problem-solving will help consolidate mastery toward the 'Excellent' category."
        ),
        "Excellent": (
            "The model reflects an outstanding performance trajectory. Maintain healthy study-life balance "
            "and consider advanced topic exploration or peer mentoring to deepen mastery."
        ),
    }

    # 3. Factor-Wise Rule Evaluation

    # --- Weekly Study Time (studytime: 1=<2h, 2=2-5h, 3=5-10h, 4=>10h) ---
    if "studytime" in data and data["studytime"] is not None and not pd.isna(data["studytime"]):
        studytime = int(data["studytime"])
        evaluated_factors["studytime"] = studytime
        if studytime == 1:
            actionable_recs.append(
                "Increase weekly independent study time to at least 5–10 hours (Level 3). "
                "Establish dedicated 1-hour daily study blocks in a distraction-free environment."
            )
        elif studytime == 2:
            if predicted_category in ("Needs Improvement", "Average"):
                actionable_recs.append(
                    "Consider scaling study time from 2–5 hours up to 5–10 hours per week, "
                    "focusing especially on concept summarization and problem sets."
                )
            else:
                strengths.append("Consistent baseline study commitment (2–5 hours weekly).")
        elif studytime >= 3:
            strengths.append(
                f"Commendable self-study dedication (Level {studytime}: 5+ hours weekly). "
                "Maintain this disciplined study habit."
            )

    # --- School Absences ---
    if "absences" in data and data["absences"] is not None and not pd.isna(data["absences"]):
        absences = int(data["absences"])
        evaluated_factors["absences"] = absences
        if absences >= 10:
            actionable_recs.append(
                f"Attendance Alert: High absenteeism ({absences} missed sessions) creates conceptual gaps. "
                "Prioritize consistent lecture attendance and review lecture notes for missed classes."
            )
        elif 5 <= absences < 10:
            actionable_recs.append(
                f"Monitor class attendance ({absences} absences recorded) to maintain continuity in subject topic progression."
            )
        else:
            strengths.append(f"Excellent attendance record ({absences} absences), supporting continuous learning.")

    # --- Past Class Failures ---
    if "failures" in data and data["failures"] is not None and not pd.isna(data["failures"]):
        failures = int(data["failures"])
        evaluated_factors["failures"] = failures
        if failures > 0:
            actionable_recs.append(
                f"Prior academic difficulty noted ({failures} past failure(s)). "
                "Schedule a consultation during faculty office hours to review prerequisite concepts and exam strategies."
            )
        else:
            strengths.append("Pristine academic track record with no prior subject failures.")

    # --- Extra School Educational Support (schoolsup) ---
    if "schoolsup" in data and data["schoolsup"] is not None and not pd.isna(data["schoolsup"]):
        schoolsup = str(data["schoolsup"]).lower().strip()
        evaluated_factors["schoolsup"] = schoolsup
        if schoolsup == "no" and predicted_category in ("Needs Improvement", "Average"):
            actionable_recs.append(
                "Explore department-provided academic tutoring or remedial study sessions to gain guided practice."
            )
        elif schoolsup == "yes":
            actionable_recs.append(
                "Continue making active use of institutional academic support and review remedial worksheets regularly."
            )

    # --- First-Period Exam Grade (G1, available in Scenario B) ---
    if "G1" in data and data["G1"] is not None and not pd.isna(data["G1"]):
        g1 = float(data["G1"])
        evaluated_factors["G1"] = g1
        if g1 < 10:
            actionable_recs.append(
                f"First-period assessment ({g1}/20) was below the passing mark. "
                "Prioritize immediate revision of early course themes before the subsequent assessment cycle."
            )
        elif 10 <= g1 < 14:
            actionable_recs.append(
                f"First-period score ({g1}/20) is passing. Identify specific questions where marks were lost "
                "and complete supplementary exercises."
            )
        else:
            strengths.append(f"Strong first-period exam foundation ({g1}/20). Maintain this momentum.")

    # --- Higher Education Aspiration (higher) ---
    if "higher" in data and data["higher"] is not None and not pd.isna(data["higher"]):
        higher = str(data["higher"]).lower().strip()
        evaluated_factors["higher"] = higher
        if higher == "yes":
            strengths.append("High academic aspiration for higher education serves as a strong positive motivator.")

    # 4. Fallback if no specific factors fired recommendations
    if not actionable_recs:
        actionable_recs.append(
            "Maintain a consistent weekly study timetable, participate actively in lectures, "
            "and consult course instructors whenever challenging topics arise."
        )

    # 5. Pedagogical Disclaimer
    disclaimer = (
        "Notice: These recommendations are rule-based academic support suggestions generated from "
        "statistical prediction estimates. They are intended for formative student encouragement and "
        "must not be interpreted as definitive guarantees of future academic results."
    )

    return {
        "predicted_category": predicted_category,
        "summary": category_summaries[predicted_category],
        "actionable_recommendations": actionable_recs,
        "strengths_identified": strengths,
        "evaluated_factors": evaluated_factors,
        "disclaimer": disclaimer,
    }
