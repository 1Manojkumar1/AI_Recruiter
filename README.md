# AI Recruiter — Intelligent Candidate Discovery & Ranking System

> **Redrob Hackathon Submission** — An AI-powered candidate ranking system that goes beyond keyword matching to understand who truly fits a role.

**Live Demo**: [huggingface.co/spaces/pandugamanoj9/ai_recruiter](https://huggingface.co/spaces/pandugamanoj9/ai_recruiter)

---

## Problem Statement

Recruiters miss the right candidates because keyword filters can't see what actually matters. The challenge: build an AI system that ranks candidates the way a great recruiter would — not by matching keywords, but by understanding fit.

**The dataset**: 100,000 synthetic candidate profiles with deliberate traps — keyword stuffers, non-technical roles with AI keywords, honeypots with impossible career timelines, and consulting-only backgrounds.

---

## Approach

A **multi-factor scoring engine** evaluating candidates across 6 weighted dimensions:

| Dimension | Weight | What It Measures |
|-----------|--------|------------------|
| **Skill Match** | 30% | Exact, related, and preferred skill coverage with fuzzy matching |
| **Semantic Similarity** | 22% | Embedding-based understanding of role fit beyond keywords |
| **Experience Alignment** | 18% | Years of experience, seniority trajectory, leadership depth |
| **Platform Activity** | 12% | Behavioral signals: response rate, open-to-work, recruiter engagement |
| **Achievement Score** | 10% | Leadership, impact metrics, promotions, patents, publications |
| **Education Score** | 8% | Institution tier, degree level, field relevance |

**Key design choices:**
- **Two-stage ranking**: Fast metadata filter (top 500) then semantic re-ranking (top 100) — fits within the 5-minute CPU budget
- **Honeypot defense**: Automatic detection and penalization of impossible profiles
- **Trap-aware scoring**: Heavy penalties for non-tech titles, consulting-only backgrounds, and pure-research profiles
- **Data-driven reasoning**: Each candidate gets a unique explanation derived from their actual profile

---

## Architecture

```
candidates.jsonl (100K) ──► Processing Pipeline ──► processed_candidates.jsonl
                                                          │
job_description.txt ──► JD Parser ──► Structured JD       │
                                      │                    │
                                      ▼                    │
                                 Embedding Service         │
                                 (sentence-transformers)   │
                                      │                    │
                     ┌────────────────┬┘                    │
                     ▼                ▼                     │
             Stage 1: Fast     Stage 2: Re-rank            │
             Filter (500)      (semantic, top 100)         │
                     │                │                     │
                     └───────┬────────┘                     │
                             ▼                              │
                    Multi-Factor Scoring ◄──────────────────┘
                    (6 dimensions, weighted)
                             │
                             ▼
                    submission.csv (100 ranked candidates)
```

---

## How It Works

### 1. Candidate Processing Pipeline

Preprocesses all 100K candidates using multiprocessing (16 workers):

| Module | Purpose |
|--------|---------|
| `skill_processor.py` | Normalizes skill names via 60+ alias mappings, computes proficiency scores |
| `education_analyzer.py` | Scores institutions by tier (1-4), degree level |
| `career_analyzer.py` | Detects promotions, job-switch frequency, career growth |
| `trait_extractor.py` | Leadership, impact, domain expertise, seniority classification |
| `redrob_signal_extractor.py` | Extracts 23 platform behavioral signals into 4 sub-scores |
| `embedding_generator.py` | 384-dim embeddings via `all-MiniLM-L6-v2` with random-projection fallback |

### 2. JD Parser

Extracts structured requirements from free-text JDs:
- Required/preferred skills via section detection + skill alias matching
- Experience years from patterns like "5-9 years"
- Seniority level from title keywords
- Anti-pattern detection (skills explicitly not wanted)

### 3. Two-Stage Ranking Engine

```
All 100K candidates
        │
        ▼
Stage 1: Fast Filter ──► Top 500 (skills, experience, seniority — no embeddings)
        │
        ▼
Stage 2: Re-rank ──────► Top 100 (cosine similarity + all 6 factors)
```

**Why two stages?** Embedding all 100K candidates takes ~15-20 min on CPU. Filtering to 500 first keeps us under 5 minutes.

### 4. Reasoning Generation

Data-driven reasoning for each candidate referencing:
- YoE fit against JD requirement
- AI skill density and specific skills
- JD required/preferred skill coverage
- Platform signals (open to work, recruiter engagement)

---

## Trap & Honeypot Detection

| Trap Type | Penalty | Detection |
|-----------|---------|-----------|
| Non-tech title | Disqualified | Title contains "marketing", "sales", "HR", "accountant", etc. |
| Consulting-only | -50pts | All career history at TCS, Infosys, Wipro, Accenture, etc. |
| Honeypot profile | Disqualified | Expert skills with 0 duration, career history > total experience |

---

## Getting Started

### Prerequisites

- Python 3.10+
- 16 GB RAM (for 100K candidates)

### Quick Start

```bash
git clone https://github.com/1Manojkumar1/AI_Recruiter.git
cd AI_Recruiter
pip install -r backend/requirements.txt
pip install sentence-transformers
```

### Data Setup

The full candidate dataset is not included in the repo (465MB). To run the ranking pipeline:

1. Download the dataset from [Google Drive](https://drive.google.com/file/d/1MfD47XvVdRKBGRAyzGOxDCEf2ve96Jjo/view)
2. Extract `candidates.jsonl` and `processed_candidates.jsonl`
3. Place them in `backend/` directory:
   ```
   backend/candidates.jsonl
   backend/processed_candidates.jsonl
   ```

**Quick demo without full data:**

The sandbox demo at [huggingface.co/spaces/pandugamanoj9/ai_recruiter](https://huggingface.co/spaces/pandugamanoj9/ai_recruiter) runs with a 200-candidate sample — no data setup needed.

### Generate Submission

```bash
python rank.py
```

Output: `submission.csv` (100 ranked candidates)

### Validate

```bash
python "[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/validate_submission.py" submission.csv
```

### Full Verification

Runs unit tests, ranking pipeline, format validation, and trap detection:

```bash
python run_verification.py
```

### Run Frontend (React Dashboard)

```bash
cd frontend
npm install
npm run dev
```

Opens at `http://localhost:5173`. Requires the backend API running separately:

```bash
# Terminal 1 — Backend
cd backend
python -m uvicorn app.main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm run dev
```

### Run Frontend Tests

```bash
cd frontend
npm test
```

---

## Project Structure

```
AI_Recruiter/
├── rank.py                          # Main entry: generates submission.csv
├── job_description.txt              # Target job description
├── submission.csv                   # Generated output
├── submission_metadata.yaml         # Hackathon metadata
│
├── backend/
│   ├── candidates.jsonl             # Raw 100K candidates (download separately)
│   ├── processed_candidates.jsonl   # Enriched 100K candidates (download separately)
│   ├── candidate_processing/        # Data processing pipeline
│   ├── part2/                       # JD parsing
│   ├── part3/                       # Ranking engine (scoring + weights)
│   ├── part4/                       # Explanation engine
│   └── app/                         # FastAPI REST API
│
├── frontend/                        # React dashboard
├── sandbox/                         # HuggingFace Space demo
└── [PUB] India_runs_data_and_ai_challenge/  # Official dataset
```

---

## Results

| Metric | Value |
|--------|-------|
| Candidates ranked | 100,000 → 100 |
| AI-relevant roles in top 100 | 98/100 |
| Unique reasonings | 100/100 (zero templated) |
| Runtime (CPU) | ~105 seconds |
| JD required skills extracted | python, embeddings, ndcg, mrr, milvus, pinecone, elasticsearch, etc. |
| Seniority correctly matched | Senior (JD asks for 5-9 years) |

**Sample top-5 rankings:**

| Rank | Title | YoE | AI Skills | Key Matches |
|------|-------|-----|-----------|-------------|
| 1 | Senior NLP Engineer | 8.0 | 5 | elasticsearch, milvus, pinecone, qdrant |
| 2 | Lead Staff ML Engineer | 8.8 | 4 | elasticsearch, milvus, opensearch, python |
| 3 | Senior Recommendation Systems Engineer | 5.8 | 3 | embedding, faiss, milvus, opensearch |
| 4 | Senior NLP Engineer | 7.9 | 3 | elasticsearch, faiss, opensearch, pinecone |
| 5 | Senior Applied ML Engineer | 8.0 | 4 | embedding, opensearch, pinecone, qdrant |

---

## Compute Constraints

| Constraint | Requirement | Implementation |
|-----------|-------------|----------------|
| Time | ≤ 5 min | ~105s (two-stage filtering) |
| Memory | ≤ 16 GB | ~4-8 GB (lazy loading) |
| CPU only | No GPU | All scoring is numpy-vectorized |
| No network | No API calls | sentence-transformers runs locally |

---

## Design Decisions

**Why multi-factor scoring (not pure embeddings)?**
Pure embedding similarity surfaces keyword stuffers. Combining semantic similarity with structured signals (experience, seniority, platform) distinguishes someone who *lists* "RAG" from someone who *built* a recommendation system.

**Why two-stage ranking?**
Embedding 100K candidates takes ~15-20 min on CPU. The 5-minute budget requires pre-filtering to 500 using fast metadata signals first.

**Why template-based explanations?**
The compute constraint prohibits external LLM calls. Template-based NLG produces deterministic, auditable explanations that work fully offline.

**Why platform behavioral signals?**
A perfect-on-paper candidate who hasn't logged in for 6 months isn't actually available. Platform signals capture this reality.

---

## License

Built for the Redrob Intelligent Candidate Discovery & Ranking Challenge (India Runs Data & AI Challenge).

---

## Submission Files

| File | Description |
|------|-------------|
| `submission.csv` | Top 100 ranked candidates (required format) |
| `submission_metadata.yaml` | Team info, compute specs, methodology |
| `presentation.pdf` | 10-slide technical presentation |
| `rank.py` | Main entry point — run `python rank.py` to reproduce |
| `README.md` | This file |
