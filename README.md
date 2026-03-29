# ResumeMatch AI — AI Resume-Based Job Finder

A full-stack application that parses your resume with an LLM, searches for relevant jobs, and ranks them with match scores and skill gap analysis.

## Architecture

```
┌─────────────────────┐     ┌──────────────────────────────────┐
│   React Frontend    │────▶│       FastAPI Backend             │
│   Vite + Tailwind   │◀────│                                  │
└─────────────────────┘     │  ┌────────────┐ ┌─────────────┐  │
                            │  │ Resume     │ │ LLM Service │  │
                            │  │ Parser     │ │ (HuggingFace│  │
                            │  │ (PDF/DOCX) │ │  / Ollama)  │  │
                            │  └────────────┘ └─────────────┘  │
                            │  ┌────────────┐ ┌─────────────┐  │
                            │  │ Job Search │ │ Ranking     │  │
                            │  │ (SerpAPI / │ │ Engine      │  │
                            │  │  Mock)     │ │ (Rule+LLM)  │  │
                            │  └────────────┘ └─────────────┘  │
                            │  ┌────────────┐ ┌─────────────┐  │
                            │  │ MongoDB /  │ │ Redis /     │  │
                            │  │ In-Memory  │ │ In-Memory   │  │
                            │  └────────────┘ └─────────────┘  │
                            └──────────────────────────────────┘
```

## Pipeline Flow

1. **Upload** → PDF/DOCX resume uploaded and text extracted (PyMuPDF / python-docx)
2. **Parse** → LLM extracts structured profile (skills, experience, roles)
3. **Search** → Jobs fetched from SerpAPI (or mock data in dev)
4. **Rank** → Each job scored via rule-based, LLM, or hybrid method
5. **Display** → Results shown with match %, skill tags, gap analysis

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- (Optional) MongoDB, Redis, OpenAI API key

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env — add your HF_API_TOKEN (free at huggingface.co/settings/tokens)

python main.py
# → http://localhost:8000/docs (Swagger UI)
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

The Vite dev server proxies `/api` to the backend automatically.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `huggingface` | `huggingface` or `ollama` |
| `HF_API_TOKEN` | — | Free token from huggingface.co/settings/tokens |
| `HF_MODEL` | `meta-llama/Llama-3.1-8B-Instruct` | Any HF Inference Providers model |
| `SERPAPI_KEY` | — | SerpAPI key (falls back to mock) |
| `MONGODB_URI` | `mongodb://localhost:27017` | Falls back to in-memory |
| `REDIS_URL` | — | Falls back to in-memory cache |
| `RATE_LIMIT_PER_MINUTE` | `30` | API rate limit |

### Recommended HuggingFace Models (all free via Inference Providers)

| Model | Speed | Quality | Provider |
|---|---|---|---|
| `meta-llama/Llama-3.1-8B-Instruct` | Fast | Good | Cerebras/SambaNova |
| `Qwen/Qwen2.5-72B-Instruct` | Medium | Best | SambaNova |
| `meta-llama/Llama-3.3-70B-Instruct` | Medium | Excellent | Cerebras |
| `deepseek-ai/DeepSeek-V3-0324` | Medium | Excellent | Together/Novita |
| `mistralai/Mistral-Small-24B-Instruct-2501` | Fast | Good | Various |

> **Token setup**: Go to [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens), create a fine-grained token, and enable the **"Make calls to Inference Providers"** permission.

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/upload-resume` | Upload PDF/DOCX |
| `POST` | `/api/extract-profile` | LLM resume parsing |
| `GET` | `/api/profile/{id}` | Retrieve profile |
| `POST` | `/api/jobs` | Search jobs by skills/roles |
| `GET` | `/api/jobs/search` | Quick job search (query params) |
| `POST` | `/api/rank-jobs` | Score and rank jobs |

## Ranking Methods

- **Rule-Based** — Fast skill overlap + keyword matching (no API cost)
- **LLM-Based** — Deep semantic scoring with explanations (uses LLM tokens)
- **Hybrid** — Rule-based pre-filter → LLM on top matches (balanced)

## Project Structure

```
backend/
├── main.py              # FastAPI app with middleware
├── config.py            # Pydantic settings from .env
├── routes/
│   ├── resume.py        # Upload + profile extraction
│   ├── jobs.py          # Job search endpoints
│   └── ranking.py       # Scoring endpoints
├── services/
│   ├── resume_parser.py # PDF/DOCX text extraction
│   ├── llm_service.py   # OpenAI/Ollama with JSON extraction
│   ├── job_search.py    # SerpAPI + mock fallback + caching
│   └── ranking.py       # Dual scoring engine
├── models/
│   └── schemas.py       # Pydantic request/response models
├── database/
│   └── connection.py    # Motor async MongoDB + fallback
├── utils/
│   ├── logger.py        # Production logging
│   ├── cache.py         # Redis / in-memory caching
│   ├── rate_limiter.py  # slowapi rate limiting
│   └── exceptions.py    # Custom exceptions + handler
└── tests/
    └── test_core.py     # Unit tests with mocks

frontend/
├── src/
│   ├── App.jsx          # Pipeline state machine
│   ├── services/api.js  # Axios API client
│   └── components/
│       ├── Header.jsx
│       ├── StepIndicator.jsx
│       ├── ResumeUpload.jsx
│       ├── ProfileCard.jsx
│       ├── JobResults.jsx
│       ├── ScoreRing.jsx
│       ├── SkillGapPanel.jsx
│       └── ErrorBanner.jsx
├── index.html
├── tailwind.config.js
└── vite.config.js
```

## Production Features

- **Async everywhere** — FastAPI async endpoints, Motor async MongoDB, httpx async HTTP
- **Error handling** — Custom exceptions, global handler, proper HTTP status codes
- **Caching** — Redis with in-memory fallback, configurable TTL
- **Rate limiting** — Per-IP limits via slowapi
- **Structured logging** — Timestamped, leveled, file + console output
- **Graceful fallbacks** — No MongoDB? In-memory. No Redis? In-memory. No SerpAPI? Mock data.
- **LLM robustness** — HuggingFace 503 (model loading) + 429 (rate limit) retry with backoff, JSON extraction with fence/preamble stripping, truncation
- **Zero cost** — HuggingFace Inference API free tier, no paid API keys required

## Testing

```bash
cd backend
pytest tests/ -v
```

## Deployment

- **Backend**: Deploy to Render/Railway, set env vars
- **Frontend**: Deploy to Vercel, set `VITE_API_URL` to backend URL
