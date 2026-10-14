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
# NOTE: allow_origins=["*"] is for development/demo only.
# For production deployment, restrict to specific domains.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
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

    # Get AI explanation (or demo mode fallback)
    try:
        ai_explanation, is_demo_mode = ai_service.get_explanation(
            data, safety_urgency, safety_reasoning
        )
    except Exception as e:
        print(f"AI service error: {e}")
        ai_explanation, is_demo_mode = ai_service._get_demo_explanation(
            data, safety_urgency
        ), True

    # Build recommended next steps based on urgency
    if safety_urgency == UrgencyLevel.EMERGENCY:
        emergency_number = TriageEngine.get_emergency_contact()
        next_steps = [
            f"Contact emergency services immediately ({emergency_number})",
            "Do not drive yourself - have someone else drive or call emergency transport",
            "Stay calm and try to remain still",
            "If possible, have someone stay with you",
        ]
    elif safety_urgency == UrgencyLevel.URGENT:
        next_steps = [
            "Seek medical attention today",
            "Contact your healthcare provider or urgent care",
            "Monitor symptoms for any changes",
            "If symptoms worsen, seek emergency care",
        ]
    elif safety_urgency == UrgencyLevel.ROUTINE:
        next_steps = [
            "Schedule an appointment with a healthcare provider",
            "Monitor symptoms for any changes",
            "If symptoms worsen or new symptoms develop, seek medical attention",
            "Rest and stay hydrated as appropriate",
        ]
    else:  # UNKNOWN
        next_steps = [
            "More information is needed for proper assessment",
            "Consider consulting a healthcare provider",
            "If you are concerned about your symptoms, seek medical attention",
        ]

    # Add AI-provided considerations
    next_steps.extend(ai_explanation.professional_considerations)

    # Build limitations
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

    # Determine if follow-up is needed
    needs_follow_up = False
    follow_up_question = None

    # Simple logic: if information is very limited, ask for more
    if len(data.main_symptom) < 10 and not data.associated_symptoms:
        needs_follow_up = True
        follow_up_question = "Could you describe any other symptoms you're experiencing, or provide more details about how the symptom feels?"

    return AssessmentResponse(
        urgency=safety_urgency,
        warning_signs_detected=warning_signs,
        reasoning=safety_reasoning + "\n\n" + "General possibilities: " + "; ".join(ai_explanation.general_possibilities),
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
