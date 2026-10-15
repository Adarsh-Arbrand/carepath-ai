# CarePath AI

**Challenge:** AI / ML in Healthcare
**Hackathon:** Hack2Skill PromptWars × HackWkie AI Code Submission

## Problem Statement

Many people struggle to understand when to seek emergency care, urgent medical attention, or routine evaluation for their health concerns. Access to clear, safe guidance on appropriate next steps can help individuals make informed decisions about seeking professional medical care.

CarePath AI is an intelligent healthcare navigation assistant that gathers symptom-related context, asks relevant follow-up questions, identifies potential warning signs, and provides safe, explainable guidance on appropriate next steps.

## Intended Users

- Individuals experiencing symptoms who need guidance on appropriate care levels
- Caregivers assessing symptoms for others (children, elderly)
- Anyone seeking informational guidance before deciding to seek professional medical care

## Features

### Guided Symptom Assessment
- Step-by-step questionnaire with progress indication
- Age group selection (infant, child, teen, adult, senior)
- Main symptom description
- Duration and onset information
- Severity assessment
- Associated symptoms tracking
- Warning signs identification
- Optional additional context
- Back and continue navigation without losing answers

### Deterministic Safety Engine
- Independent of AI/LLM systems
- Conservative, rule-based safety checks
- Based on reputable public health guidance (NHS UK, Mayo Clinic, American Heart Association, CDC, WHO)
- Emergency warning sign detection (chest pain, breathing difficulty, stroke symptoms, severe bleeding, etc.)
- Urgent condition detection (persistent fever, pain, vomiting/diarrhea)
- Emergency contact guidance (112 for India, configurable for other regions)
- Conservative, rule-based safety checks designed to err on the side of caution; does not provide diagnostic guarantees and is not clinically comprehensive

### AI-Powered Explanations (Optional)
- Provider abstraction supporting multiple LLM APIs
- Currently supports Google Gemini API
- Structured outputs validated with Pydantic
- Minimum necessary context shared with AI
- System safety instructions cannot be overridden
- Safe demo mode fallback when AI unavailable
- Timeouts, bounded retries, and clear error handling

### Assessment Results
- Urgency level (emergency, urgent, routine, unknown)
- Detected warning signs with sources
- Explainable reasoning
- Recommended next steps
- Important limitations
- Demo mode indicator when applicable
- Follow-up questions for insufficient information
- Printable assessment summary

### Safety & Privacy
- No database storage of assessment histories
- No names, addresses, or identifying information collected
- No localStorage or analytics for sensitive data
- No logging of request bodies or health information
- API keys exclusively on backend
- CORS restrictions and rate limiting
- Clear privacy messaging throughout

## Architecture

### Backend (Python/FastAPI)
- **FastAPI**: Modern, fast web framework with automatic OpenAPI documentation
- **Pydantic**: Data validation and settings management
- **Deterministic Safety Engine**: Rule-based triage system in `backend/app/triage.py`
- **AI Service**: Provider abstraction in `backend/app/ai_service.py`
- **API Endpoints**:
  - `GET /api/health` - Health check
  - `GET /api/config` - Public configuration
  - `POST /api/assess` - Symptom assessment
  - `POST /api/follow-up` - Follow-up processing
- **Serves Frontend**: Built React frontend served from `/` in production

### Frontend (React/Vite/TypeScript)
- **React 19**: UI library
- **Vite**: Fast build tool and dev server
- **TypeScript**: Type safety
- **Tailwind CSS**: Utility-first styling
- **Components**:
  - `Disclaimer`: Persistent medical disclaimer
  - `Questionnaire`: Guided multi-step form
  - `Results`: Assessment display with print support
- **State Management**: React hooks for form state
- **API Client**: Fetch-based with error handling

### Decision-Making Workflow

1. User completes guided questionnaire
2. Frontend sends assessment to `/api/assess`
3. Backend validates request (Pydantic schemas, length limits)
4. **Safety Engine** evaluates symptoms against emergency/urgent rules
5. **Emergency assessments** return deterministic emergency guidance immediately without calling or waiting for AI
6. **Non-emergency assessments** call AI asynchronously with timeout; AI recommendations/possibilities are suppressed for emergency and urgent results
7. AI output cannot alter deterministic safety classification
8. Frontend displays results with urgency, reasoning, and next steps

## Safety and Privacy Design

### Safety
- **Deterministic Safety Engine**: Runs independently of AI, never overridden
- **Conservative Rules**: Err on the side of caution
- **Source Documentation**: All rules cite reputable public health sources
- **No Diagnosis**: System never claims to diagnose, rule out, or treat
- **Clear Limitations**: Always displayed that this is not clinically validated
- **Emergency Guidance**: Prominent display of emergency contact information
- **Prompt Injection Protection**: User text treated as untrusted, system instructions protected

