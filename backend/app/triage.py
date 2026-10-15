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

# Failure-of-relief or non-negating phrases: when these appear between the negation cue
# and the symptom, the patient is describing lack of relief or inability to stop a symptom,
# NOT denying the symptom's presence.
_NON_NEGATING_INTERVENING = re.compile(
    r"\b(?:"
    r"relief\b|"
    r"improvement\b|"
    r"better\b|"
    r"only\b|"
    r"just\b|"
    r"(?:able\s+to\s+|unable\s+to\s+)?(?:stop|control|manage|help)\b|"
    r"go\s+away\b"
    r")",
    re.IGNORECASE,
)

# Intensifier phrases following a symptom (e.g. "never had chest pain this bad")
_INTENSIFIER_FOLLOWING = re.compile(
    r"\b(?:this|so)\s+(?:bad|severe|intense|terrible|awful|worse)\b|\blike\s+this\b",
    re.IGNORECASE,
)


# --- Sign matching -----------------------------------------------------------
# Signs must match strictly at word boundaries.
# Avoid false positives such as "fit" inside "fitting", "ache" inside "teacher",
# or "pain" inside "painting".
_Matcher = Tuple[str, dict, Pattern[str]]


def _sign_pattern(sign: str) -> Pattern[str]:
    norm_sign = _normalize(sign)
    if norm_sign == "pain":
        return re.compile(r"(?<![a-z0-9])pain(?:s|ful|fully)?(?![a-z0-9])")
    elif norm_sign == "fit":
        return re.compile(r"(?<![a-z0-9])fits?(?![a-z0-9])")
    elif norm_sign == "ache":
        return re.compile(r"(?:\b(?:(?:head|tooth|teeth|ear|back|belly|stomach|body|muscle)ache|ache)(?:s|d)?\b|\baching\b)")
    else:
        body = re.escape(norm_sign)
        left = r"(?<![a-z0-9])"
        right = r"(?:s|d|ed|es)?(?![a-z0-9])"
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
                "crushing chest pain",
                "pressure in chest",
                "tightness in chest",
                "tightness in my chest",
                "pressure on chest",
                "pressure on my chest",
                "elephant on chest",
                "elephant on my chest",
                "elephant sitting on chest",
                "elephant sitting on my chest",
                "heart attack",
                "having a heart attack",
                "think i am having a heart attack",
                "pain radiating to arm",
                "pain radiating to left arm",
                "pain radiating to jaw",
                "cardiac arrest",
                "myocardial infarction",
            ],
            "description": "Chest pain, pressure, tightness, or suspected heart attack can indicate a life-threatening cardiac event",
            "source": "American Heart Association, NHS UK",
        },
        "breathing_difficulty": {
            "signs": [
                "difficulty breathing",
                "shortness of breath",
                "can't breathe",
                "cant breathe",
                "cannot breathe",
                "breathless",
                "wheezing severe",
                "severe wheezing",
                "trouble breathing",
                "unable to breathe",
                "struggling to breathe",
                "hard to breathe",
                "cannot catch breath",
                "cant catch breath",
                "cannot catch my breath",
                "cant catch my breath",
                "unable to catch breath",
                "unable to catch my breath",
                "gasping for air",
                "gasping for breath",
                "fighting for air",
                "choking",
                "suffocating",
                "turning blue",
                "blue lips",
                "lips turning blue",
            ],
            "description": "Severe difficulty breathing or respiratory compromise requires immediate emergency evaluation",
            "source": "NHS UK, Mayo Clinic",
        },
        "infant_breathing_emergency": {
            "signs": [
                "chest sucking in",
                "ribs sucking in",
                "skin sucking in",
                "chest retractions",
                "chest retraction",
                "grunting",
                "grunting while breathing",
                "flaring nostrils",
                "nostril flaring",
                "pauses in breathing",
                "stopped breathing",
                "stops breathing",
                "blue around mouth",
                "baby struggling to breathe",
                "infant struggling to breathe",
            ],
            "description": "Signs of respiratory distress in infants or children require immediate pediatric emergency care",
            "source": "American Academy of Pediatrics (AAP), NHS UK, WHO",
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
                "cant stop bleeding",
                "cannot stop bleeding",
                "heavy bleeding",
                "blood loss heavy",
                "bleeding heavily",
                "bleeding will not stop",
                "bleeding won't stop",
                "bleeding wont stop",
                "blood soaking through",
                "gushing blood",
                "spurting blood",
                "losing a lot of blood",
                "pooling blood",
                "massive bleeding",
            ],
            "description": "Uncontrolled severe bleeding requires immediate emergency medical care",
            "source": "NHS UK, Mayo Clinic",
        },
        "severe_head_injury": {
            "signs": [
                "head injury severe",
                "severe head injury",
                "loss of consciousness",
                "passed out",
                "fainted",
                "unconscious",
                "confusion after head injury",
                "worst headache of life",
                "worst headache of my life",
                "thunderclap headache",
                "sudden severe headache",
            ],
            "description": "Severe head injury or sudden severe headache needs immediate emergency evaluation",
            "source": "NHS UK, CDC, American Stroke Association",
        },
        "severe_abdominal_pain": {
            "signs": [
                "severe abdominal pain",
                "severe stomach pain",
                "severe belly pain",
                "stomach pain severe",
                "belly pain severe",
                "abdomen rigid",
                "rigid abdomen",
                "stomach rigid",
                "tender abdomen",
                "acute abdomen",
                "intense abdominal pain",
                "agonizing stomach pain",
                "severe pelvic pain",
            ],
            "description": "Sudden or severe abdominal pain may indicate acute surgical or life-threatening conditions",
            "source": "Mayo Clinic, NHS UK",
        },
        "severe_allergic_reaction": {
            "signs": [
                "swelling face",
                "swelling throat",
                "swelling tongue",
                "difficulty swallowing",
                "hives severe",
                "severe hives",
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
                "having a seizure",
                "had a seizure",
                "grand mal",
                "shaking uncontrollably",
                "seizing",
                "violent shaking",
                "epileptic fit",
                "jerking uncontrollably",
            ],
            "description": "Seizure activity or uncontrollable shaking requires immediate medical evaluation",
            "source": "NHS UK, Mayo Clinic",
        },
        "suicidal_thoughts": {
            "signs": [
                "suicidal",
                "want to die",
                "i want to die",
                "wish i was dead",
                "wish i were dead",
                "wishing i was dead",
                "do not want to live",
                "dont want to live",
                "do not want to live anymore",
                "dont want to live anymore",
                "no reason to live",
                "better off dead",
                "thinking of ending my life",
                "suicide",
                "self harm",
                "hurt myself",
                "harming myself",
                "kill myself",
                "end my life",
                "take my own life",
            ],
            "description": "Suicidal thoughts, self-harm, or despair require immediate crisis intervention and mental health support",
            "source": "NHS UK, Tele-MANAS, SAMHSA",
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
                "overdosed",
                "overdosing",
                "suspected overdose",
                "took too many pills",
                "swallowed a bottle",
                "swallowed a bottle of",
                "took an entire bottle",
                "took all my pills",
                "drug overdose",
                "medication overdose",
                "poisoning",
                "ingested poison",
                "drank poison",
                "drank bleach",
                "chemical ingestion",
                "swallowed pills",
                "accidental overdose",
                "poisoned",
            ],
            "description": "Suspected drug overdose or chemical ingestion requires immediate emergency medical care",
            "source": "NHS UK, CDC, American Association of Poison Control Centers",
        },
    }

    # Urgent (but not emergency) warning signs
    URGENT_RULES = {
        "persistent_fever": {
            "signs": ["fever", "feverish", "temperature", "chills"],
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
            "signs": ["dizzy", "dizziness", "lightheaded", "vertigo"],
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
    def _is_negated(clause: str, match_start: int, match_end: int = 0) -> bool:
        """
        True if a negation word appears within the last few words before the match,
        inside the same clause, AND the negation is genuinely negating the symptom.

        Conservative safety invariants:
        - "no relief from chest pain" -> NOT negated (patient has chest pain without relief)
        - "no improvement in shortness of breath" -> NOT negated
        - "never had chest pain this bad" -> NOT negated (intensifier)
        - "the medicine did not stop the chest pain" -> NOT negated (treatment failure)
        - "not able to stop severe bleeding" -> NOT negated
        - "not only chest pain" -> NOT negated
        - "no chest pain" -> NEGATED (genuine negative)
        """
        preceding_text = clause[:match_start]
        following_text = clause[match_end:] if match_end else clause[match_start:]
        preceding_tokens = _TOKEN_RE.findall(preceding_text)

        recent_tokens = preceding_tokens[-_NEGATION_WINDOW:]
        negation_cues_found = [t for t in recent_tokens if t in _NEGATION_CUES]
        if not negation_cues_found:
            return False

        # Find position of the negation cue in preceding_text
        last_cue = negation_cues_found[-1]
        cue_idx = preceding_text.rfind(last_cue)
        intervening = preceding_text[cue_idx:]

        # Check for failure of relief / treatment / non-negating intervening phrases
        if _NON_NEGATING_INTERVENING.search(intervening):
            return False

        # Check for intensifier following the symptom (e.g. "never had ... this bad/severe/like this")
        if "never" in negation_cues_found and _INTENSIFIER_FOLLOWING.search(following_text):
            return False

        return True

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

        # Evaluate symptom and severity together where required
        norm_sev = _normalize(request.severity)
        if any(term in norm_sev for term in ("severe", "critical", "extreme", "excruciating", "worst", "unbearable", "10/10")):
            norm_main = _normalize(request.main_symptom)
            clauses.append(f"{norm_sev} {norm_main}")
            clauses.append(f"{norm_main} {norm_sev}")
            for assoc in request.associated_symptoms:
                norm_assoc = _normalize(assoc)
                clauses.append(f"{norm_sev} {norm_assoc}")
                clauses.append(f"{norm_assoc} {norm_sev}")

        # If age group is infant (0-2), evaluate infant-specific breathing distress
        age_str = str(getattr(request.age_group, "value", request.age_group)).lower()
        if age_str in ("infant", "0-2", "0-1") or "infant" in str(request.age_group).lower():
            all_text = " ".join([request.main_symptom, *request.associated_symptoms, request.additional_context or ""])
            norm_all = _normalize(all_text)
            for resp_sign in ("rapid breathing", "fast breathing", "breathing fast", "stridor", "wheezing", "grunting", "struggling to breathe"):
                if resp_sign in norm_all:
                    clauses.append("infant struggling to breathe")
                    break

        return clauses

    @classmethod
    def _find_signs(cls, matchers: Tuple[_Matcher, ...], clauses: List[str]) -> List[WarningSign]:
        """Return each sign that has at least one non-negated occurrence."""
        found: List[WarningSign] = []
        for sign, rule, pattern in matchers:
            for clause in clauses:
                if any(not cls._is_negated(clause, m.start(), m.end()) for m in pattern.finditer(clause)):
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
