# AI Recruiter — Intelligent Candidate Discovery & Ranking System

> **Redrob Hackathon Submission** — An AI-powered candidate ranking system that goes beyond keyword matching to understand who truly fits a role.

---

## Table of Contents

- [Problem Statement](#problem-statement)
- [Our Approach](#our-approach)
- [Architecture Overview](#architecture-overview)
- [How It Works](#how-it-works)
  - [Stage 1: Candidate Processing Pipeline](#stage-1-candidate-processing-pipeline)
  - [Stage 2: Job Description Parsing](#stage-2-job-description-parsing)
  - [Stage 3: Two-Stage Ranking Engine](#stage-3-two-stage-ranking-engine)
  - [Stage 4: Explainable AI](#stage-4-explainable-ai)
- [Scoring Dimensions](#scoring-dimensions)
- [Trap & Honeypot Detection](#trap--honeypot-detection)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Quick Start](#quick-start)
  - [Running the Full Pipeline](#running-the-full-pipeline)
  - [Running the API Server](#running-the-api-server)
  - [Running the Frontend](#running-the-frontend)
  - [Docker Deployment](#docker-deployment)
- [API Reference](#api-reference)
- [Ranking Algorithm Deep Dive](#ranking-algorithm-deep-dive)
- [Configuration & Weights](#configuration--weights)
- [Verification & Testing](#verification--testing)
- [Compute Constraints](#compute-constraints)
- [Design Decisions](#design-dedecisions)
- [Known Limitations](#known-limitations)
- [License](#license)

---

## Problem Statement

Recruiters go through hundreds of profiles and still often miss the right person — not because the talent isn't there, but because keyword filters can't see what actually matters. The challenge: build an AI system that ranks candidates the way a great recruiter would — not by matching keywords, but by actually understanding who fits the role.

**The dataset**: 100,000 synthetic candidate profiles with deliberate traps — keyword stuffers, non-technical roles with AI keywords, honeypots with impossible career timelines, and consulting-only backgrounds. The "right answer" is not "find candidates whose skills section contains the most AI keywords."

---

## Our Approach

We built a **multi-factor scoring engine** that evaluates candidates across 6 weighted dimensions:

| Dimension | Weight | What It Measures |
|-----------|--------|------------------|
| **Skill Match** | 30% | Exact, related, and preferred skill coverage with fuzzy matching |
| **Semantic Similarity** | 22% | Embedding-based understanding of role fit beyond keywords |
| **Experience Alignment** | 18% | Years of experience, seniority trajectory, leadership depth |
| **Platform Activity** | 12% | Behavioral signals: response rate, open-to-work, recruiter engagement |
| **Achievement Score** | 10% | Leadership, impact metrics, promotions, patents, publications |
| **Education Score** | 8% | Institution tier, degree level, field relevance |

**Key differentiators:**
- **Two-stage ranking**: Fast metadata filter (top 500) then semantic re-ranking (top 100) — efficient within the 5-minute CPU budget
- **Honeypot defense**: Automatic detection and penalization of impossible profiles (expert skills with 0 duration, career history exceeding total experience)
- **Trap-aware scoring**: Heavy penalties for non-tech titles (-80pts), consulting-only backgrounds (-50pts), and pure-research profiles
- **Template-free reasoning**: Each candidate gets a unique explanation derived from their actual profile data

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DATA FLOW                                    │
│                                                                     │
│  candidates.jsonl ──► Candidate Processing ──► processed_candidates │
│       (100K)              Pipeline                   .jsonl        │
│                                                         │           │
│                                                         ▼           │
│  job_description.txt ──► JD Parser ──► Structured JD                │
│                                         │                           │
│                                         ▼                           │
│                                    Embedding Service                │
│                                    (sentence-transformers)          │
│                                         │                           │
│                    ┌────────────────────┬┘                          │
│                    ▼                    ▼                           │
│            Stage 1: Fast Filter   Stage 2: Re-rank                 │
│            (metadata signals)     (semantic similarity)            │
│            Top 500 candidates     Top 100 candidates               │
│                    │                    │                           │
│                    └────────┬───────────┘                           │
│                             ▼                                       │
│                    Multi-Factor Scoring                             │
│                    (6 dimensions, weighted)                         │
│                             │                                       │
│                             ▼                                       │
│                    submission.csv                                    │
│                    (100 ranked candidates)                          │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                        WEB APPLICATION                              │
│                                                                     │
│  React Frontend ◄──── FastAPI Backend ◄──── Ranking Engine          │
│  (Dashboard,             (REST API)        (same scoring logic)    │
│   Comparison,                                                 │
│   Score Charts)                                                │
└─────────────────────────────────────────────────────────────────────┘
```

---

## How It Works

### Stage 1: Candidate Processing Pipeline

The preprocessing pipeline (`backend/candidate_processing/`) runs once over all 100K candidates using multiprocessing (up to 16 workers):

| Module | What It Does |
|--------|--------------|
| `parser.py` | Loads raw JSONL with error handling for malformed lines |
| `skill_processor.py` | Normalizes skill names via 60+ alias mappings (e.g., "py" → "python", "k8s" → "kubernetes"), computes composite proficiency scores from proficiency level + endorsements + duration |
| `education_analyzer.py` | Scores institutions by tier (1-4), degree level bonus (PhD +15pts, Masters +10pts), and grade normalization |
| `career_analyzer.py` | Detects promotions from title progression, calculates job-switch frequency, career growth score (0-1) |
| `trait_extractor.py` | Infers leadership score (keyword-based), impact score (regex metric detection), domain expertise mapping, and seniority classification (Junior → Principal) |
| `summary_generator.py` | Generates recruiter-friendly paragraph summaries from structured data |
| `redrob_signal_extractor.py` | Extracts and normalizes 23 platform behavioral signals into 4 sub-scores: engagement, visibility, credibility, availability |
| `embedding_generator.py` | Generates 384-dim embeddings via `all-MiniLM-L6-v2` with random-projection fallback for environments without sentence-transformers |

**Output**: `processed_candidates.jsonl` — enriched records with normalized skills, domains, scores, summaries, and platform signals.

### Stage 2: Job Description Parsing

The `JobParser` (`backend/part2/job_parser.py`) extracts structured requirements from free-text JDs:

- **Required skills** — identified via regex section detection + skill alias matching
- **Preferred skills** — secondary skill requirements
- **Experience years** — extracted from patterns like "5-9 years", "5+ years"
- **Seniority level** — mapped from title keywords (Senior, Lead, Staff, Principal)
- **Domain keywords** — matched against a vocabulary of 10 technical domains

### Stage 3: Two-Stage Ranking Engine

```
All 100K candidates
        │
        ▼
┌─────────────────────────┐
│  Stage 1: Fast Filter   │  ◄── Skills, experience, seniority, domain
│  (metadata signals)     │      (no embedding computation)
│  Score all → Top 500    │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Stage 2: Re-rank       │  ◄── Cosine similarity between job and
│  (semantic similarity)  │      candidate embeddings (384-dim)
│  Score top 500 → 100    │      Generated on-the-fly for top 500 only
└───────────┬─────────────┘
            │
            ▼
    Final 100 candidates
    (with score breakdown)
```

**Why two stages?** Generating sentence-transformer embeddings for all 100K candidates would exceed the 5-minute CPU budget. By filtering to 500 first using fast metadata signals, we only compute embeddings for the candidates most likely to make the final cut.

### Stage 4: Explainable AI

The explanation engine (`backend/part4/explanation_engine.py`) generates natural-language reasoning for each candidate:

- **Strengths**: What makes this candidate a good fit (skill coverage, experience match, achievements)
- **Weaknesses**: What's missing or concerning (skill gaps, experience shortfall, leadership gaps)
- **Summary**: A paragraph contextualizing the candidate's fit
- **Recommendation**: Highly Recommended / Recommended / Consider with Reservations / Not Recommended

All explanations are **template-based NLG** — no external LLM API calls, fully offline, deterministic.

---

## Scoring Dimensions

### 1. Skill Match (Weight: 0.30)

```
skill_score = (required_matches × 0.70 + preferred_matches × 0.30) × 100
```

- **Exact match**: Candidate has the skill with score 1.0
- **Related match**: Candidate has a synonym/related skill with score 0.5 (e.g., Flask ↔ FastAPI ↔ Django)
- **No match**: Score 0.0

Uses 60+ alias mappings and 30+ synonym groups covering web frameworks, language families, cloud providers, databases, ML frameworks, and DevOps tools.

### 2. Semantic Similarity (Weight: 0.22)

- Generates 384-dimensional embeddings using `all-MiniLM-L6-v2`
- Computes cosine similarity between job description embedding and candidate profile embedding
- Scaled to 0-100 score
- **Fallback**: If sentence-transformers is unavailable, uses a deterministic random-projection of bag-of-words features (same dimensionality, compatible scoring)

### 3. Experience Alignment (Weight: 0.18)

```
experience_score = base_years_score ± seniority_bonus ± leadership_bonus
```

- Smooth curve: meets/exceeds requirement (85-100), slightly below (60-85), notably below (30-60), far below (0-30)
- Seniority bonus: ±5pts based on level match
- Leadership bonus: up to 5pts for demonstrated people management

### 4. Platform Activity (Weight: 0.12)

Extracts from Redrob's 23 behavioral signals:

| Sub-score | Signals Used |
|-----------|--------------|
| **Engagement** (25%) | Recruiter response rate, avg response time, interview completion rate, application volume |
| **Visibility** (25%) | Profile completeness, recruiter saves, search appearances |
| **Credibility** (25%) | Email/phone verification, LinkedIn, GitHub activity, endorsements, connections |
| **Availability** (25%) | Open-to-work flag, notice period, offer acceptance rate |

### 5. Achievement Score (Weight: 0.10)

| Component | Max Points | Detection Method |
|-----------|------------|------------------|
| Leadership | 25 | Keyword detection: "led team", "managed engineers", "direct reports" |
| Impact | 25 | Keyword + regex: "reduced latency by 40%", "increased revenue" |
| Promotions | 25 | Career history title progression analysis |
| Keyword Achievements | 25 | Scanning for patents, publications, awards, launches |

### 6. Education Score (Weight: 0.08)

- Institution tier scoring (tier_1: 1.0, tier_2: 0.8, tier_3: 0.6, tier_4: 0.4)
- Degree level bonus (PhD: +15pts, Masters: +10pts)
- Field relevance matching

---

## Trap & Honeypot Detection

The dataset contains deliberate traps. Our system handles them at multiple levels:

### Automatic Penalties (Ranking Service)

| Trap Type | Penalty | Detection |
|-----------|---------|-----------|
| Non-tech title | -80pts | Title contains "marketing", "sales", "HR", "accountant", "civil engineer", etc. |
| Consulting-only background | -50pts | All career history at TCS, Infosys, Wipro, Accenture, Cognizant, Capgemini |
| Honeypot profile | -100pts | Expert proficiency in 3+ skills with 0 months duration, or career history > total experience |

### Honeypot Detection Rules (rank.py)

```python
# 1. Expert proficiency in 3+ skills with 0 duration → honeypot
# 2. Single role duration > total experience → honeypot
# 3. Sum of career history durations > total experience + 1.5 years → honeypot
```

### Verification Script Scanning

The `run_verification.py` script scans the top-100 shortlist for:
- Non-technical titles (marketing, sales, operations, HR, accountant, civil, mechanical, support, etc.)
- Data anomalies (current role years > total experience)

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **NLP / Embeddings** | sentence-transformers (all-MiniLM-L6-v2) | 384-dim semantic embeddings |
| **Vector Search** | FAISS (with numpy brute-force fallback) | Candidate retrieval |
| **Scoring** | numpy, scikit-learn | Vectorized multi-factor scoring |
| **Skill Matching** | Custom fuzzy matcher with 60+ aliases | Skill normalization and matching |
| **Backend API** | FastAPI + uvicorn | REST API with async support |
| **Frontend** | React 18 + TypeScript + Tailwind CSS | Interactive dashboard |
| **Charts** | Recharts | Score breakdown visualization |
| **Testing** | pytest, vitest | Unit tests for backend and frontend |
| **Deployment** | Docker + Docker Compose | Containerized deployment |
| **Build** | Vite 5 (frontend), pip (backend) | Development and production builds |

---

## Project Structure

```
AI_Recruiter/
├── README.md                          # This file
├── rank.py                            # Main entry point: generates submission CSV
├── run_verification.py                # One-click verification suite
├── docker-compose.yml                 # Docker deployment (backend + frontend)
├── submission.csv                     # Generated submission (top 100 candidates)
├── AI_Recruiter.csv                   # Final submission file
├── submission_metadata.yaml           # Hackathon submission metadata
├── submission_spec.txt                # Hackathon submission specification
│
├── job_description.txt                # Target job description
├── redrob_signals_doc.txt             # Behavioral signals reference
│
├── backend/
│   ├── main.py                        # Candidate processing pipeline entry point
│   ├── requirements.txt               # Python dependencies
│   ├── Dockerfile                     # Backend Docker image
│   ├── pytest.ini                     # Pytest configuration
│   │
│   ├── candidates.jsonl               # Raw candidate data (100K records)
│   ├── processed_candidates.jsonl     # Enriched candidate data (post-processing)
│   │
│   ├── candidate_processing/          # Stage 1: Data processing pipeline
│   │   ├── config.py                  #   Configuration and constants
│   │   ├── parser.py                  #   JSONL loader
│   │   ├── candidate_processor.py     #   Main orchestrator (multiprocessing)
│   │   ├── skill_processor.py         #   Skill normalization + scoring
│   │   ├── education_analyzer.py      #   Education tier scoring
│   │   ├── career_analyzer.py         #   Career growth analysis
│   │   ├── trait_extractor.py         #   Leadership, impact, seniority inference
│   │   ├── summary_generator.py       #   NLG profile summaries
│   │   ├── redrob_signal_extractor.py #   Platform behavioral signal extraction
│   │   ├── embedding_generator.py     #   Sentence-transformer embeddings
│   │   └── utils.py                   #   Shared utilities
│   │
│   ├── part2/                         # Stage 2: JD parsing + ranking engine
│   │   ├── config.py                  #   Ranking configuration
│   │   ├── job_parser.py              #   JD text → structured requirements
│   │   ├── skill_matcher.py           #   Skill match scoring
│   │   ├── experience_matcher.py      #   Experience match scoring
│   │   ├── domain_matcher.py          #   Domain expertise scoring
│   │   ├── seniority_matcher.py       #   Seniority level scoring
│   │   ├── achievement_scorer.py      #   Achievement scoring
│   │   ├── career_growth.py           #   Career growth scoring
│   │   ├── embedding.py               #   Job embedding generation
│   │   ├── faiss_search.py            #   Vector retrieval (FAISS/numpy)
│   │   ├── ranking_engine.py          #   Ranking orchestrator
│   │   └── explainer.py               #   Structured explanation generation
│   │
│   ├── part3/                         # Stage 3: Refined scoring engine
│   │   ├── services/
│   │   │   └── ranking_service.py     #   Full ranking pipeline with penalties
│   │   ├── scores/
│   │   │   ├── skill_score.py         #   Enhanced skill scoring
│   │   │   ├── semantic_score.py      #   Cosine similarity scoring
│   │   │   ├── experience_score.py    #   Enhanced experience scoring
│   │   │   ├── platform_score.py      #   Redrob platform activity scoring
│   │   │   ├── education_score.py     #   Education scoring
│   │   │   └── achievement_score.py   #   Enhanced achievement scoring
│   │   └── utils/
│   │       ├── weights.py             #   Configurable weight dataclass
│   │       ├── skill_mapper.py        #   60+ aliases, 30+ synonym groups
│   │       └── education_mapper.py    #   Education level scoring
│   │
│   ├── part4/                         # Stage 4: Explainable AI
│   │   ├── explanation_engine.py      #   Natural-language explanations
│   │   └── comparison_engine.py       #   Head-to-head candidate comparison
│   │
│   ├── app/                           # FastAPI production API
│   │   ├── main.py                    #   FastAPI app with lifespan, CORS, routes
│   │   ├── config/
│   │   │   └── settings.py            #   Environment-based configuration
│   │   ├── models/
│   │   │   └── schemas.py             #   Pydantic request/response schemas
│   │   ├── services/
│   │   │   ├── embedding_service.py   #   Embedding generation service
│   │   │   ├── search_service.py      #   Candidate retrieval service
│   │   │   └── ranking_service.py     #   Full ranking pipeline service
│   │   └── routers/
│   │       ├── search.py              #   POST /search
│   │       ├── rank.py                #   POST /rank
│   │       ├── explain.py             #   POST /explain, POST /explain/compare
│   │       └── candidate.py           #   GET /candidate/{id}
│   │
│   └── tests/
│       ├── test_embeddings.py
│       ├── test_ranking.py
│       ├── test_search.py
│       ├── test_explanation_api.py
│       └── test_api.py
│
├── frontend/
│   ├── package.json                   # Node.js dependencies
│   ├── Dockerfile                     # Multi-stage Docker build
│   ├── nginx.conf                     # Nginx config with API proxy
│   ├── index.html                     # HTML entry point
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── tsconfig.json
│   ├── vite.config.ts
│   │
│   ├── src/
│   │   ├── main.tsx                   # React entry point
│   │   ├── App.tsx                    # Router + context provider
│   │   ├── index.css                  # Tailwind imports
│   │   ├── types/
│   │   │   └── index.ts               # TypeScript interfaces for API contracts
│   │   ├── hooks/
│   │   │   └── useCandidates.ts       # React hooks for candidate data
│   │   ├── services/
│   │   │   └── api.ts                 # Axios API client
│   │   ├── context/
│   │   │   └── CandidateContext.tsx    # Global candidate state
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx          # Main ranking dashboard
│   │   │   └── CandidateDetails.tsx   # Individual candidate view
│   │   └── components/
│   │       ├── Navbar.tsx
│   │       ├── JobInput.tsx           # JD text input
│   │       ├── CandidateCard.tsx      # Candidate summary card
│   │       ├── CandidateTable.tsx     # Ranked candidate table
│   │       ├── CandidateComparison.tsx# Side-by-side comparison
│   │       ├── ScoreBreakdownChart.tsx# Radar/bar chart scores
│   │       ├── ExplanationCard.tsx    # AI explanation display
│   │       ├── LoadingSpinner.tsx
│   │       └── ErrorMessage.tsx
│   │
│   └── src/__tests__/                 # Frontend unit tests
│       ├── CandidateCard.test.tsx
│       ├── CandidateTable.test.tsx
│       ├── ExplanationCard.test.tsx
│       ├── ErrorMessage.test.tsx
│       ├── LoadingSpinner.test.tsx
│       └── helpers.test.ts
│
└── [PUB] India_runs_data_and_ai_challenge/
    └── India_runs_data_and_ai_challenge/
        ├── candidates.jsonl            # Official dataset
        ├── job_description.docx        # Official JD (docx format)
        ├── candidate_schema.json       # Candidate data schema
        ├── sample_candidates.json      # Sample candidates for reference
        ├── sample_submission.csv       # Format reference
        ├── validate_submission.py      # Official format validator
        └── redrob_signals_doc.docx     # Behavioral signals documentation
```

---

## Getting Started

### Prerequisites

- **Python 3.10+** (tested on 3.11.4 and 3.12)
- **Node.js 18+** (for frontend)
- **16 GB RAM** recommended (for loading 100K candidates)
- **Docker** (optional, for containerized deployment)

### Quick Start

**1. Clone the repository:**

```bash
git clone https://github.com/AI-Recruiter/ai-recruiter.git
cd ai-recruiter
```

**2. Install Python dependencies:**

```bash
pip install -r backend/requirements.txt
```

**3. (Optional) Install sentence-transformers for embeddings:**

```bash
pip install sentence-transformers
```

> **Note**: The system works without sentence-transformers using a random-projection fallback, but embedding quality will be lower.

**4. Generate the submission CSV:**

```bash
python rank.py --candidates ./backend/processed_candidates.jsonl --out ./submission.csv
```

**5. Validate the submission:**

```bash
python "[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/validate_submission.py" submission.csv
```

**6. Run the full verification suite:**

```bash
python run_verification.py
```

### Running the Full Pipeline

If you need to reprocess candidates from raw data:

```bash
# Step 1: Process all 100K candidates (generates processed_candidates.jsonl)
python -m backend.main

# Step 2: Generate the submission CSV
python rank.py --candidates ./backend/processed_candidates.jsonl --out ./submission.csv
```

**Pipeline options:**

```bash
# Process only first 1000 candidates (for testing)
python -m backend.main --limit 1000

# Skip embedding generation (faster, for debugging)
python -m backend.main --no-embeddings

# Use custom input/output paths
python rank.py \
  --candidates ./backend/processed_candidates.jsonl \
  --raw-candidates "./[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl" \
  --job-description "./[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/job_description.docx" \
  --out ./submission.csv \
  --top-n 100
```

### Running the API Server

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

API docs available at: `http://localhost:8000/docs`

### Running the Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend available at: `http://localhost:5173`

### Docker Deployment

```bash
# Build and start both backend and frontend
docker-compose up --build

# Backend: http://localhost:8000
# Frontend: http://localhost:80
```

---

## API Reference

### POST `/search` — Semantic Candidate Search

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Senior AI Engineer with RAG and vector search experience", "top_k": 20}'
```

**Response:**
```json
{
  "results": [
    {
      "candidate_id": "CAND_0080766",
      "score": 0.8742,
      "profile_summary": "Lead Staff Machine Learning Engineer with 8.8 years...",
      "seniority": "Lead",
      "total_experience_years": 8.8
    }
  ],
  "total": 20,
  "query_time_ms": 45.2
}
```

### POST `/rank` — Full Candidate Ranking

```bash
curl -X POST http://localhost:8000/rank \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "Senior AI Engineer — Founding Team\n\nRequired: Python, embeddings, vector databases...\nExperience: 5-9 years",
    "top_n": 20
  }'
```

**Response:**
```json
{
  "candidates": [
    {
      "candidate_id": "CAND_0080766",
      "rank": 1,
      "final_score": 87.5,
      "skill_score": 92.0,
      "experience_score": 85.0,
      "education_score": 78.0,
      "semantic_score": 88.5,
      "achievement_score": 82.0,
      "platform_score": 75.0,
      "strengths": ["Strong skill coverage: embeddings, vector DB, Python", "..."],
      "weaknesses": ["Notice period of 45 days may delay start"],
      "explanation": "Highly Recommended. This candidate demonstrates...",
      "profile_summary": "Lead Staff ML Engineer with 8.8 years...",
      "seniority": "Lead",
      "total_experience_years": 8.8
    }
  ],
  "total_scored": 100000,
  "query_time_ms": 1250.0,
  "weights_used": {"skill": 0.30, "semantic": 0.22, "experience": 0.18, "platform": 0.12, "achievement": 0.10, "education": 0.08}
}
```

### POST `/explain` — Candidate Explanation

```bash
curl -X POST http://localhost:8000/explain \
  -H "Content-Type: application/json" \
  -d '{"candidate_id": "CAND_0080766", "job_description": "Senior AI Engineer..."}'
```

### POST `/explain/compare` — Head-to-Head Comparison

```bash
curl -X POST http://localhost:8000/explain/compare \
  -H "Content-Type: application/json" \
  -d '{
    "candidate_a_id": "CAND_0080766",
    "candidate_b_id": "CAND_0055992",
    "job_description": "Senior AI Engineer..."
  }'
```

### GET `/candidate/{candidate_id}` — Candidate Profile

```bash
curl http://localhost:8000/candidate/CAND_0080766
```

### GET `/health` — Health Check

```bash
curl http://localhost:8000/health
```

---

## Ranking Algorithm Deep Dive

### Composite Score Calculation

```python
final_score = (
    skill_score      × 0.30 +   # Skill match coverage
    semantic_score   × 0.22 +   # Embedding similarity
    experience_score × 0.18 +   # Years + seniority alignment
    platform_score   × 0.12 +   # Behavioral signals
    achievement_score× 0.10 +   # Leadership + impact + promotions
    education_score  × 0.08     # Institution tier + degree level
) × 100  # Scale to 0-100

# Apply penalties
if non_tech_title:
    final_score -= 80
if consulting_only:
    final_score -= 50
if honeypot_detected:
    final_score -= 100

final_score = max(0, final_score)
```

### Skill Matching Algorithm

```
For each JD required skill:
    Find best match in candidate skills:
        - Exact name match → score 1.0
        - Synonym group match → score 0.5
        - No match → score 0.0

    skill_match_score += matched_score × proficiency_weight × duration_weight

final_skill_score = (required_matches × 0.70 + preferred_matches × 0.30) × 100
```

### Semantic Similarity

```python
# Generate embeddings
job_embedding = sentence_transformer.encode(jd_text)        # 384-dim
candidate_embedding = sentence_transformer.encode(profile)  # 384-dim

# Cosine similarity
similarity = dot(job_embedding, candidate_embedding) / (
    norm(job_embedding) * norm(candidate_embedding)
)

# Scale to 0-100
semantic_score = similarity × 100
```

### Score Normalization

```python
# Min-max normalization across all scored candidates
normalized_score = (score - min_score) / (max_score - min_score)

# Tie-breaking: candidate_id ascending
if score_a == score_b:
    rank_by_candidate_id_ascending()
```

---

## Configuration & Weights

All weights are configurable via `backend/part3/utils/weights.py`:

```python
@dataclass
class RankingWeights:
    skill: float = 0.30        # Skill match
    experience: float = 0.18   # Experience alignment
    semantic: float = 0.22     # Semantic similarity
    education: float = 0.08    # Education quality
    achievement: float = 0.10  # Achievements
    platform: float = 0.12     # Platform activity

# Must sum to 1.0 — validated at runtime
```

**Custom weights via API:**

```json
{
  "job_description": "...",
  "top_n": 100,
  "weights": {
    "skill": 0.35,
    "semantic": 0.25,
    "experience": 0.15,
    "platform": 0.10,
    "achievement": 0.10,
    "education": 0.05
  }
}
```

---

## Verification & Testing

### One-Click Verification

```bash
python run_verification.py
```

This runs 4 checks:

| Check | What It Does |
|-------|-------------|
| 1. Pytest Unit Tests | Runs all tests in `backend/tests/` |
| 2. Ranking Pipeline | Executes `rank.py` and generates submission CSV |
| 3. Format Validator | Runs official `validate_submission.py` against output |
| 4. Trap/Honeypot Scan | Scans top-100 for non-tech titles and data anomalies |

### Running Tests Separately

```bash
# Backend unit tests
python -m pytest backend/tests -v

# Frontend unit tests
cd frontend && npm test

# Specific test file
python -m pytest backend/tests/test_ranking.py -v
```

---

## Compute Constraints

The ranking step must satisfy:

| Constraint | Requirement | Our Implementation |
|-----------|-------------|-------------------|
| **Time** | ≤ 5 minutes | ~2-3 minutes (two-stage filtering reduces embedding computation) |
| **Memory** | ≤ 16 GB | ~4-8 GB (candidates loaded lazily, embeddings computed on-demand) |
| **CPU only** | No GPU required | All scoring is numpy-vectorized |
| **No network** | No API calls during ranking | sentence-transformers runs locally; no external LLM calls |

**How we stay within budget:**

1. **Pre-filter to 500** using fast metadata signals (no embeddings needed)
2. **Generate embeddings only for 500** candidates (not 100K)
3. **Numpy vectorized operations** for all scoring (no Python loops over candidates)
4. **Lazy loading** — candidates loaded once, scored in-place

---

## Design Decisions

### Why Multi-Factor Scoring (Not Pure Embeddings)?

Pure embedding similarity tends to surface candidates who use the same keywords as the JD. Our dataset deliberately includes "keyword stuffers" — candidates who list AI skills but have non-technical career histories. By combining semantic similarity with structured signals (experience, seniority, platform activity), we can distinguish between someone who *lists* "RAG" as a skill and someone who has *built* a recommendation system.

### Why Two-Stage Ranking?

Generating sentence-transformer embeddings for 100K candidates takes ~15-20 minutes on CPU. The 5-minute budget doesn't allow this. By filtering to 500 candidates first using fast metadata scoring (skill match, experience, seniority), we reduce the embedding computation to a manageable subset while retaining the most promising candidates.

### Why Template-Based Explanations (Not LLM)?

The compute constraint prohibits calling external LLM APIs during ranking. Template-based NLG produces deterministic, auditable explanations that can be verified against the candidate's actual profile. This also ensures the system works fully offline.

### Why Platform Behavioral Signals?

A perfect-on-paper candidate who hasn't logged in for 6 months and has a 5% recruiter response rate is, for hiring purposes, not actually available. Platform signals capture this reality and allow the system to down-weight inactive candidates regardless of their profile quality.

### Why FAISS with Numpy Fallback?

FAISS provides fast approximate nearest neighbor search for large-scale retrieval, but it requires compilation and may not be available on all systems. The numpy brute-force fallback ensures the system works everywhere with identical results, just slower for the initial retrieval step.

---

## Known Limitations

1. **Embedding quality without sentence-transformers**: The random-projection fallback produces lower-quality embeddings. For best results, install `sentence-transformers`.

2. **Skill synonym coverage**: While we have 60+ aliases and 30+ synonym groups, there may be domain-specific skill variants we haven't mapped. Contributions welcome.

3. **Explanation specificity**: Template-based NLG can produce somewhat generic explanations for edge cases. LLM-based explanations would be richer but violate the compute constraint.

4. **Static weights**: The current weights are tuned for the "Senior AI Engineer" JD. Different roles may benefit from different weight configurations. The API supports custom weights.

5. **No real-time learning**: The system doesn't learn from recruiter feedback. A production version would incorporate click-through rates, interview outcomes, and hire data.

---

## License

This project was built for the Redrob Intelligent Candidate Discovery & Ranking Challenge (India Runs Data & AI Challenge).

---

## Acknowledgments

- **Redrob AI** for the hackathon challenge and dataset
- **sentence-transformers** for the `all-MiniLM-L6-v2` embedding model
- **FastAPI** for the high-performance async API framework
- **React + Tailwind** for the frontend stack