### Privacy
- **No Persistent Storage**: Assessments not stored in database by default
- **Minimal Data Collection**: Only age group (not DOB), symptoms, duration
- **No Identifying Info**: No names, addresses, government IDs
- **No Logging**: Request bodies and health information not logged
- **API Key Security**: Keys stored server-side, never exposed to frontend
- **Transient Processing**: Information used only for current assessment

## AI Provider Configuration

### Optional AI Integration
CarePath AI works fully in demo mode without any AI provider. When configured, AI adds explanatory context but never overrides safety rules.

### Setting Up Gemini API

1. Create a Google Cloud project
2. Enable the Generative Language API
3. Create an API key
4. Set environment variable:
   ```bash
   export GEMINI_API_KEY=your_api_key_here
   export GEMINI_MODEL=gemini-3.8-flash  # Optional, defaults to gemini-3.8-flash
   export AI_TIMEOUT=30  # Optional, defaults to 30 seconds
   ```

### Demo Mode
When no API key is configured, the system operates in demo mode with:
- Deterministic, generalized explanations
- Clear labeling that AI is unavailable
- Full safety engine functionality
- All other features working normally

## Local Setup Instructions

### Prerequisites
- Python 3.11 or later
- Node.js 20 or later
- npm or yarn

### Windows Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd carepath-ai
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Frontend Setup**
   ```bash
   cd ../frontend
   npm install
   ```

4. **Environment Variables**
   ```bash
   # Copy .env.example to .env in the root directory
   # Add your GEMINI_API_KEY if using AI features (optional)
   ```

5. **Run Development Servers**
   
   Terminal 1 (Backend):
   ```bash
   cd backend
   venv\Scripts\activate
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

   Terminal 2 (Frontend):
   ```bash
   cd frontend
   npm run dev
   ```

6. **Access the Application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/api/docs

### Unix/Linux/macOS Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd carepath-ai
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Frontend Setup**
   ```bash
   cd ../frontend
   npm install
   ```

4. **Environment Variables**
   ```bash
   cp .env.example .env
   # Edit .env to add GEMINI_API_KEY if using AI features (optional)
   ```

5. **Run Development Servers**
   
   Terminal 1 (Backend):
   ```bash
   cd backend
   source venv/bin/activate
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

   Terminal 2 (Frontend):
   ```bash
   cd frontend
   npm run dev
   ```

6. **Access the Application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/api/docs

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | No | - | Google Gemini API key for AI features |
| `GEMINI_MODEL` | No | `gemini-3.8-flash` | Gemini model to use |
| `AI_TIMEOUT` | No | `30` | AI request timeout in seconds |
| `PORT` | No | `8000` | Server port |

## API Endpoints

### Health Check
```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### Configuration
```http
GET /api/config
```

**Response:**
```json
{
  "ai_enabled": true,
  "demo_mode": false
}
```

### Symptom Assessment
```http
POST /api/assess
Content-Type: application/json

{
  "age_group": "18-64",
  "main_symptom": "chest pain",
  "duration": "1 hour",
  "onset": "sudden",
  "severity": "severe",
  "associated_symptoms": ["shortness of breath"],
  "warning_signs": [],
  "additional_context": null
}
```

**Response:**
```json
{
  "urgency": "emergency",
  "warning_signs_detected": [
    {
      "sign": "chest pain",
      "description": "Chest pain can indicate heart attack or other serious conditions",
      "source": "American Heart Association, NHS UK"
    }
  ],
  "reasoning": "Warning signs detected: chest pain...",
  "recommended_next_steps": [
    "Contact emergency services immediately (112)",
    "Do not drive yourself - have someone else drive or call emergency transport"
  ],
  "limitations": [
    "This is an informational tool, not a diagnostic system",
    "This has not been clinically validated"
  ],
  "is_demo_mode": false,
  "needs_follow_up": false
}
```

### Follow-up
```http
POST /api/follow-up
Content-Type: application/json

{
  "assessment_id": "test-123",
  "answer": "Yes, I also have nausea"
}
```

## Testing Commands

### Backend Tests (Pytest)
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
pytest tests/ -v
```

**Test Coverage:**
- 138 automated backend tests covering:
  - Emergency rule validation and clinical safety signs (26 tests)
  - Unicode apostrophes, negation scope, failure of relief, temporal markers, and false-positive prevention (58 regression tests)
  - AI provider abstraction, numbered lists, adversarial filtering, and error fallbacks (17 tests)
  - Async non-blocking execution and timeout enforcement (8 tests)
  - API endpoints, validation, injection resistance, emergency AI bypass, and crisis/overdose routing (29 tests)

