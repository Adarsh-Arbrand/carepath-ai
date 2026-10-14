"""
Regression tests for the deterministic safety engine (triage.py).

These cover failure modes found in an audit of commit 6b42533:

* Unicode (curly) apostrophes were not normalized, so "can’t breathe" was missed.
* Any negation word within 50 characters suppressed a symptom, even across
  clause boundaries ("no chest pain but shortness of breath"), inside other
  words ("piano"), or across separate form fields.
* Substring matching flagged unrelated words ("benefit" -> "fit", "spain" -> "pain").

Rule of thumb for every test here: when in doubt the engine must stay MORE
conservative (higher urgency), never less.

NOTE: These are software regression tests, not clinical validation.
"""

from app.models import SymptomRequest, AgeGroup, UrgencyLevel
from app.triage import TriageEngine

EMERGENCY = UrgencyLevel.EMERGENCY
URGENT = UrgencyLevel.URGENT
ROUTINE = UrgencyLevel.ROUTINE


def assess(
    main="mild headache",
    *,
    duration="2 days",
    onset="gradual",
    severity="moderate",
    associated=(),
    warning=(),
    context=None,
):
    request = SymptomRequest(
        age_group=AgeGroup.ADULT,
        main_symptom=main,
        duration=duration,
        onset=onset,
        severity=severity,
        associated_symptoms=list(associated),
        warning_signs=list(warning),
        additional_context=context,
    )
    return TriageEngine.evaluate(request)


class TestUnicodeApostrophes:
    """Curly/typographic apostrophes (phones, word processors) must behave like ASCII."""

    def test_curly_apostrophe_cant_breathe_is_emergency(self):
        urgency, signs = assess("I can’t breathe")
        assert urgency == EMERGENCY
        assert any("breathe" in s.sign for s in signs)

    def test_curly_apostrophe_cant_stop_bleeding_is_emergency(self):
        urgency, _ = assess("I can’t stop bleeding")
        assert urgency == EMERGENCY

    def test_other_apostrophe_variants_are_emergency(self):
        variants = {
            "U+2018": "‘",
            "U+201B": "‛",
            "U+02BC": "ʼ",
            "U+00B4": "´",
            "backtick": "`",
            "fullwidth": "＇",
        }
        for name, apostrophe in variants.items():
            urgency, _ = assess(f"I can{apostrophe}t breathe")
            assert urgency == EMERGENCY, f"apostrophe variant {name} was missed"

    def test_apostrophe_missing_entirely_is_emergency(self):
        for text in ("i cant breathe", "I cant stop bleeding"):
            urgency, _ = assess(text)
            assert urgency == EMERGENCY, text

    def test_curly_apostrophe_negation_still_works(self):
        urgency, signs = assess(
            "mild headache", context="I don’t have chest pain"
        )
        assert urgency != EMERGENCY
        assert not any("chest" in s.sign for s in signs)

    def test_zero_width_characters_do_not_hide_a_symptom(self):
        urgency, _ = assess("chest​ pain")
        assert urgency == EMERGENCY


