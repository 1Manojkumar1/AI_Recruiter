---
title: AI Recruiter
emoji: 🎯
colorFrom: blue
colorTo: purple
sdk: streamlit
sdk_version: 1.39.0
app_file: app.py
pinned: false
license: mit
---

# AI Recruiter — Candidate Ranking Demo

Multi-factor AI-powered candidate ranking system for the Redrob Hackathon.

## Features

- **Semantic Search**: sentence-transformers embeddings for candidate-JD matching
- **Multi-Factor Scoring**: 6 weighted dimensions (skill, semantic, experience, platform, achievement, education)
- **Trap Detection**: Automatic penalization of non-tech roles, consulting-only backgrounds, and honeypots
- **Explainable AI**: Strengths, weaknesses, and hiring recommendations for each candidate

## How to Use

1. Paste a job description in the text area
2. Adjust scoring weights in the sidebar
3. Click "Rank Candidates" to see the top candidates ranked by fit

## Architecture

Two-stage ranking pipeline:
1. **Stage 1**: Fast metadata filter (skills, experience, seniority) → Top 500
2. **Stage 2**: Semantic re-ranking (sentence-transformer embeddings) → Top N

## Tech Stack

- Python, sentence-transformers, numpy, Streamlit
- Backend: FastAPI, React, TypeScript, Tailwind CSS
