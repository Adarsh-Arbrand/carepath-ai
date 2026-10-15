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


class TestNegationFailureOfRelief:
    """
    Failure-of-relief and intensifier phrases must not be treated as negating the symptom.
    When a patient says 'no relief from chest pain' or 'medicine did not stop bleeding',
    the symptom is actively present and untreated.
    """

    def test_no_relief_from_chest_pain_is_emergency(self):
        urgency, signs = assess("No relief from chest pain.")
        assert urgency == EMERGENCY
        assert any("chest" in s.sign for s in signs)

    def test_no_improvement_in_shortness_of_breath_is_emergency(self):
        urgency, signs = assess("No improvement in shortness of breath.")
        assert urgency == EMERGENCY
        assert any("breath" in s.sign for s in signs)

    def test_never_had_chest_pain_this_bad_is_emergency(self):
        urgency, signs = assess("Never had chest pain this bad.")
        assert urgency == EMERGENCY
        assert any("chest" in s.sign for s in signs)

    def test_the_medicine_did_not_stop_the_chest_pain_is_emergency(self):
        urgency, signs = assess("The medicine did not stop the chest pain.")
        assert urgency == EMERGENCY
        assert any("chest" in s.sign for s in signs)

    def test_not_able_to_stop_severe_bleeding_is_emergency(self):
        urgency, signs = assess("Not able to stop severe bleeding.")
        assert urgency == EMERGENCY
        assert any("bleeding" in s.sign for s in signs)

    def test_not_only_chest_pain_is_emergency(self):
        urgency, signs = assess("Not only chest pain.")
        assert urgency == EMERGENCY
        assert any("chest" in s.sign for s in signs)

    def test_unable_to_stop_heavy_bleeding_is_emergency(self):
        urgency, signs = assess("unable to stop heavy bleeding")
        assert urgency == EMERGENCY

    def test_never_felt_chest_pain_this_severe_is_emergency(self):
        urgency, signs = assess("never felt chest pain this severe")
        assert urgency == EMERGENCY

    def test_genuine_negatives_still_suppress(self):
        for text in ("no chest pain", "not experiencing chest pain", "never had chest pain", "without chest pain"):
            urgency, signs = assess("mild headache", context=text)
            assert urgency != EMERGENCY, text
            assert not any("chest" in s.sign for s in signs), text

    def test_mixed_statement_still_flags_positive_symptom(self):
        urgency, signs = assess("no chest pain but shortness of breath")
        assert urgency == EMERGENCY
        assert any("breath" in s.sign for s in signs)
        assert not any("chest" in s.sign for s in signs)