**Expected Result:** All 138 tests pass

### Frontend Tests (Vitest)
```bash
cd frontend
npm test -- --run
```

**Test Coverage:**
- 25 tests covering:
  - Questionnaire navigation and validation (10 tests)
  - Results display and accessibility (15 tests)

**Expected Result:** All 25 tests pass

### Build Verification
```bash
# Frontend build
cd frontend
npm run build

# Backend type check (if using mypy)
cd backend
mypy app/  # Optional
```

## Deployment Instructions

### Google Cloud Run Deployment

#### Option 1: Using gcloud CLI

1. **Build and Deploy**
   ```bash
   gcloud run deploy carepath-ai \
     --source . \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --port 8080 \
     --set-env-vars=GEMINI_API_KEY=$GEMINI_API_KEY
   ```

2. **Set Environment Variables**
   ```bash
   gcloud run services update carepath-ai \
     --region us-central1 \
     --set-env-vars="GEMINI_API_KEY=your_key,GEMINI_MODEL=gemini-3.8-flash"
   ```

#### Option 2: Using Docker

1. **Build Docker Image**
   ```bash
   docker build -t carepath-ai .
   ```

2. **Tag for Google Artifact Registry**
   ```bash
   docker tag carepath-ai gcr.io/PROJECT_ID/carepath-ai
   ```

3. **Push to Registry**
   ```bash
   docker push gcr.io/PROJECT_ID/carepath-ai
   ```

4. **Deploy to Cloud Run**
   ```bash
   gcloud run deploy carepath-ai \
     --image gcr.io/PROJECT_ID/carepath-ai \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --port 8080
   ```

### Deployment Verification

After deployment:
1. Check health endpoint: `https://<your-url>/api/health`
2. Access the application: `https://<your-url>/`
3. View API docs: `https://<your-url>/api/docs`

## Assumptions

1. **Demo Mode**: The application is fully functional without AI configuration
2. **Single Service**: FastAPI serves both API and built React frontend
3. **Conservative Safety**: Rules are intentionally conservative and may trigger on non-emergency situations
4. **No Persistent Storage**: Assessments are not stored by default
5. **India-Oriented**: Emergency number defaults to 112 (India), but users should use appropriate number for their location
6. **Reputable Sources**: Safety rules based on NHS UK, Mayo Clinic, AHA, CDC, WHO guidance
7. **Not Clinically Validated**: This is a demonstration prototype, not a certified medical device

## Known Limitations

1. **Rule Set Scope**: Initial rule set is narrow and not comprehensive
2. **No Medical History**: System does not incorporate medical history or medications
3. **Limited Follow-up**: Follow-up flow is simplified for demonstration
4. **Single Language**: Currently supports English only
5. **Rate Limiting**: Simple in-memory rate limiting (not production-grade)
6. **AI Dependency**: When AI is configured, availability depends on third-party service
7. **No Offline Support**: Requires internet connection for API calls
8. **Generic Explanations**: Demo mode provides generalized, not personalized explanations

## Future Improvements

1. **Expanded Rule Set**: Add more warning signs based on additional medical guidance
2. **Multi-language Support**: Internationalization for different languages
3. **Enhanced Follow-up**: More sophisticated question routing based on responses
4. **User Accounts**: Optional accounts for history tracking (with consent)
5. **Additional AI Providers**: Support for OpenAI, Anthropic, etc.
6. **Production Rate Limiting**: Redis-based distributed rate limiting
7. **Analytics**: Anonymous, aggregate analytics for system improvement
8. **Mobile App**: Native mobile applications
9. **Integration**: Potential integration with telehealth platforms
10. **Clinical Validation**: Partnership with medical institutions for validation studies

## Important Disclaimer

**CarePath AI is NOT a diagnostic system. It does NOT diagnose, rule out, or treat any disease.**

This tool provides general informational guidance only and is NOT a substitute for professional medical advice, diagnosis, or treatment.

- This is a demonstration prototype
- It has NOT undergone clinical validation
- It is NOT a certified medical device
- Always seek the advice of a qualified healthcare provider
- If you have a medical emergency, call your local emergency services immediately (112 in India, 911 in US)

## License

This project is created for the Hack2Skill PromptWars × HackWkie AI Code Submission hackathon.

## Acknowledgments

- Medical guidance sources: NHS UK, Mayo Clinic, American Heart Association, CDC, WHO
- Built with: FastAPI, React, Vite, TypeScript, Tailwind CSS
- AI integration: Google Gemini API (optional)
