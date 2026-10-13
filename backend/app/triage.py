"""
Deterministic Safety Engine for CarePath AI

This module implements conservative, rule-based safety checks that run independently
of any AI/LLM system. These rules are based on reputable public health guidance
and are designed to identify potential emergency situations.

IMPORTANT:
- This is NOT a diagnostic system
- Rules are conservative and may trigger on non-emergency situations
- When in doubt, the system errs on the side of caution
- These rules have NOT been clinically validated
- Always seek professional medical evaluation for actual medical decisions

Sources:
- National Health Service (NHS) UK
- Mayo Clinic
- American Heart Association
- Centers for Disease Control and Prevention (CDC)
- World Health Organization (WHO)

Last reviewed: October 2025
Scope: General informational guidance only
Limitations: Not comprehensive, not clinically validated, not a substitute for professional medical advice
"""

from typing import List, Tuple
from app.models import UrgencyLevel, SymptomRequest, WarningSign


class TriageEngine:
    """
    Deterministic safety engine that evaluates symptom information against
    conservative emergency warning signs.
    """

    # Emergency warning signs based on reputable public health guidance
    EMERGENCY_RULES = {
        "chest_pain": {
            "signs": [
                "chest pain",
                "chest pressure",
                "chest tightness",
                "chest discomfort",
            ],
            "description": "Chest pain or pressure can indicate heart attack or other serious conditions",
            "source": "American Heart Association, NHS UK",
        },
        "breathing_difficulty": {
            "signs": [
                "difficulty breathing",
                "shortness of breath",
                "can't breathe",
                "breathless",
                "wheezing severe",
            ],
            "description": "Difficulty breathing requires immediate emergency evaluation",
            "source": "NHS UK, Mayo Clinic",
        },
        "stroke_symptoms": {
            "signs": [
                "face drooping",
                "slurred speech",
                "difficulty speaking",
                "arm weakness",
                "numbness face",
                "numbness arm",
                "confusion sudden",
            ],
            "description": "These may indicate stroke - time-sensitive emergency",
            "source": "American Stroke Association, CDC",
        },
        "severe_bleeding": {
            "signs": [
                "severe bleeding",
                "can't stop bleeding",
                "heavy bleeding",
                "blood loss heavy",
            ],
            "description": "Uncontrolled severe bleeding requires immediate care",
            "source": "NHS UK, Mayo Clinic",
        },
        "severe_head_injury": {
            "signs": [
                "head injury severe",
                "loss of consciousness",
                "passed out",
                "fainted",
                "unconscious",
                "confusion after head injury",
            ],
            "description": "Severe head injury with loss of consciousness needs emergency care",
            "source": "NHS UK, CDC",
        },
        "severe_abdominal_pain": {
            "signs": [
                "severe abdominal pain",
                "stomach pain severe",
                "belly pain severe",
                "abdomen rigid",
                "tender abdomen",
            ],
            "description": "Sudden severe abdominal pain may indicate serious conditions",
            "source": "Mayo Clinic, NHS UK",
        },
        "severe_allergic_reaction": {
            "signs": [
                "swelling face",
                "swelling throat",
                "swelling tongue",
                "difficulty swallowing",
                "hives severe",
                "anaphylaxis",
            ],
            "description": "Signs of severe allergic reaction can be life-threatening",
            "source": "NHS UK, Mayo Clinic",
        },
        "high_fever": {
            "signs": [
                "fever very high",
                "fever above 39",
                "temperature high",
                "fever with stiff neck",
                "fever with rash",
            ],
            "description": "Very high fever or fever with concerning symptoms needs evaluation",
            "source": "CDC, NHS UK",
        },
        "seizure": {
            "signs": [
                "seizure",
                "convulsion",
                "fit",
                "uncontrollable shaking",
            ],
            "description": "Seizure activity requires medical evaluation",
            "source": "NHS UK, Mayo Clinic",
        },
        "suicidal_thoughts": {
            "signs": [
                "suicidal",
                "want to die",
                "self harm",
                "hurt myself",
            ],
            "description": "Suicidal thoughts require immediate mental health support",
            "source": "NHS UK, National Suicide Prevention Lifeline",
        },
    }

    # Urgent (but not emergency) warning signs
    URGENT_RULES = {
        "persistent_fever": {
            "signs": ["fever", "temperature", "chills"],
            "description": "Fever that persists may need medical evaluation",
            "source": "CDC, NHS UK",
        },
        "persistent_pain": {
            "signs": ["pain", "ache", "hurt"],
            "description": "Persistent pain should be evaluated by a healthcare professional",
            "source": "Mayo Clinic",
        },
        "vomiting_diarrhea": {
            "signs": ["vomiting", "throwing up", "diarrhea", "nausea"],
            "description": "Persistent vomiting or diarrhea can lead to dehydration",
            "source": "CDC, NHS UK",
        },
        "dizziness": {
            "signs": ["dizzy", "lightheaded", "vertigo"],
            "description": "Persistent dizziness may need evaluation",
            "source": "Mayo Clinic",
        },
    }

    @classmethod
    def evaluate(cls, request: SymptomRequest) -> Tuple[UrgencyLevel, List[WarningSign]]:
        """
        Evaluate a symptom request against safety rules.

        Returns:
            Tuple of (urgency_level, list of triggered warning signs)
        """
        all_text = " ".join([
            request.main_symptom.lower(),
            request.duration.lower(),
            request.onset.lower(),
            request.severity.lower(),
            " ".join(s.lower() for s in request.associated_symptoms),
            " ".join(s.lower() for s in request.warning_signs),
            (request.additional_context or "").lower(),
        ])

        detected_signs = []

        # Check emergency rules first
        for rule_name, rule in cls.EMERGENCY_RULES.items():
            for sign in rule["signs"]:
                if sign in all_text:
                    detected_signs.append(WarningSign(
                        sign=sign,
                        description=rule["description"],
                        source=rule["source"]
                    ))

        # If any emergency signs detected, return emergency
        if detected_signs:
            return UrgencyLevel.EMERGENCY, detected_signs

        # Check urgent rules
        for rule_name, rule in cls.URGENT_RULES.items():
            for sign in rule["signs"]:
                if sign in all_text:
                    detected_signs.append(WarningSign(
                        sign=sign,
                        description=rule["description"],
                        source=rule["source"]
                    ))

        # If urgent signs detected, return urgent
        if detected_signs:
            return UrgencyLevel.URGENT, detected_signs

        # If insufficient information, return unknown
        if not request.main_symptom or len(request.main_symptom) < 3:
            return UrgencyLevel.UNKNOWN, []

        # Default to routine for non-emergency symptoms
        return UrgencyLevel.ROUTINE, []

    @classmethod
    def get_emergency_contact(cls) -> str:
        """
        Returns the emergency contact number.
        For India-oriented demonstration, returns 112.
        """
        return "112"
