# AI Recruiter — Candidate Ranking Demo

Multi-factor AI-powered candidate ranking system for the Redrob Hackathon.

## Features

- **Multi-Factor Scoring**: 6 weighted dimensions (skill, semantic, experience, platform, achievement, education)
- **Trap Detection**: Automatic penalization of non-tech roles, consulting-only backgrounds, and honeypots
- **Explainable AI**: Strengths, weaknesses, and hiring recommendations for each candidate

## How to Run

```bash
pip install streamlit numpy
streamlit run app.py
```

## How to Use

1. Paste a job description in the text area
2. Adjust scoring weights in the sidebar
3. Click "Rank Candidates" to see the top candidates ranked by fit

## Tech Stack

- Python, numpy, Streamlit
