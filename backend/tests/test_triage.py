"""
Tests for the deterministic safety engine (triage.py)
"""

import pytest
from app.models import SymptomRequest, AgeGroup, UrgencyLevel
from app.triage import TriageEngine


class TestTriageEngine:
    """Test cases for the safety engine."""

    def test_emergency_chest_pain(self):
        """Test that chest pain triggers emergency urgency."""
        request = SymptomRequest(
            age_group=AgeGroup.ADULT,
            main_symptom="severe chest pain",
            duration="2 hours",
            onset="sudden",
            severity="severe",
        )
        urgency, signs = TriageEngine.evaluate(request)
        assert urgency == UrgencyLevel.EMERGENCY
        assert len(signs) > 0
        assert any("chest" in sign.sign.lower() for sign in signs)

    def test_emergency_breathing_difficulty(self):
        """Test that breathing difficulty triggers emergency urgency."""
        request = SymptomRequest(
            age_group=AgeGroup.ADULT,
            main_symptom="shortness of breath",
            duration="1 hour",
            onset="gradual",
            severity="moderate",
        )
        urgency, signs = TriageEngine.evaluate(request)
        assert urgency == UrgencyLevel.EMERGENCY
        assert len(signs) > 0

    def test_emergency_stroke_symptoms(self):
        """Test that stroke symptoms trigger emergency urgency."""
        request = SymptomRequest(
            age_group=AgeGroup.SENIOR,
            main_symptom="face drooping",
            duration="30 minutes",
            onset="sudden",
            severity="severe",
        )
        urgency, signs = TriageEngine.evaluate(request)
        assert urgency == UrgencyLevel.EMERGENCY
        assert len(signs) > 0

    def test_emergency_severe_bleeding(self):
        """Test that severe bleeding triggers emergency urgency."""
        request = SymptomRequest(
            age_group=AgeGroup.ADULT,
            main_symptom="cut on arm",
            duration="10 minutes",
            onset="accident",
            severity="severe bleeding",
            warning_signs=["can't stop bleeding"],
        )
        urgency, signs = TriageEngine.evaluate(request)
        assert urgency == UrgencyLevel.EMERGENCY
        assert len(signs) > 0

    def test_emergency_head_injury(self):
        """Test that head injury with loss of consciousness triggers emergency."""
        request = SymptomRequest(
            age_group=AgeGroup.ADULT,
            main_symptom="head injury",
            duration="1 hour",
            onset="fall",
            severity="severe",
            warning_signs=["loss of consciousness"],
        )
        urgency, signs = TriageEngine.evaluate(request)
        assert urgency == UrgencyLevel.EMERGENCY
        assert len(signs) > 0

    def test_emergency_severe_abdominal_pain(self):
        """Test that severe abdominal pain triggers emergency urgency."""
        request = SymptomRequest(
            age_group=AgeGroup.ADULT,
            main_symptom="severe abdominal pain",
            duration="2 hours",
            onset="sudden",
            severity="severe",
        )
        urgency, signs = TriageEngine.evaluate(request)
        assert urgency == UrgencyLevel.EMERGENCY
        assert len(signs) > 0

    def test_emergency_allergic_reaction(self):
        """Test that severe allergic reaction triggers emergency."""
        request = SymptomRequest(
            age_group=AgeGroup.ADULT,
            main_symptom="swelling",
            duration="15 minutes",
            onset="after eating",
            severity="severe",
            warning_signs=["swelling throat", "difficulty swallowing"],
        )
        urgency, signs = TriageEngine.evaluate(request)
        assert urgency == UrgencyLevel.EMERGENCY
        assert len(signs) > 0

    def test_emergency_high_fever(self):
        """Test that very high fever triggers emergency."""
        request = SymptomRequest(
            age_group=AgeGroup.ADULT,
            main_symptom="fever",
            duration="1 day",
            onset="gradual",
            severity="very high",
            warning_signs=["fever above 39"],
        )
        urgency, signs = TriageEngine.evaluate(request)
        assert urgency == UrgencyLevel.EMERGENCY
        assert len(signs) > 0

    def test_emergency_seizure(self):
        """Test that seizure triggers emergency."""
        request = SymptomRequest(
            age_group=AgeGroup.CHILD,
            main_symptom="seizure",
            duration="2 minutes",
            onset="sudden",
            severity="severe",
        )
        urgency, signs = TriageEngine.evaluate(request)
        assert urgency == UrgencyLevel.EMERGENCY
        assert len(signs) > 0

    def test_emergency_suicidal_thoughts(self):
        """Test that suicidal thoughts trigger emergency."""
        request = SymptomRequest(
            age_group=AgeGroup.TEEN,
            main_symptom="feeling depressed",
            duration="2 weeks",
            onset="gradual",
            severity="severe",
            additional_context="I have suicidal thoughts",
        )
        urgency, signs = TriageEngine.evaluate(request)
        assert urgency == UrgencyLevel.EMERGENCY
        assert len(signs) > 0

    def test_emergency_coughing_blood(self):
        """Test that coughing blood triggers emergency."""
        request = SymptomRequest(
            age_group=AgeGroup.ADULT,
            main_symptom="coughing",
            duration="1 hour",
            onset="sudden",
            severity="severe",
            warning_signs=["coughing blood"],
        )
        urgency, signs = TriageEngine.evaluate(request)
        assert urgency == UrgencyLevel.EMERGENCY
        assert len(signs) > 0
        assert any("blood" in sign.sign.lower() for sign in signs)

    def test_emergency_overdose(self):
        """Test that overdose triggers emergency."""
        request = SymptomRequest(
            age_group=AgeGroup.ADULT,
            main_symptom="took too many pills",
            duration="30 minutes",
            onset="sudden",
            severity="severe",
        )
        urgency, signs = TriageEngine.evaluate(request)
        assert urgency == UrgencyLevel.EMERGENCY
        assert len(signs) > 0

    def test_emergency_severe_chest_pain(self):
        """Test that severe chest pain triggers emergency (regression test)."""
        request = SymptomRequest(
            age_group=AgeGroup.ADULT,
            main_symptom="severe chest pain",
            duration="30 minutes",
            onset="sudden",
            severity="severe",
        )
        urgency, signs = TriageEngine.evaluate(request)
        assert urgency == UrgencyLevel.EMERGENCY
        assert len(signs) > 0
        assert any("chest" in sign.sign.lower() for sign in signs)

    def test_negated_symptoms_no_false_positive(self):
        """Test that negated symptoms don't trigger false positives."""
        request = SymptomRequest(
            age_group=AgeGroup.ADULT,
            main_symptom="mild discomfort",
            duration="2 hours",
            onset="gradual",
            severity="mild",
            additional_context="no chest pain, no difficulty breathing",
        )
        urgency, signs = TriageEngine.evaluate(request)
        # Should not be emergency since symptoms are negated
        assert urgency != UrgencyLevel.EMERGENCY
        # Should have no emergency warning signs
        assert not any("chest" in sign.sign.lower() or "breathing" in sign.sign.lower() for sign in signs)

    def test_negated_with_contractions(self):
        """Test that negated symptoms with contractions don't trigger false positives."""
        request = SymptomRequest(
            age_group=AgeGroup.ADULT,
            main_symptom="mild headache",
            duration="1 hour",
            onset="gradual",
            severity="mild",
            additional_context="I don't have chest pain and I'm not experiencing difficulty breathing",
        )
        urgency, signs = TriageEngine.evaluate(request)
        # Should not be emergency since symptoms are negated
        assert urgency != UrgencyLevel.EMERGENCY
        assert not any("chest" in sign.sign.lower() or "breathing" in sign.sign.lower() for sign in signs)

    def test_negated_variations(self):
        """Test various negation patterns."""
        request = SymptomRequest(
            age_group=AgeGroup.ADULT,
            main_symptom="sore throat",
            duration="2 days",
            onset="gradual",
            severity="mild",
            additional_context="never had chest pain, no breathing issues",
        )
        urgency, signs = TriageEngine.evaluate(request)
        # Should not be emergency since symptoms are negated
        assert urgency != UrgencyLevel.EMERGENCY
        assert not any("chest" in sign.sign.lower() or "breathing" in sign.sign.lower() for sign in signs)

    def test_genuine_symptom_not_suppressed_by_negation_elsewhere(self):
        """Test that genuine emergency symptoms are not suppressed by negations elsewhere."""
        request = SymptomRequest(
            age_group=AgeGroup.ADULT,
            main_symptom="severe chest pain",
            duration="30 minutes",
            onset="sudden",
            severity="severe",
            additional_context="no fever, no headache",
        )
        urgency, signs = TriageEngine.evaluate(request)
        # Should be emergency due to genuine chest pain in main symptom
        assert urgency == UrgencyLevel.EMERGENCY
        assert any("chest" in sign.sign.lower() for sign in signs)

    def test_urgent_persistent_fever(self):
        """Test that persistent fever triggers urgent (not emergency)."""
        request = SymptomRequest(
            age_group=AgeGroup.ADULT,
            main_symptom="fever",
            duration="3 days",
            onset="gradual",
            severity="moderate",
        )
        urgency, signs = TriageEngine.evaluate(request)
        assert urgency == UrgencyLevel.URGENT
        assert len(signs) > 0

    def test_urgent_persistent_pain(self):
        """Test that persistent pain triggers urgent."""
        request = SymptomRequest(
            age_group=AgeGroup.ADULT,
            main_symptom="back pain",
            duration="1 week",
            onset="gradual",
            severity="moderate",
        )
        urgency, signs = TriageEngine.evaluate(request)
        assert urgency == UrgencyLevel.URGENT
        assert len(signs) > 0

    def test_urgent_vomiting_diarrhea(self):
        """Test that vomiting/diarrhea triggers urgent."""
        request = SymptomRequest(
            age_group=AgeGroup.ADULT,
            main_symptom="vomiting",
            duration="1 day",
            onset="sudden",
            severity="moderate",
            associated_symptoms=["diarrhea"],
        )
        urgency, signs = TriageEngine.evaluate(request)
        assert urgency == UrgencyLevel.URGENT
        assert len(signs) > 0

    def test_routine_minor_symptom(self):
        """Test that minor symptoms result in routine urgency."""
        request = SymptomRequest(
            age_group=AgeGroup.ADULT,
            main_symptom="mild fatigue",
            duration="2 hours",
            onset="gradual",
            severity="mild",
        )
        urgency, signs = TriageEngine.evaluate(request)
        assert urgency == UrgencyLevel.ROUTINE
        # May or may not have warning signs based on keywords

    def test_unknown_insufficient_info(self):
        """Test that insufficient information returns unknown."""
        request = SymptomRequest(
            age_group=AgeGroup.ADULT,
            main_symptom="x",  # Too short
            duration="unknown",
            onset="unknown",
            severity="unknown",
        )
        urgency, signs = TriageEngine.evaluate(request)
        assert urgency == UrgencyLevel.UNKNOWN
        assert len(signs) == 0

    def test_multiple_warning_signs(self):
        """Test that multiple warning signs are all detected."""
        request = SymptomRequest(
            age_group=AgeGroup.ADULT,
            main_symptom="chest pain",
            duration="1 hour",
            onset="sudden",
            severity="severe",
            warning_signs=["shortness of breath", "can't stop bleeding"],
        )
        urgency, signs = TriageEngine.evaluate(request)
        assert urgency == UrgencyLevel.EMERGENCY
        assert len(signs) >= 2

    def test_emergency_contact(self):
        """Test that emergency contact returns 112."""
        contact = TriageEngine.get_emergency_contact()
        assert contact == "112"

    def test_case_insensitive_matching(self):
        """Test that matching is case-insensitive."""
        request = SymptomRequest(
            age_group=AgeGroup.ADULT,
            main_symptom="CHEST PAIN",
            duration="2 hours",
            onset="SUDDEN",
            severity="SEVERE",
        )
        urgency, signs = TriageEngine.evaluate(request)
        assert urgency == UrgencyLevel.EMERGENCY

    def test_symptom_in_additional_context(self):
        """Test that symptoms in additional context are detected."""
        request = SymptomRequest(
            age_group=AgeGroup.ADULT,
            main_symptom="feeling unwell",
            duration="1 hour",
            onset="gradual",
            severity="moderate",
            additional_context="I'm having chest pain and difficulty breathing",
        )
        urgency, signs = TriageEngine.evaluate(request)
        assert urgency == UrgencyLevel.EMERGENCY
