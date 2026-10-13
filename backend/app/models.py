from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from enum import Enum


class AgeGroup(str, Enum):
    INFANT = "0-2"
    CHILD = "3-12"
    TEEN = "13-17"
    ADULT = "18-64"
    SENIOR = "65+"


class UrgencyLevel(str, Enum):
    EMERGENCY = "emergency"
    URGENT = "urgent"
    ROUTINE = "routine"
    UNKNOWN = "unknown"


class SymptomRequest(BaseModel):
    age_group: AgeGroup
    main_symptom: str = Field(..., min_length=1, max_length=500)
    duration: str = Field(..., min_length=1, max_length=200)
    onset: str = Field(..., min_length=1, max_length=200)
    severity: str = Field(..., min_length=1, max_length=200)
    associated_symptoms: List[str] = Field(default_factory=list, max_length=20)
    warning_signs: List[str] = Field(default_factory=list, max_length=20)
    additional_context: Optional[str] = Field(None, max_length=1000)

    @field_validator("associated_symptoms", "warning_signs")
    @classmethod
    def validate_symptom_lists(cls, v):
        if v:
            for item in v:
                if len(item) > 500:
                    raise ValueError("Each symptom must be 500 characters or less")
        return v


class FollowUpRequest(BaseModel):
    assessment_id: str = Field(..., min_length=1, max_length=100)
    answer: str = Field(..., min_length=1, max_length=1000)


class WarningSign(BaseModel):
    sign: str
    description: str
    source: str


class AssessmentResponse(BaseModel):
    urgency: UrgencyLevel
    warning_signs_detected: List[WarningSign]
    reasoning: str
    recommended_next_steps: List[str]
    limitations: List[str]
    is_demo_mode: bool
    needs_follow_up: bool = False
    follow_up_question: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    version: str


class ConfigResponse(BaseModel):
    ai_enabled: bool
    demo_mode: bool