class TestDeterministicEmergencyDetection:
    """
    Realistic emergency phrasings, combined severity evaluations, infant distress,
    and avoidance of false positive substring collisions.
    """

    def test_realistic_breathing_difficulties_are_emergencies(self):
        phrases = [
            "struggling to breathe",
            "gasping for air",
            "gasping for breath",
            "hard to breathe",
            "cant catch my breath",
            "unable to catch my breath",
            "lips turning blue",
            "turning blue",
            "severe wheezing",
            "suffocating",
        ]
        for phrase in phrases:
            urgency, _ = assess(phrase)
            assert urgency == EMERGENCY, phrase

    def test_heavy_bleeding_phrasings_are_emergencies(self):
        phrases = [
            "bleeding heavily",
            "bleeding will not stop",
            "bleeding won't stop",
            "spurting blood",
            "gushing blood",
            "losing a lot of blood",
            "blood soaking through",
            "massive bleeding",
        ]
        for phrase in phrases:
            urgency, _ = assess(phrase)
            assert urgency == EMERGENCY, phrase

    def test_chest_pressure_tightness_and_heart_attack_are_emergencies(self):
        phrases = [
            "pressure on my chest",
            "elephant sitting on my chest",
            "crushing chest pain",
            "tightness in my chest",
            "think i am having a heart attack",
            "having a heart attack",
            "pain radiating to left arm",
            "pain radiating to jaw",
            "cardiac arrest",
        ]
        for phrase in phrases:
            urgency, _ = assess(phrase)
            assert urgency == EMERGENCY, phrase

    def test_severe_abdominal_pain_combined_with_severity(self):
        # Abdominal / stomach / belly pain combined with severe severity
        for symptom in ("abdominal pain", "stomach pain", "belly pain"):
            request = SymptomRequest(
                age_group=AgeGroup.ADULT,
                main_symptom=symptom,
                duration="6 hours",
                onset="sudden",
                severity="severe",
                associated_symptoms=[],
                warning_signs=[],
            )
            urgency, signs = TriageEngine.evaluate(request)
            assert urgency == EMERGENCY, f"{symptom} with severe severity must be emergency"
            assert any("abdomen" in s.sign or "abdominal" in s.sign or "stomach" in s.sign or "belly" in s.sign for s in signs)

    def test_mild_abdominal_pain_is_urgent_not_emergency(self):
        request = SymptomRequest(
            age_group=AgeGroup.ADULT,
            main_symptom="abdominal pain",
            duration="2 days",
            onset="gradual",
            severity="mild",
            associated_symptoms=[],
            warning_signs=[],
        )
        urgency, _ = TriageEngine.evaluate(request)
        assert urgency == URGENT  # urgent due to persistent pain, but NOT emergency

    def test_infant_breathing_emergencies(self):
        # Infant distress signs
        for sign in ("chest sucking in", "ribs sucking in", "skin sucking in", "flaring nostrils", "grunting while breathing", "baby struggling to breathe"):
            urgency, _ = assess(sign)
            assert urgency == EMERGENCY, sign

        # Fast breathing in an infant under 1 year
        infant_request = SymptomRequest(
            age_group=AgeGroup.INFANT,
            main_symptom="rapid breathing",
            duration="1 hour",
            onset="sudden",
            severity="moderate",
            associated_symptoms=[],
            warning_signs=[],
        )
        urgency, _ = TriageEngine.evaluate(infant_request)
        assert urgency == EMERGENCY, "Rapid breathing in infant must trigger emergency"

    def test_substring_false_positives_prevented(self):
        # "fit" inside "fitting" must not trigger seizure emergency
        urgency, _ = assess("mild headache", context="replacing a bathroom light fitting")
        assert urgency != EMERGENCY

        # "ache" inside "teacher" must not trigger urgent persistent pain
        urgency, signs = assess("tired", context="I was speaking with my teacher")
        assert urgency == ROUTINE
        assert not any("ache" in s.sign for s in signs)

        # "pain" inside "painting" must not trigger urgent persistent pain
        urgency, signs = assess("dry cough", context="I spent the afternoon painting the bedroom")
        assert urgency == ROUTINE
        assert not any("pain" in s.sign for s in signs)


class TestSuicideAndOverdoseDetection:
    """
    Mental health crisis, self-harm, suspected overdose, and realistic seizure phrasing.
    """

    def test_suicide_phrasing_triggers_emergency(self):
        phrases = [
            "I want to die",
            "I wish I was dead",
            "I wish I were dead",
            "I don’t want to live anymore",
            "I dont want to live anymore",
            "no reason to live",
            "better off dead",
            "thinking of ending my life",
        ]
        for phrase in phrases:
            urgency, signs = assess(phrase)
            assert urgency == EMERGENCY, phrase
            assert any("die" in s.sign or "dead" in s.sign or "live" in s.sign or "suicid" in s.sign or "life" in s.sign for s in signs), phrase

    def test_overdose_phrasing_triggers_emergency(self):
        phrases = [
            "suspected overdose",
            "swallowed a bottle of pills",
            "swallowed a bottle",
            "took an entire bottle",
            "took all my pills",
            "drank poison",
            "drank bleach",
        ]
        for phrase in phrases:
            urgency, signs = assess(phrase)
            assert urgency == EMERGENCY, phrase
            assert any("overdose" in s.sign or "pill" in s.sign or "poison" in s.sign or "bottle" in s.sign or "bleach" in s.sign for s in signs), phrase

    def test_seizure_phrasing_triggers_emergency(self):
        phrases = [
            "having a seizure",
            "grand mal",
            "shaking uncontrollably",
            "violent shaking",
            "epileptic fit",
            "jerking uncontrollably",
        ]
        for phrase in phrases:
            urgency, signs = assess(phrase)
            assert urgency == EMERGENCY, phrase
            assert any("seiz" in s.sign or "fit" in s.sign or "shak" in s.sign or "jerk" in s.sign or "mal" in s.sign for s in signs), phrase

