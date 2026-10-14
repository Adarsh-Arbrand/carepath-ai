# CarePath AI - Project Handoff

**Hackathon:** Hack2Skill PromptWars × HackWkie AI Code Submission
**Date:** October 14, 2026
**Status:** Ready for public GitHub and deployment

---

## Overview

CarePath AI is an intelligent healthcare navigation assistant that provides safe, explainable guidance on appropriate next steps for health concerns. It uses a deterministic safety engine independent of AI systems, with optional AI-powered explanations.

**Key Principle:** This is NOT a diagnostic system. It provides informational guidance only and is NOT a substitute for professional medical advice.

---

## Architecture

### Backend (Python/FastAPI)
- **Framework:** FastAPI 0.143.0
- **Python Version:** 3.14.7
- **Structure:**
  - `app/main.py` - API endpoints and application logic
  - `app/triage.py` - Deterministic safety engine (rule-based)
  - `app/ai_service.py` - AI service abstraction with Gemini integration
  - `app/models.py` - Pydantic data models
  - `tests/` - 47 tests covering all components

### Frontend (React/TypeScript)
- **Framework:** React 19.2.8 with Vite 8.3.4
- **Styling:** Tailwind CSS v4.3.3
- **Build:** TypeScript 6.0.3
- **Structure:**
  - `src/App.tsx` - Main application with routing
  - `src/components/` - Disclaimer, Questionnaire, Results
  - `src/api.ts` - API client
  - `src/types.ts` - TypeScript type definitions
  - `src/test/` - 25 frontend tests

### Decision Flow
1. User completes guided questionnaire
2. Frontend sends assessment to `/api/assess`
3. Backend validates request (Pydantic schemas, length limits)
4. **Safety Engine** evaluates symptoms against emergency/urgent rules (runs BEFORE AI)
5. **AI Service** (if configured) provides explanatory context
6. Results combine safety determination + AI explanation
7. AI output cannot downgrade safety classification
8. Frontend displays results with urgency, reasoning, and next steps

---

## Completed Work

### ✅ Implemented Features

**Backend:**
- Deterministic Safety Engine with 10 emergency rules and 4 urgent rules
- AI Service abstraction supporting Google Gemini API
- Demo mode fallback when AI unavailable
- API endpoints: `/api/health`, `/api/config`, `/api/assess`, `/api/follow-up`
- Rate limiting (simple in-memory, 10 requests/60 seconds)
- CORS middleware
- Pydantic validation with length limits
- Error handling with custom exception handlers

**Frontend:**
- Guided multi-step questionnaire (6 steps)
- Age group selection (5 groups: infant, child, teen, adult, senior)
- Symptom, duration, onset, severity inputs
- Associated symptoms and warning signs tracking
- Results display with urgency banners (emergency/urgent/routine/unknown)
- Medical disclaimer component (persistent)
- About and Privacy pages
- Print functionality for assessment summary
- Progress indicator
- Responsive design with Tailwind CSS v4

**Safety & Privacy:**
- No database storage of assessment histories
- No names, addresses, or identifying information collected
- No localStorage or analytics for sensitive data
- API keys exclusively on backend
- CORS restrictions and rate limiting
- Clear privacy messaging throughout

### ✅ Test Results

**Backend Tests:** 47/47 PASSED (0.79s)
- 9 AI service tests
- 15 API endpoint tests
- 23 triage engine tests

**Frontend Tests:** 25/25 PASSED (4.26s)
- 15 Results component tests
- 10 Questionnaire component tests

**Production Build:** SUCCESS
- Build time: 362ms
- CSS: 18.11 kB (gzipped: 4.29 kB)
- JS: 247.74 kB (gzipped: 75.15 kB)

### ✅ Security Verifications

**Gemini Integration:**
- ✅ API key read from server-side environment variable (`os.getenv("GEMINI_API_KEY")`)
- ✅ API key never exposed to frontend
- ✅ No API key references in frontend code
- ✅ Demo mode works without API key (tests confirm)
- ✅ API key removed from `.env` (now empty for security)

**Safety Rules Cannot Be Overridden:**
- ✅ Safety engine runs BEFORE AI in `main.py` (line 139)
- ✅ Safety urgency determined independently
- ✅ AI only provides explanatory context, never changes urgency
- ✅ AI system prompt explicitly states urgency must be respected
- ✅ Test `test_cannot_downgrade_safety` confirms architecture

