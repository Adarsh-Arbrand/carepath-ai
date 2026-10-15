"""
CarePath AI - Main Application

FastAPI application serving both the API and the React frontend.
"""

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import ValidationError
import time
import os
from typing import Dict
import uuid

from app.models import (
    SymptomRequest,
    FollowUpRequest,
    AssessmentResponse,
    HealthResponse,
    ConfigResponse,
    UrgencyLevel,
)
from app.triage import TriageEngine
from app.ai_service import AIService


# Rate limiting (simple in-memory for demo)
# In production, use Redis or similar
rate_limit_store: Dict[str, list] = {}
RATE_LIMIT_REQUESTS = 10
RATE_LIMIT_WINDOW = 60  # seconds


app = FastAPI(
    title="CarePath AI",
    description="Intelligent healthcare navigation assistant",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS middleware
# Configure allowed origins via ALLOWED_ORIGINS environment variable
# Format: comma-separated list of origins, e.g., "https://example.com,http://localhost:5173"
# If not set, defaults to localhost for development
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:8000")
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,  # No authentication/cookies in this app
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Initialize services
ai_service = AIService()


def check_rate_limit(client_id: str) -> bool:
    """Simple rate limiting check."""
    now = time.time()
    if client_id not in rate_limit_store:
        rate_limit_store[client_id] = []

    # Remove old requests outside the window
    rate_limit_store[client_id] = [
        t for t in rate_limit_store[client_id] if now - t < RATE_LIMIT_WINDOW
    ]

    if len(rate_limit_store[client_id]) >= RATE_LIMIT_REQUESTS:
        return False

    rate_limit_store[client_id].append(now)
    return True


def get_client_id(request: Request) -> str:
    """Get client identifier for rate limiting."""
    # Use IP address (in production, consider more sophisticated methods)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Invalid request data", "errors": exc.errors()},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    # NOTE: Using print for demo. Production should use proper logging (e.g., logging module)
    print(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred"},
    )


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="healthy", version="1.0.0")


@app.get("/api/config", response_model=ConfigResponse)
async def get_config():
    """Public configuration (no secrets)."""
    return ConfigResponse(
        ai_enabled=ai_service.enabled,
        demo_mode=not ai_service.enabled,
    )


