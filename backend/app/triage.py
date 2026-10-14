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
                "trouble breathing",
                "unable to breathe",
                "choking",
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
                "kill myself",
                "end my life",
            ],
            "description": "Suicidal thoughts require immediate mental health support",
            "source": "NHS UK, National Suicide Prevention Lifeline",
        },
        "coughing_blood": {
            "signs": [
                "coughing blood",
                "cough blood",
                "coughing up blood",
                "blood in cough",
                "hemoptysis",
            ],
            "description": "Coughing blood can indicate serious lung or heart conditions",
            "source": "NHS UK, Mayo Clinic",
        },
        "overdose": {
            "signs": [
                "overdose",
                "took too many pills",
                "drug overdose",
                "medication overdose",
                "poisoning",
                "ingested poison",
            ],
            "description": "Drug overdose or poisoning requires immediate emergency care",
            "source": "NHS UK, CDC",
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
    def _normalize_text(cls, text: str) -> str:
        """
        Normalize text by handling Unicode apostrophes and common contractions.
        This is a conservative approach, not full NLP.
        """
        # Normalize Unicode apostrophes to standard ASCII apostrophe
        text = text.replace("'", "'").replace("'", "'").replace("'", "'")
        text = text.replace("`", "'")

        # Expand common contractions for negation detection
        contractions = {
            "don't": "do not",
            "doesn't": "does not",
            "didn't": "did not",
            "won't": "will not",
            "can't": "cannot",
            "couldn't": "could not",
            "shouldn't": "should not",
            "wouldn't": "would not",
            "isn't": "is not",
            "aren't": "are not",
            "wasn't": "was not",
            "weren't": "were not",
            "haven't": "have not",
            "hasn't": "has not",
            "hadn't": "had not",
            "i'm": "i am",
            "it's": "it is",
            "that's": "that is",
        }

        for contraction, expansion in contractions.items():
            text = text.replace(contraction, expansion)

        return text.lower()

    @classmethod
    def _is_negated(cls, text: str, symptom: str, match_start: int) -> bool:
        """
        Check if a symptom occurrence is negated.

        This is a conservative phrase-boundary check, not full NLP.
        Looks for negation words within a small window before the symptom.

        Returns True if the symptom appears to be negated.
        """
        # Get the text before the match
        preceding_text = text[:match_start].strip()

        # Check for negation words in the last 50 characters before the match
        window = preceding_text[-50:] if len(preceding_text) > 50 else preceding_text

        # Remove trailing spaces from window for matching
        window_stripped = window.rstrip()

        negation_words = [
            "no", "not", "never", "without", "none",
            "do not", "does not", "did not", "cannot",
            "will not", "could not", "should not", "would not",
            "is not", "are not", "was not", "were not",
            "have not", "has not", "had not",
        ]

        # Check if the window ends with a negation word (with or without space)
        for neg in negation_words:
            # Check if window ends with the negation word
            if window_stripped.endswith(neg):
                return True
            # Check if negation word is in window with a space after
            if f"{neg} " in window:
                return True

        return False

    @classmethod
    def evaluate(cls, request: SymptomRequest) -> Tuple[UrgencyLevel, List[WarningSign]]:
        """
        Evaluate a symptom request against safety rules.

        Returns:
            Tuple of (urgency_level, list of triggered warning signs)
        """
        # Normalize and combine all text
        all_text = " ".join([
            request.main_symptom,
            request.duration,
            request.onset,
            request.severity,
            " ".join(request.associated_symptoms),
            " ".join(request.warning_signs),
            (request.additional_context or ""),
        ])

        normalized_text = cls._normalize_text(all_text)

        detected_signs = []

        # Check emergency rules first
        for rule_name, rule in cls.EMERGENCY_RULES.items():
            for sign in rule["signs"]:
                normalized_sign = cls._normalize_text(sign)

                # Find all occurrences of the sign
                start = 0
                sign_detected = False

                while True:
                    match_start = normalized_text.find(normalized_sign, start)
                    if match_start == -1:
                        break

                    # Check if this occurrence is negated
                    if not cls._is_negated(normalized_text, normalized_sign, match_start):
                        # Non-negated occurrence found
                        detected_signs.append(WarningSign(
                            sign=sign,
                            description=rule["description"],
                            source=rule["source"]
                        ))
                        sign_detected = True
                        break  # Only add once per sign

                    start = match_start + 1

        # If any emergency signs detected, return emergency
        if detected_signs:
            return UrgencyLevel.EMERGENCY, detected_signs

        # Check urgent rules
        for rule_name, rule in cls.URGENT_RULES.items():
            for sign in rule["signs"]:
                normalized_sign = cls._normalize_text(sign)

                # Find all occurrences of the sign
                start = 0
                sign_detected = False

                while True:
                    match_start = normalized_text.find(normalized_sign, start)
                    if match_start == -1:
                        break

                    # Check if this occurrence is negated
                    if not cls._is_negated(normalized_text, normalized_sign, match_start):
                        # Non-negated occurrence found
                        detected_signs.append(WarningSign(
                            sign=sign,
                            description=rule["description"],
                            source=rule["source"]
                        ))
                        sign_detected = True
                        break  # Only add once per sign

                    start = match_start + 1

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