**No Committed Secrets/Artifacts:**
- ✅ `.env` excluded from Git (verified with `git check-ignore`)
- ✅ No venv, node_modules, dist, __pycache__, .pytest_cache in git
- ✅ Test files use mock API keys (not real secrets)
- ✅ No hardcoded secrets in source code
- ✅ `.gitignore` properly configured

**Emergency-Rule Precedence:**
- ✅ Emergency rules checked first (lines 195-207 in triage.py)
- ✅ If any emergency sign detected, immediately returns EMERGENCY
- ✅ Urgent rules checked only if no emergency signs (lines 209-221)
- ✅ Emergency rules cannot be overridden by urgent rules

**Input Validation:**
- ✅ Pydantic models with Field validators
- ✅ Length limits: main_symptom (500), duration/onset/severity (200), additional_context (1000)
- ✅ List limits: associated_symptoms (20), warning_signs (20)
- ✅ Each list item limited to 500 characters
- ✅ Age group validated as enum
- ✅ Empty string validation for required fields

**CORS Configuration:**
- ✅ Currently `allow_origins=["*"]` for development
- ⚠️ Added documentation comment for production deployment
- ⚠️ Should be restricted to specific domains for production

**Error Handling:**
- ✅ Pydantic validation errors return 422 with details
- ✅ General exceptions return 500 with generic message
- ✅ AI service errors fall back to demo mode
- ✅ Rate limiting returns 429 when exceeded
- ⚠️ Using `print()` for logging (documented for production upgrade)

---

## Remaining Bugs & Known Limitations

### Critical Issues (RESOLVED)
- ✅ **RESOLVED:** Real API key was in `.env` - removed and replaced with empty string

### High Priority (Recommended for Production)
1. **Deprecated Google Gemini package**
   - Using `google.generativeai` which is deprecated
   - Should migrate to `google.genai` package
   - Non-blocking: current package still works

2. **CORS configuration too permissive**
   - `allow_origins=["*"]` allows any origin
   - Should restrict to specific domains for production
   - Documented with comment in code

### Medium Priority (Acceptable for Hackathon)
3. **Rate limiting is in-memory only**
   - Not production-ready for distributed systems
   - Should use Redis or similar for production
   - Documented in code comments

4. **Follow-up endpoint is a stub**
   - Returns hardcoded response
   - Doesn't integrate with assessment state
   - Documented as demonstration feature

5. **No actual database persistence**
   - Follow-up feature would require assessment storage
   - Current design is stateless by design (privacy feature)
   - Documented in README

### Low Priority (Known Limitations per README)
6. Rule set is narrow (not comprehensive)
7. No medical history integration
8. Single language (English only)
9. Generic demo mode explanations
10. No offline support

---

## Local Setup Commands

### Prerequisites
- Python 3.11 or later
- Node.js 20 or later
- npm or yarn

### Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # On Windows
# source venv/bin/activate  # On Unix/Linux/macOS
pip install -r requirements.txt
```

### Frontend Setup
```bash
cd frontend
npm install
```

### Environment Variables
```bash
# Copy .env.example to .env in the root directory
cp .env.example .env

# Edit .env to add GEMINI_API_KEY if using AI features (optional)
# For demo mode, leave GEMINI_API_KEY empty
```

### Run Development Servers

**Terminal 1 (Backend):**
```bash
cd backend
venv\Scripts\activate  # On Windows
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm run dev
```

### Access the Application
- Frontend: http://localhost:5173 (or port shown in terminal)
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/api/docs

### Run Tests

**Backend Tests:**
```bash
cd backend
venv\Scripts\activate
pytest tests/ -v
```

**Frontend Tests:**
```bash
cd frontend
npm test -- --run
```

### Production Build
```bash
cd frontend
npm run build
```

---

## Deployment Instructions

### Google Cloud Run Deployment

**Option 1: Using gcloud CLI**
```bash
gcloud run deploy carepath-ai \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --set-env-vars=GEMINI_API_KEY=$GEMINI_API_KEY
```

**Option 2: Using Docker**
```bash
docker build -t carepath-ai .
docker tag carepath-ai gcr.io/PROJECT_ID/carepath-ai
docker push gcr.io/PROJECT_ID/carepath-ai
gcloud run deploy carepath-ai \
  --image gcr.io/PROJECT_ID/carepath-ai \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080
