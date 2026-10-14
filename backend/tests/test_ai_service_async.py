"""
Tests for the non-blocking AI path (ai_service.get_explanation_async) and the
AI_TIMEOUT setting.

The Gemini SDK call is synchronous. These tests make sure it no longer blocks the
event loop, that a slow call falls back to the deterministic demo explanation, and
that the configured timeout is actually passed to the SDK.

Tests are plain functions that use asyncio.run, so they do not depend on
pytest-asyncio configuration.
"""

import asyncio
import time
from contextlib import contextmanager
from unittest.mock import Mock, patch

from app.models import SymptomRequest, AgeGroup, UrgencyLevel
from app.ai_service import AIService, DEFAULT_AI_TIMEOUT_SECONDS

LLM_TEXT = """
Possibilities to consider:
- Muscle strain
- Tension headache

Additional context that would help:
- How long it has lasted

What a professional might weigh:
- Physical examination
"""


def _request():
    return SymptomRequest(
        age_group=AgeGroup.ADULT,
        main_symptom="headache",
        duration="2 hours",
        onset="gradual",
        severity="mild",
    )


@contextmanager
def ai_service(generate_content, timeout="30"):
    """An enabled AIService whose Gemini model is a mock driven by `generate_content`."""
    env = {"GEMINI_API_KEY": "test-key", "AI_TIMEOUT": timeout}
    with patch.dict("os.environ", env, clear=True), patch("app.ai_service.genai") as genai:
        genai.types.GenerationConfig = Mock
        model = Mock()
        model.generate_content.side_effect = generate_content
        genai.GenerativeModel.return_value = model
        service = AIService()
        yield service, model


def _ok_response(*_args, **_kwargs):
    response = Mock()
    response.text = LLM_TEXT
    return response


def _slow_response(seconds):
    def generate(*_args, **_kwargs):
        time.sleep(seconds)
        return _ok_response()

    return generate


class TestAsyncExplanation:
    def test_async_success_matches_sync_behaviour(self):
        with ai_service(_ok_response) as (service, _model):
            explanation, is_demo = asyncio.run(
                service.get_explanation_async(_request(), UrgencyLevel.ROUTINE, "none")
            )
        assert is_demo is False
        assert "Muscle strain" in explanation.general_possibilities

    def test_disabled_service_returns_demo_without_calling_model(self):
        with patch.dict("os.environ", {}, clear=True):
            service = AIService()
        explanation, is_demo = asyncio.run(
            service.get_explanation_async(_request(), UrgencyLevel.ROUTINE, "none")
        )
        assert is_demo is True
        assert explanation.general_possibilities

    def test_provider_error_falls_back_to_demo(self):
        def boom(*_a, **_k):
            raise RuntimeError("provider down")

        with ai_service(boom) as (service, _model):
            _explanation, is_demo = asyncio.run(
                service.get_explanation_async(_request(), UrgencyLevel.URGENT, "x")
            )
        assert is_demo is True

    def test_slow_call_times_out_and_falls_back_to_demo(self):
        with ai_service(_slow_response(2.0), timeout="1") as (service, _model):

            async def timed():
                started = time.perf_counter()
                result = await service.get_explanation_async(
                    _request(), UrgencyLevel.EMERGENCY, "x"
                )
                return result, time.perf_counter() - started

            (explanation, is_demo), elapsed = asyncio.run(timed())

        assert is_demo is True
        assert explanation.general_possibilities
        assert elapsed < 1.8, f"response waited {elapsed:.2f}s for a 1s timeout"

    def test_slow_call_does_not_block_the_event_loop(self):
        with ai_service(_slow_response(1.0)) as (service, _model):

            async def run():
                gaps = []

                async def heartbeat():
                    last = time.perf_counter()
                    while True:
                        await asyncio.sleep(0.05)
                        now = time.perf_counter()
                        gaps.append(now - last)
                        last = now

                beat = asyncio.create_task(heartbeat())
                await asyncio.sleep(0.2)  # let the heartbeat establish a baseline
                await service.get_explanation_async(_request(), UrgencyLevel.ROUTINE, "x")
                # Give the heartbeat a chance to run again: if the call had blocked the
                # loop, the stall is only recorded on the heartbeat's next iteration.
                await asyncio.sleep(0.2)
                beat.cancel()
                return max(gaps)

            worst_gap = asyncio.run(run())

        # With a blocking call the loop would stall for ~1.0s.
        assert worst_gap < 0.4, f"event loop stalled for {worst_gap:.2f}s"


class TestTimeoutConfiguration:
    def test_timeout_is_passed_to_the_sdk(self):
        with ai_service(_ok_response, timeout="7") as (service, model):
            service.get_explanation(_request(), UrgencyLevel.ROUTINE, "none")
        assert model.generate_content.call_args.kwargs["request_options"] == {"timeout": 7}

    def test_invalid_timeout_values_fall_back_to_default(self):
        for raw in ("abc", "", "0", "-5", "1.5"):
            with patch.dict("os.environ", {"AI_TIMEOUT": raw}, clear=True):
                assert AIService().timeout == DEFAULT_AI_TIMEOUT_SECONDS, raw

    def test_valid_timeout_is_used(self):
        with patch.dict("os.environ", {"AI_TIMEOUT": "12"}, clear=True):
            assert AIService().timeout == 12