@app.post("/api/assess", response_model=AssessmentResponse)
async def assess_symptoms(request: Request, data: SymptomRequest):
    """
    Evaluate symptom assessment.

    This endpoint:
    1. Runs the deterministic safety engine
    2. Calls AI for explanatory context (if available)
    3. Returns structured assessment with urgency and guidance
    """
    # Rate limiting
    client_id = get_client_id(request)
    if not check_rate_limit(client_id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
        )

    # Run safety engine first (independent of AI)
    safety_urgency, warning_signs = TriageEngine.evaluate(data)

    # Build safety reasoning
    safety_reasoning = ""
    if warning_signs:
        safety_reasoning = "Warning signs detected: " + "; ".join(
            [ws.description for ws in warning_signs]
        )
    else:
        safety_reasoning = "No specific emergency warning signs detected based on provided information."

    emergency_number = TriageEngine.get_emergency_contact()

    # P0-D: Return deterministic emergency result immediately WITHOUT invoking or waiting for AI service
    if safety_urgency == UrgencyLevel.EMERGENCY:
        is_crisis = any(
            ("suicidal" in ws.description.lower() or "crisis" in ws.description.lower() or "self-harm" in ws.description.lower())
            or any(k in ws.sign for k in ("suicid", "die", "dead", "live", "self harm", "hurt myself", "harming myself", "kill myself", "end my life", "ending my life", "take my own life"))
            for ws in warning_signs
        )
        is_overdose = any(
            ("overdose" in ws.description.lower() or "poison" in ws.description.lower() or "chemical ingestion" in ws.description.lower())
            or any(k in ws.sign for k in ("overdos", "pill", "poison", "bottle", "bleach", "chemical"))
            for ws in warning_signs
        )

        if is_crisis and is_overdose:
            next_steps = [
                f"Contact emergency services immediately ({emergency_number}) or call the Tele-MANAS mental health helpline (14416 / 1800-891-4416)",
                "Do not induce vomiting unless explicitly directed by a poison control or medical professional",
                "If safe to do so, locate and retain the medication packaging, bottle, or substance for emergency responders",
                "Stay with someone you trust - do not remain alone",
                "If the person is unconscious, having difficulty breathing, or having a seizure, place them in the recovery position and call emergency services immediately",
            ]
            reasoning = (
                safety_reasoning
                + "\n\n"
                + "Recommended action: Immediate crisis intervention and emergency medical evaluation for suspected overdose are required right now."
            )
        elif is_crisis:
            next_steps = [
                f"Contact emergency services immediately ({emergency_number}) or call the Tele-MANAS mental health helpline (14416 / 1800-891-4416)",
                "Stay with someone you trust - do not remain alone",
                "Remove any harmful objects or medications from your immediate surroundings",
                "Reach out immediately to a trusted family member, mental health professional, or hospital emergency room",
            ]
            reasoning = (
                safety_reasoning
                + "\n\n"
                + "Recommended action: Immediate crisis support and safety evaluation are required. Please reach out for help right now."
            )
        elif is_overdose:
            next_steps = [
                f"Contact emergency services immediately ({emergency_number})",
                "Do not induce vomiting unless explicitly directed by a poison control or medical professional",
                "If safe to do so, locate and retain the medication packaging, bottle, or substance for emergency responders",
                "If the person is unconscious, having difficulty breathing, or having a seizure, place them in the recovery position and call emergency services immediately",
            ]
            reasoning = (
                safety_reasoning
                + "\n\n"
                + "Recommended action: Suspected overdose or poisoning is a time-critical medical emergency. Seek immediate emergency evaluation."
            )
        else:
            next_steps = [
                f"Contact emergency services immediately ({emergency_number})",
                "Do not drive yourself - have someone else drive or call emergency transport",
                "Stay calm and try to remain still",
                "If possible, have someone stay with you",
            ]
            reasoning = (
                safety_reasoning
                + "\n\n"
                + "Recommended action: Immediate emergency medical evaluation is required. Do not delay seeking care."
            )

        limitations = [
            "This is an informational tool, not a diagnostic system",
            "This has not been clinically validated",
            "This cannot replace professional medical evaluation",
            "Always consult a qualified healthcare provider for medical concerns",
            "Emergency/crisis resources cited (112, Tele-MANAS 14416) are for India; if outside India, contact your local emergency services (e.g. 988 in US/Canada, 999 in UK)",
        ]

        # P0-E: Never prompt for additional information in an emergency
        return AssessmentResponse(
            urgency=safety_urgency,
            warning_signs_detected=warning_signs,
            reasoning=reasoning,
            recommended_next_steps=next_steps,
            limitations=limitations,
            is_demo_mode=True,  # live AI bypassed for emergency safety
            needs_follow_up=False,
            follow_up_question=None,
        )

    # For non-emergency assessments (URGENT, ROUTINE, UNKNOWN), query AI asynchronously with timeout
    try:
        ai_explanation, is_demo_mode = await ai_service.get_explanation_async(
            data, safety_urgency, safety_reasoning
        )
    except Exception as e:
        print(f"AI service error: {e}")
        ai_explanation, is_demo_mode = ai_service._get_demo_explanation(
            data, safety_urgency
        ), True

    # P0-C: For URGENT assessments, suppress untrusted AI-authored next steps and possibilities
    if safety_urgency == UrgencyLevel.URGENT:
        next_steps = [
            "Seek medical attention today",
            "Contact your healthcare provider or urgent care",
            "Monitor symptoms for any changes",
            f"If symptoms worsen or you develop severe symptoms, seek emergency care immediately ({emergency_number})",
        ]
        reasoning = (
            safety_reasoning
            + "\n\n"
            + "Recommended action: Urgent medical evaluation is recommended today to assess persistent or concerning symptoms."
        )
        is_demo_mode = True  # AI possibilities and recommendations suppressed for safety
    elif safety_urgency == UrgencyLevel.ROUTINE:
        next_steps = [
            "Schedule an appointment with a healthcare provider",
            "Monitor symptoms for any changes",
            "If symptoms worsen or new symptoms develop, seek medical attention",
            "Rest and stay hydrated as appropriate",
        ]
        # Include sanitized AI considerations for routine cases
        next_steps.extend(ai_explanation.professional_considerations)
        reasoning = (
            safety_reasoning
            + "\n\n"
            + "General possibilities: "
            + "; ".join(ai_explanation.general_possibilities)
        )
    else:  # UNKNOWN
        next_steps = [
            "More information is needed for proper assessment",
            "Consider consulting a healthcare provider",
            "If you are concerned about your symptoms, seek medical attention",
        ]
        next_steps.extend(ai_explanation.professional_considerations)
        reasoning = (
            safety_reasoning
            + "\n\n"
            + "General possibilities: "
            + "; ".join(ai_explanation.general_possibilities)
        )

    limitations = [
        "This is an informational tool, not a diagnostic system",
        "This has not been clinically validated",
        "This cannot replace professional medical evaluation",
        "Always consult a qualified healthcare provider for medical concerns",
    ]
    if is_demo_mode:
        limitations.append(
            "Operating in demo mode - AI explanations are generalized"
        )

    # Determine if follow-up is needed (NEVER on emergency or urgent)
    needs_follow_up = False
    follow_up_question = None

    if safety_urgency not in (UrgencyLevel.EMERGENCY, UrgencyLevel.URGENT):
        if len(data.main_symptom) < 10 and not data.associated_symptoms:
            needs_follow_up = True
            follow_up_question = "Could you describe any other symptoms you're experiencing, or provide more details about how the symptom feels?"

    return AssessmentResponse(
        urgency=safety_urgency,
        warning_signs_detected=warning_signs,
        reasoning=reasoning,
        recommended_next_steps=next_steps,
        limitations=limitations,
        is_demo_mode=is_demo_mode,
        needs_follow_up=needs_follow_up,
        follow_up_question=follow_up_question,
    )