class TestNegationScope:
    """A negation must only suppress the symptom it actually governs."""

    def test_contrast_word_ends_negation_scope(self):
        urgency, signs = assess("no chest pain but shortness of breath")
        assert urgency == EMERGENCY
        assert any("breath" in s.sign for s in signs)
        assert not any("chest" in s.sign for s in signs)

    def test_comma_ends_negation_scope(self):
        urgency, _ = assess(
            "Doctor said no fever, but I have severe abdominal pain"
        )
        assert urgency == EMERGENCY

    def test_uncertain_not_sure_does_not_suppress(self):
        urgency, _ = assess("not sure what it is but I have chest pain")
        assert urgency == EMERGENCY

    def test_not_knowing_does_not_suppress(self):
        urgency, _ = assess("I do not know if I have chest pain")
        assert urgency == EMERGENCY

    def test_and_ends_negation_scope(self):
        urgency, _ = assess("I have no fever and chest pain")
        assert urgency == EMERGENCY

    def test_negation_in_another_form_field_does_not_leak(self):
        urgency, _ = assess("tired", severity="not severe", associated=["chest pain"])
        assert urgency == EMERGENCY

        urgency, _ = assess("tired", duration="no change", associated=["coughing blood"])
        assert urgency == EMERGENCY

        urgency, _ = assess("tired", onset="never before", warning=["difficulty breathing"])
        assert urgency == EMERGENCY

    def test_negation_must_be_a_whole_word(self):
        # "piano" ends in "no", "know" contains "no", "nothing"/"nose" start with "no"
        for text in (
            "after playing piano I have chest pain",
            "I know I have chest pain",
            "nose bleed and chest pain",
            "nothing helps my chest pain",
        ):
            urgency, _ = assess(text)
            assert urgency == EMERGENCY, text

    def test_symptom_after_earlier_negated_mention_is_still_detected(self):
        urgency, _ = assess(
            "mild headache",
            context="never had chest pain before, but now I have chest pain",
        )
        assert urgency == EMERGENCY

    def test_negation_after_other_symptom_in_same_text_is_irrelevant(self):
        urgency, _ = assess("no headache, severe chest pain")
        assert urgency == EMERGENCY

    def test_genuine_negations_still_suppress(self):
        cases = [
            "no chest pain",
            "not experiencing any chest pain",
            "never had chest pain",
            "without chest pain",
            "I don't have chest pain",
            "I do not have any difficulty breathing",
            "no chest pain or shortness of breath",
        ]
        for text in cases:
            urgency, signs = assess("mild headache", context=text)
            assert urgency != EMERGENCY, text
            assert not signs or all(
                "chest" not in s.sign and "breath" not in s.sign for s in signs
            ), text


class TestMatchingPrecision:
    """Signs match at word starts, not inside unrelated words."""

    def test_unrelated_words_do_not_trigger_emergency(self):
        for text in (
            "wondering about the benefit of vitamins",
            "doing a fitness class",
            "bought a new outfit",
        ):
            urgency, _ = assess("mild cough", context=text)
            assert urgency != EMERGENCY, text

    def test_unrelated_words_do_not_trigger_urgent(self):
        urgency, signs = assess("sneezing", context="just got back from Spain")
        assert urgency == ROUTINE
        assert signs == []

    def test_existing_word_variants_are_still_matched(self):
        # These matched before the change through plain substring search.
        urgent_cases = ["painful knee", "headache", "stomach ache", "it hurts", "feverish", "persistent vomiting"]
        for text in urgent_cases:
            urgency, _ = assess(text)
            assert urgency in (URGENT, EMERGENCY), text

        emergency_cases = [
            "my child is having fits",
            "had a fit this morning",
            "seizures",
            "convulsions",
            "he is unconscious",
            "overdosed on tablets",
        ]
        for text in emergency_cases:
            urgency, _ = assess(text)
            assert urgency == EMERGENCY, text

    def test_known_limitation_fit_as_adjective_is_still_flagged(self):
        # "fit" is a British word for seizure. Whole-word "fit" stays an emergency
        # trigger (over-triage is the safe direction). Documented limitation; change
        # only with clinical review.
        urgency, _ = assess("mild cough", context="otherwise I feel fit and healthy")
        assert urgency == EMERGENCY


class TestNoRuleWasWeakened:
    """Every configured sign must still trigger by itself, in any casing/apostrophe style."""

    def test_every_emergency_sign_triggers_alone(self):
        for rule_name, rule in TriageEngine.EMERGENCY_RULES.items():
            for sign in rule["signs"]:
                for text in (sign, sign.upper(), sign.replace("'", "’")):
                    urgency, signs = assess(text)
                    assert urgency == EMERGENCY, f"{rule_name}: {text!r}"
                    assert signs, f"{rule_name}: {text!r}"

    def test_every_urgent_sign_triggers_alone(self):
        for rule_name, rule in TriageEngine.URGENT_RULES.items():
            for sign in rule["signs"]:
                urgency, _ = assess(sign)
                assert urgency in (URGENT, EMERGENCY), f"{rule_name}: {sign!r}"

    def test_emergency_is_never_downgraded_by_urgent_or_negated_text(self):
        urgency, _ = assess(
            "severe chest pain",
            associated=["no fever", "no headache", "not dizzy"],
            context="no vomiting, no chills",
        )
        assert urgency == EMERGENCY

    def test_warning_signs_field_is_evaluated(self):
        urgency, _ = assess("tired", warning=["slurred speech"])
        assert urgency == EMERGENCY
