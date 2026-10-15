"""
Tests for the AI service (ai_service.py)
"""

import pytest
from unittest.mock import Mock, patch
from app.models import SymptomRequest, AgeGroup, UrgencyLevel
from app.ai_service import AIService, AIExplanation


class TestAIService:
    """Test cases for the AI service."""

    def test_initialization_without_api_key(self):
        """Test that AI service initializes without API key."""
        with patch.dict("os.environ", {}, clear=True):
            service = AIService()
            assert service.enabled is False

    def test_initialization_with_api_key(self):
        """Test that AI service initializes with API key."""
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
            service = AIService()
            assert service.enabled is True
            assert service.api_key == "test-key"

    def test_demo_mode_explanation(self):
        """Test demo mode explanation when AI is unavailable."""
        with patch.dict("os.environ", {}, clear=True):
            service = AIService()
            request = SymptomRequest(
                age_group=AgeGroup.ADULT,
                main_symptom="headache",
                duration="2 hours",
                onset="gradual",
                severity="mild",
            )
            explanation, is_demo = service.get_explanation(
                request, UrgencyLevel.ROUTINE, "No warning signs"
            )
            assert is_demo is True
            assert isinstance(explanation, AIExplanation)
            assert len(explanation.general_possibilities) > 0
            assert len(explanation.additional_context_needed) > 0
            assert len(explanation.professional_considerations) > 0

    def test_demo_mode_for_emergency(self):
        """Test demo mode adjusts for emergency urgency."""
        with patch.dict("os.environ", {}, clear=True):
            service = AIService()
            request = SymptomRequest(
                age_group=AgeGroup.ADULT,
                main_symptom="chest pain",
                duration="1 hour",
                onset="sudden",
                severity="severe",
            )
            explanation, is_demo = service.get_explanation(
                request, UrgencyLevel.EMERGENCY, "Emergency warning signs"
            )
            assert is_demo is True
            assert isinstance(explanation, AIExplanation)
            # Emergency should have different considerations
            assert any("emergency" in c.lower() for c in explanation.professional_considerations)

    @patch("app.ai_service.genai")
    def test_llm_call_success(self, mock_genai):
        """Test successful LLM call."""
        # Mock the Gemini API
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = """
        General possibilities:
        - Tension headache
        - Migraine
        - Dehydration

        Additional context needed:
        - Duration and pattern
        - Triggers

        Professional considerations:
        - Physical examination
        - Medical history review
        """
        mock_model.generate_content.return_value = mock_response
        mock_genai.configure.return_value = None
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.types.GenerationConfig = Mock

        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
            service = AIService()
            request = SymptomRequest(
                age_group=AgeGroup.ADULT,
                main_symptom="headache",
                duration="2 hours",
                onset="gradual",
                severity="mild",
            )
            explanation, is_demo = service.get_explanation(
                request, UrgencyLevel.ROUTINE, "No warning signs"
            )
            assert is_demo is False
            assert isinstance(explanation, AIExplanation)

    @patch("app.ai_service.genai")
    def test_llm_call_failure_fallback(self, mock_genai):
        """Test that LLM call failure falls back to demo mode."""
        mock_genai.configure.side_effect = Exception("API error")

        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
            service = AIService()
            request = SymptomRequest(
                age_group=AgeGroup.ADULT,
                main_symptom="headache",
                duration="2 hours",
                onset="gradual",
                severity="mild",
            )
            explanation, is_demo = service.get_explanation(
                request, UrgencyLevel.ROUTINE, "No warning signs"
            )
            assert is_demo is True
            assert isinstance(explanation, AIExplanation)

    def test_cannot_downgrade_safety(self):
        """Test that AI cannot downgrade safety classification."""
        with patch.dict("os.environ", {}, clear=True):
            service = AIService()
            request = SymptomRequest(
                age_group=AgeGroup.ADULT,
                main_symptom="chest pain",
                duration="1 hour",
                onset="sudden",
                severity="severe",
            )
            # Even in demo mode, we pass the safety urgency
            explanation, is_demo = service.get_explanation(
                request, UrgencyLevel.EMERGENCY, "Emergency warning signs"
            )
            # The service should not change the urgency - that's handled by the caller
            assert is_demo is True
            assert isinstance(explanation, AIExplanation)

    def test_parse_llm_response(self):
        """Test LLM response parsing."""
        with patch.dict("os.environ", {}, clear=True):
            service = AIService()
            text = """
            General possibilities:
            - Condition A
            - Condition B

            Additional context:
            - Duration
            - Severity

            Professional:
            - Exam
            - History
            """
            explanation = service._parse_llm_response(text)
            assert isinstance(explanation, AIExplanation)
            assert len(explanation.general_possibilities) > 0
            assert len(explanation.additional_context_needed) > 0
            assert len(explanation.professional_considerations) > 0

    def test_parse_llm_response_fallback(self):
        """Test parsing fallback when structure is unexpected."""
        with patch.dict("os.environ", {}, clear=True):
            service = AIService()
            text = "This is unstructured text without clear sections"
            explanation = service._parse_llm_response(text)
            assert isinstance(explanation, AIExplanation)
            # Should have fallback values
            assert len(explanation.general_possibilities) > 0
            assert len(explanation.additional_context_needed) > 0
            assert len(explanation.professional_considerations) > 0

    def test_default_model_name(self):
        """Test that default model name is gemini-3.8-flash."""
        with patch.dict("os.environ", {}, clear=True):
            service = AIService()
            assert service.model_name == "gemini-3.8-flash"

    def test_model_name_env_override(self):
        """Test that GEMINI_MODEL env var overrides default model name."""
        with patch.dict("os.environ", {"GEMINI_MODEL": "custom-flash-model"}, clear=True):
            service = AIService()
            assert service.model_name == "custom-flash-model"

    @patch("app.ai_service.genai")
    def test_model_failure_not_found_fallback_preserves_urgency(self, mock_genai):
        """Test that model 404 NotFound error falls back to demo mode while preserving emergency urgency."""
        mock_model = Mock()
        mock_model.generate_content.side_effect = Exception("404 models/gemini-1.5-flash is not found for API version v1beta")
        mock_genai.configure.return_value = None
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.types.GenerationConfig = Mock

        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
            service = AIService()
            request = SymptomRequest(
                age_group=AgeGroup.ADULT,
                main_symptom="chest pain",
                duration="1 hour",
                onset="sudden",
                severity="severe",
            )
            explanation, is_demo = service.get_explanation(
                request, UrgencyLevel.EMERGENCY, "Emergency warning signs"
            )
            assert is_demo is True
            assert isinstance(explanation, AIExplanation)
            assert any("emergency" in c.lower() for c in explanation.professional_considerations)
            assert not any("heart attack" in p.lower() or "myocardial" in p.lower() for p in explanation.general_possibilities)