@app.post("/api/follow-up", response_model=AssessmentResponse)
async def process_follow_up(request: Request, data: FollowUpRequest):
    """
    Process a follow-up response.

    In a more sophisticated implementation, this would:
    1. Retrieve the original assessment
    2. Incorporate the new information
    3. Re-run the assessment

    For this demo, we provide a simple acknowledgment.
    """
    # Rate limiting
    client_id = get_client_id(request)
    if not check_rate_limit(client_id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
        )

    # In a real implementation, we would:
    # 1. Look up the assessment by ID
    # 2. Update with new information
    # 3. Re-run the assessment

    # For demo, return a simple response
    return AssessmentResponse(
        urgency=UrgencyLevel.UNKNOWN,
        warning_signs_detected=[],
        reasoning="Follow-up information received. In a full implementation, this would update the assessment.",
        recommended_next_steps=[
            "Please consult a healthcare provider with complete information",
            "A professional evaluation is recommended",
        ],
        limitations=[
            "This is a demonstration of the follow-up flow",
            "Full assessment requires complete information",
        ],
        is_demo_mode=True,
        needs_follow_up=False,
    )


# Serve static files from frontend build (for production)
# For development, the frontend runs separately
frontend_build_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "frontend",
    "dist"
)

if os.path.exists(frontend_build_path):
    app.mount("/static", StaticFiles(directory=os.path.join(frontend_build_path, "static")), name="static")

    @app.get("/")
    async def serve_frontend():
        return FileResponse(os.path.join(frontend_build_path, "index.html"))

    @app.get("/{path:path}")
    async def catch_all(path: str):
        # Prevent path traversal attacks
        # Normalize the path and ensure it stays within frontend_build_path
        normalized_path = os.path.normpath(path)
        if normalized_path.startswith("..") or os.path.isabs(normalized_path):
            # Reject path traversal attempts
            return FileResponse(os.path.join(frontend_build_path, "index.html"))

        file_path = os.path.join(frontend_build_path, normalized_path)
        # Ensure the resolved path is still within frontend_build_path
        real_path = os.path.realpath(file_path)
        real_build_path = os.path.realpath(frontend_build_path)
        if not real_path.startswith(real_build_path):
            # Reject path traversal attempts
            return FileResponse(os.path.join(frontend_build_path, "index.html"))

        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_build_path, "index.html"))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