```

### Production Configuration Checklist
- [ ] Set `GEMINI_API_KEY` environment variable (optional, for AI features)
- [ ] Restrict CORS origins to specific domains
- [ ] Implement Redis-based rate limiting for production
- [ ] Set up proper logging (replace `print()` with logging module)
- [ ] Configure monitoring and alerting
- [ ] Review and update emergency contact number (currently 112 for India)

---

## Next Steps for Claude.ai

### Immediate (Before Public Release)
1. **Commit current changes**
   - Stage and commit the modified files
   - Ensure `.env` remains uncommitted
   - Push to GitHub

2. **Update README with latest changes**
   - Document Tailwind CSS v4 migration
   - Add note about CORS configuration for production
   - Update test results if needed

### Short-term (Production Hardening)
1. **Migrate to `google.genai` package**
   - Update `requirements.txt`
   - Update `ai_service.py` imports
   - Update tests if needed
   - Run tests to verify

2. **Implement production logging**
   - Replace `print()` with Python `logging` module
   - Configure log levels
   - Add structured logging for monitoring

3. **Restrict CORS for production**
   - Create environment variable for allowed origins
   - Update CORS middleware configuration
   - Test with specific domains

### Medium-term (Feature Enhancements)
1. **Expand safety rule set**
   - Add more emergency warning signs
   - Add more urgent condition rules
   - Cite additional reputable sources

2. **Implement follow-up properly**
   - Add database for assessment storage (with consent)
   - Implement assessment ID tracking
   - Integrate follow-up with assessment state

3. **Add multi-language support**
   - Internationalization (i18n) setup
   - Translate UI elements
   - Translate safety rules and messages

### Long-term (Future Improvements)
1. **Additional AI providers**
   - Support for OpenAI, Anthropic, etc.
   - Provider abstraction already in place
   - Configuration-based provider selection

2. **Enhanced testing**
   - Add E2E tests with Playwright/Cypress
   - Add load testing
   - Add security testing

3. **Analytics (with consent)**
   - Anonymous, aggregate analytics
   - System improvement insights
   - Privacy-first design

---

## Important Notes

### Security
- ⚠️ **NEVER commit `.env` file** - it contains sensitive API keys
- ⚠️ **NEVER expose API keys to frontend** - always server-side only
- ⚠️ **NEVER allow unrestricted CORS in production** - restrict to specific domains
- ✅ **ALWAYS run safety engine before AI** - AI cannot override safety rules
- ✅ **ALWAYS treat user input as untrusted** - prompt injection protection in place

### Medical Disclaimer
This tool provides general information only and is NOT a substitute for professional medical advice, diagnosis, or treatment. It has NOT been clinically validated and is NOT a certified medical device. Always seek the advice of a qualified healthcare provider.

### Privacy
- No persistent storage by default
- No identifying information collected
- No logging of request bodies or health information
- Transient processing only

---

## File Structure

```
carepath-ai/
├── .env                      # Environment variables (NOT in git)
├── .env.example              # Environment template
├── .gitignore                # Git ignore rules
├── Dockerfile                # Docker configuration
├── README.md                 # Project documentation
├── HANDOFF.md                # This file
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── ai_service.py     # AI service abstraction
│   │   ├── main.py           # FastAPI application
│   │   ├── models.py         # Pydantic models
│   │   └── triage.py         # Safety engine
│   ├── requirements.txt      # Python dependencies
│   ├── tests/                # Backend tests (47 tests)
│   └── venv/                 # Python virtual environment (NOT in git)
└── frontend/
    ├── dist/                 # Production build (NOT in git)
    ├── node_modules/         # npm dependencies (NOT in git)
    ├── package.json          # npm configuration
    ├── postcss.config.js     # PostCSS configuration
    ├── public/               # Static assets
    ├── src/
    │   ├── api.ts            # API client
    │   ├── components/       # React components
    │   │   ├── Disclaimer.tsx
    │   │   ├── Questionnaire.tsx
    │   │   ├── Results.tsx
    │   │   └── __tests__/    # Frontend tests (25 tests)
    │   ├── App.tsx           # Main application
    │   ├── index.css         # Global styles
    │   ├── main.tsx          # Entry point
    │   └── types.ts          # TypeScript types
    ├── tsconfig.app.json     # TypeScript config
    ├── tsconfig.json         # TypeScript root config
    ├── tsconfig.node.json    # TypeScript node config
    ├── vite.config.ts        # Vite configuration
    └── vitest.config.ts      # Vitest configuration
```

---

## Contact & Support

For questions or issues related to this project, please refer to the README.md or create an issue in the GitHub repository.

**Hackathon:** Hack2Skill PromptWars × HackWkie AI Code Submission
**License:** Created for hackathon submission
