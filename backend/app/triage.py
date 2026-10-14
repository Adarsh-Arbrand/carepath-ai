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

import re
import unicodedata
from typing import Dict, List, Pattern, Tuple

from app.models import UrgencyLevel, SymptomRequest, WarningSign


# --- Text normalization ------------------------------------------------------
# Typographic apostrophes (phone keyboards, word processors) -> ASCII apostrophe.
_APOSTROPHE_TABLE = {ord(c): "'" for c in "\u2018\u2019\u201b\u02bc\u00b4\u2032`"}
_ZERO_WIDTH_TABLE = {ord(c): None for c in "\u200b\u200c\u200d\u2060\ufeff"}

_CONTRACTIONS = {
    "don't": "do not", "doesn't": "does not", "didn't": "did not",
    "won't": "will not", "can't": "cannot", "couldn't": "could not",
    "shouldn't": "should not", "wouldn't": "would not", "isn't": "is not",
    "aren't": "are not", "wasn't": "was not", "weren't": "were not",
    "haven't": "have not", "hasn't": "has not", "hadn't": "had not",
    "i'm": "i am", "it's": "it is", "that's": "that is",
    # Frequently typed without the apostrophe
    "cant": "cannot", "dont": "do not", "doesnt": "does not", "didnt": "did not",
    "couldnt": "could not", "shouldnt": "should not", "wouldnt": "would not",
    "isnt": "is not", "arent": "are not", "wasnt": "was not", "werent": "were not",
    "havent": "have not", "hasnt": "has not", "hadnt": "had not",
    "can not": "cannot",
}
_CONTRACTION_RE = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in sorted(_CONTRACTIONS, key=len, reverse=True)) + r")\b"
)


def _normalize(text: str) -> str:
    """Lower-case, unify apostrophes, strip invisible characters, expand contractions."""
    # Map apostrophes first: NFKC would turn U+00B4 into a combining accent.
    text = text.translate(_ZERO_WIDTH_TABLE).translate(_APOSTROPHE_TABLE)
    text = unicodedata.normalize("NFKC", text).lower()
    text = _CONTRACTION_RE.sub(lambda m: _CONTRACTIONS[m.group(0)], text)
    return " ".join(text.split())


# --- Negation handling (conservative, deliberately NOT full NLP) ------------
# A negation only applies to a symptom in the same clause, within a few words.
# Punctuation and contrast words end a clause, so "no chest pain but shortness of
# breath" still flags the shortness of breath. Anything uncertain is NOT negated.
_CLAUSE_SPLIT_RE = re.compile(
    r"[.,;:!?()\[\]/\u2014\u2013]+|\b(?:but|however|although|though|except|yet|while|whereas|and)\b"
)
_TOKEN_RE = re.compile(r"[a-z0-9']+")
_NEGATION_CUES = frozenset({"no", "not", "never", "without", "none", "neither", "nor"})
_NEGATION_WINDOW = 4  # the cue must be within the last 4 words before the symptom


# --- Sign matching -----------------------------------------------------------
# Signs must start at a word boundary ("benefit" must not match "fit", "spain" must
# not match "pain"). Word endings stay open so "painful", "seizures", "vomiting" still
# match, as they did with plain substring search.
_LEFT_OPEN_SIGNS = frozenset({"ache"})            # headache, toothache, earache
_WHOLE_WORD_SIGNS = {"fit": r"(?:s|ting)?"}       # "fit" must not match "fitness"

_Matcher = Tuple[str, dict, Pattern[str]]


def _sign_pattern(sign: str) -> Pattern[str]:
    body = re.escape(_normalize(sign))
    left = "" if sign in _LEFT_OPEN_SIGNS else r"(?<![a-z0-9])"
    right = (_WHOLE_WORD_SIGNS[sign] + r"(?![a-z0-9])") if sign in _WHOLE_WORD_SIGNS else ""
    return re.compile(left + body + right)


def _compile_rules(rules: Dict[str, dict]) -> Tuple[_Matcher, ...]:
    """Pre-compile every sign once at import time instead of per request."""
    return tuple(
        (sign, rule, _sign_pattern(sign))
        for rule in rules.values()
        for sign in rule["signs"]
    )



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


    # Compiled once at import time (see _compile_rules).
    _EMERGENCY_MATCHERS = _compile_rules(EMERGENCY_RULES)
    _URGENT_MATCHERS = _compile_rules(URGENT_RULES)

    @classmethod
    def _normalize_text(cls, text: str) -> str:
        """Kept for backward compatibility; see module-level _normalize."""
        return _normalize(text)

    @staticmethod
    def _is_negated(clause: str, match_start: int) -> bool:
        """
        True if a negation word appears within the last few words before the match,
        inside the same clause. Conservative: anything uncertain is NOT negated.
        """
        preceding = _TOKEN_RE.findall(clause[:match_start])
        return any(token in _NEGATION_CUES for token in preceding[-_NEGATION_WINDOW:])

    @staticmethod
    def _clauses(request: SymptomRequest) -> List[str]:
        """
        Normalize each form field separately and split it into clauses, so a negation
        in one field or clause can never suppress a symptom in another.
        """
        fields = [
            request.main_symptom,
            request.duration,
            request.onset,
            request.severity,
            *request.associated_symptoms,
            *request.warning_signs,
            request.additional_context or "",
        ]
        clauses: List[str] = []
        for field in fields:
            for line in field.splitlines():
                for clause in _CLAUSE_SPLIT_RE.split(_normalize(line)):
                    clause = clause.strip()
                    if clause:
                        clauses.append(clause)
        return clauses

    @classmethod
    def _find_signs(cls, matchers: Tuple[_Matcher, ...], clauses: List[str]) -> List[WarningSign]:
        """Return each sign that has at least one non-negated occurrence."""
        found: List[WarningSign] = []
        for sign, rule, pattern in matchers:
            for clause in clauses:
                if any(not cls._is_negated(clause, m.start()) for m in pattern.finditer(clause)):
                    found.append(
                        WarningSign(
                            sign=sign,
                            description=rule["description"],
                            source=rule["source"],
                        )
                    )
                    break  # report each sign once
        return found

    @classmethod
    def evaluate(cls, request: SymptomRequest) -> Tuple[UrgencyLevel, List[WarningSign]]:
        """
        Evaluate a symptom request against safety rules.

        Returns:
            Tuple of (urgency_level, list of triggered warning signs)
        """
        clauses = cls._clauses(request)

        emergency_signs = cls._find_signs(cls._EMERGENCY_MATCHERS, clauses)
        if emergency_signs:
            return UrgencyLevel.EMERGENCY, emergency_signs

        urgent_signs = cls._find_signs(cls._URGENT_MATCHERS, clauses)
        if urgent_signs:
            return UrgencyLevel.URGENT, urgent_signs

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
