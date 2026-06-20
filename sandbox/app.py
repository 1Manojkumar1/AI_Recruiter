"""
AI Recruiter — HuggingFace Spaces Demo

Streamlit app that demonstrates the candidate ranking system
on a small sample of candidates.

Usage:
    streamlit run app.py
"""

import json
import sys
import time
from pathlib import Path

import streamlit as st
import numpy as np

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Recruiter — Candidate Ranking Demo",
    page_icon="🎯",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SAMPLE_SIZE = 100  # Load first N candidates for the demo
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# ---------------------------------------------------------------------------
# Lazy imports (cached)
# ---------------------------------------------------------------------------
@st.cache_resource
def load_dependencies():
    """Import ranking modules once."""
    # Add backend to path
    backend_dir = str(Path(__file__).resolve().parent / "backend")
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

    from part2.job_parser import JobParser
    from part3.services.ranking_service import rank_candidates
    from app.services.embedding_service import generate_embedding

    return {
        "parser": JobParser(),
        "rank_candidates": rank_candidates,
        "generate_embedding": generate_embedding,
    }


@st.cache_data(show_spinner="Loading candidates...")
def load_sample_candidates(n: int):
    """Load first N processed candidates."""
    candidates = []
    # Try multiple paths
    paths_to_try = [
        Path("processed_candidates.jsonl"),
        Path("backend") / "processed_candidates.jsonl",
        Path(__file__).resolve().parent / "processed_candidates.jsonl",
        Path(__file__).resolve().parent / "backend" / "processed_candidates.jsonl",
    ]

    data_path = None
    for p in paths_to_try:
        if p.exists():
            data_path = p
            break

    if data_path is None:
        return []

    with open(data_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if not line.strip():
                continue
            candidates.append(json.loads(line))
            if i + 1 >= n:
                break
    return candidates


# ---------------------------------------------------------------------------
# Default job description
# ---------------------------------------------------------------------------
DEFAULT_JD = """Senior AI Engineer — Founding Team

Company: Redrob AI (Series A AI-native talent intelligence platform)
Location: Pune/Noida, India (Hybrid)
Experience Required: 5–9 years

What you'd actually be doing:
Own the intelligence layer of Redrob's product — the ranking, retrieval, and matching systems that decide what recruiters see when they search for candidates.

Things you absolutely need:
- Production experience with embeddings-based retrieval systems (sentence-transformers, OpenAI embeddings, BGE, E5, or similar)
- Production experience with vector databases or hybrid search infrastructure (Pinecone, Weaviate, Qdrant, Milvus, OpenSearch, Elasticsearch, FAISS)
- Strong Python
- Hands-on experience designing evaluation frameworks for ranking systems (NDCG, MRR, MAP)

Things we'd like you to have:
- LLM fine-tuning experience (LoRA, QLoRA, PEFT)
- Experience with learning-to-rank models (XGBoost-based or neural)
- Prior exposure to HR-tech, recruiting tech, or marketplace products
- Background in distributed systems or large-scale inference optimization
"""


# ---------------------------------------------------------------------------
# Main UI
# ---------------------------------------------------------------------------
def main():
    st.title("AI Recruiter — Candidate Ranking Demo")
    st.markdown("Multi-factor AI-powered candidate ranking for the Redrob Hackathon.")

    # Load dependencies
    deps = load_dependencies()

    # Sidebar
    with st.sidebar:
        st.header("Configuration")
        sample_size = st.slider(
            "Candidate pool size",
            min_value=50,
            max_value=500,
            value=SAMPLE_SIZE,
            step=50,
            help="Number of candidates to load from the processed dataset.",
        )
        top_n = st.slider(
            "Top N to rank",
            min_value=5,
            max_value=100,
            value=20,
            step=5,
        )

        st.divider()
        st.markdown("**Scoring Weights**")
        weights = {}
        weights["skill"] = st.slider("Skill", 0.0, 0.5, 0.30, 0.05)
        weights["semantic"] = st.slider("Semantic", 0.0, 0.5, 0.22, 0.05)
        weights["experience"] = st.slider("Experience", 0.0, 0.5, 0.18, 0.05)
        weights["platform"] = st.slider("Platform", 0.0, 0.5, 0.12, 0.05)
        weights["achievement"] = st.slider("Achievement", 0.0, 0.5, 0.10, 0.05)
        weights["education"] = st.slider("Education", 0.0, 0.5, 0.08, 0.05)

        total = sum(weights.values())
        if abs(total - 1.0) > 0.01:
            st.warning(f"Weights sum to {total:.2f} (should be 1.0)")
        else:
            st.success(f"Weights sum to {total:.2f}")

    # Main content
    tab_rank, tab_about = st.tabs(["Rank Candidates", "About"])

    with tab_rank:
        # Job description input
        jd_text = st.text_area(
            "Job Description",
            value=DEFAULT_JD,
            height=250,
            help="Paste a job description. The system will parse required skills, experience, and seniority level.",
        )

        if st.button("Rank Candidates", type="primary", use_container_width=True):
            if not jd_text.strip():
                st.error("Please enter a job description.")
                return

            # Load candidates
            with st.spinner(f"Loading {sample_size} candidates..."):
                candidates = load_sample_candidates(sample_size)

            if not candidates:
                st.error(
                    "No candidates found. Make sure processed_candidates.jsonl "
                    "is in the working directory or in backend/."
                )
                return

            # Parse JD
            with st.spinner("Parsing job description..."):
                parsed_jd = deps["parser"].parse(jd_text)
                all_skills = parsed_jd.get("required_skills", []) + parsed_jd.get("preferred_skills", [])

                structured_jd = {
                    "title": "Senior AI Engineer",
                    "skills": all_skills,
                    "required_skills": parsed_jd.get("required_skills", []),
                    "preferred_skills": parsed_jd.get("preferred_skills", []),
                    "experience": parsed_jd.get("experience", 5),
                    "education": "",
                    "seniority": parsed_jd.get("seniority", "Senior"),
                    "summary": jd_text[:500],
                }

            # Display parsed JD
            with st.expander("Parsed Job Description", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Required Skills:** {', '.join(parsed_jd.get('required_skills', []))}")
                    st.markdown(f"**Preferred Skills:** {', '.join(parsed_jd.get('preferred_skills', []))}")
                with col2:
                    st.markdown(f"**Experience:** {parsed_jd.get('experience', 'N/A')} years")
                    st.markdown(f"**Seniority:** {parsed_jd.get('seniority', 'N/A')}")

            # Generate job embedding
            with st.spinner("Generating job embedding..."):
                job_embedding = deps["generate_embedding"](jd_text)

            # Stage 1: Fast filter
            with st.spinner(f"Stage 1: Filtering {len(candidates)} candidates..."):
                t0 = time.time()
                stage1_results = deps["rank_candidates"](
                    job_description=structured_jd,
                    candidates=candidates,
                    job_embedding=None,  # Skip semantic in stage 1
                    top_n=min(500, len(candidates)),
                )
                stage1_time = time.time() - t0

            # Get stage 1 candidates
            cand_map = {c.get("candidate_id", ""): c for c in candidates}
            stage1_cands = [cand_map[r["candidate_id"]] for r in stage1_results if r["candidate_id"] in cand_map]

            # Stage 2: Semantic re-rank
            with st.spinner(f"Stage 2: Re-ranking top {len(stage1_cands)} candidates with embeddings..."):
                t1 = time.time()

                # Generate embeddings for candidates missing them
                try:
                    from candidate_processing.embedding_generator import generate_embeddings as gen_embs
                    missing_emb = [c for c in stage1_cands if not c.get("candidate_embedding")]
                    if missing_emb:
                        texts = []
                        for c in missing_emb:
                            ps = c.get("profile_summary", "")
                            sk = ", ".join(c.get("skills", {}).keys()) if isinstance(c.get("skills"), dict) else ""
                            dm = ", ".join(c.get("domains", {}).keys()) if isinstance(c.get("domains"), dict) else ""
                            texts.append(f"{ps} {sk} {dm}"[:2000])
                        embs = gen_embs(texts)
                        for c, emb in zip(missing_emb, embs):
                            c["candidate_embedding"] = emb.tolist() if hasattr(emb, "tolist") else list(emb)
                except ImportError:
                    pass  # Embeddings may not be available in all environments

                ranked = deps["rank_candidates"](
                    job_description=structured_jd,
                    candidates=stage1_cands,
                    job_embedding=job_embedding,
                    top_n=top_n,
                )
                stage2_time = time.time() - t1

            total_time = time.time() - t0

            # Display results
            st.success(
                f"Ranked {len(ranked)} candidates in {total_time:.1f}s "
                f"(Stage 1: {stage1_time:.1f}s, Stage 2: {stage2_time:.1f}s)"
            )

            # Results table
            st.subheader(f"Top {min(top_n, len(ranked))} Candidates")

            rows = []
            for i, cand in enumerate(ranked):
                orig = cand_map.get(cand.get("candidate_id", ""), {})
                ps = orig.get("profile_summary", "")[:100]
                seniority = orig.get("seniority", "N/A")
                yoe = orig.get("total_experience_years", 0)
                skills = orig.get("skills", {})
                ai_skills = sum(1 for s, sc in skills.items() if sc > 0.6) if isinstance(skills, dict) else 0
                rr = orig.get("redrob_signals", {}).get("recruiter_response_rate", 0)

                rows.append({
                    "Rank": i + 1,
                    "ID": cand.get("candidate_id", ""),
                    "Seniority": seniority,
                    "YOE": f"{yoe:.1f}",
                    "AI Skills": ai_skills,
                    "Score": f"{cand.get('final_score', 0):.1f}",
                    "Response Rate": f"{rr:.0%}",
                    "Profile": ps,
                })

            st.dataframe(rows, use_container_width=True, hide_index=True)

            # Score breakdown for top candidate
            if ranked:
                st.subheader("Score Breakdown — Top Candidate")
                top = ranked[0]
                chart_data = {
                    "Skill": top.get("skill_score", 0),
                    "Semantic": top.get("semantic_score", 0),
                    "Experience": top.get("experience_score", 0),
                    "Platform": top.get("platform_score", 0),
                    "Achievement": top.get("achievement_score", 0),
                    "Education": top.get("education_score", 0),
                }
                st.bar_chart(chart_data)

                # Explanation
                st.subheader("AI Explanation")
                st.info(top.get("explanation", "No explanation available."))

                # Strengths & Weaknesses
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Strengths:**")
                    for s in top.get("strengths", []):
                        st.markdown(f"- {s}")
                with col2:
                    st.markdown("**Weaknesses:**")
                    for w in top.get("weaknesses", []):
                        st.markdown(f"- {w}")

    with tab_about:
        st.markdown("""
        ## About This System

        **AI Recruiter** is an intelligent candidate ranking system built for the Redrob Hackathon.

        ### How It Works

        1. **Candidate Processing**: Parses 100K profiles, extracts skills (60+ aliases), analyzes career trajectories, infers leadership/impact scores, and normalizes Redrob platform signals.

        2. **Two-Stage Ranking**: Fast metadata filter (skills, experience, seniority) reduces 100K to 500. Semantic re-ranking (sentence-transformer embeddings) refines to top 100.

        3. **Multi-Factor Scoring**: 6 weighted dimensions — Skill Match (30%), Semantic Similarity (22%), Experience (18%), Platform Activity (12%), Achievements (10%), Education (8%).

        4. **Trap Detection**: Automatically penalizes non-tech titles (-80pts), consulting-only backgrounds (-50pts), and honeypots with impossible career timelines (-100pts).

        5. **Explainable AI**: Template-based NLG generates strengths, weaknesses, summary, and hiring recommendation for each candidate.

        ### Tech Stack
        - **Backend**: Python, sentence-transformers, numpy, FastAPI
        - **Frontend**: React, TypeScript, Tailwind CSS
        - **Deployment**: Docker Compose

        ### Compute Constraints
        - Runs within 5 minutes on CPU (no GPU)
        - Uses < 16GB RAM
        - No external API calls during ranking
        """)


if __name__ == "__main__":
    main()
