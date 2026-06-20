"""
AI Recruiter — HuggingFace Spaces Demo

Self-contained Streamlit app demonstrating the candidate ranking system
on a small sample of candidates. No external backend dependencies.
"""

import json
import re
import math
import time
from typing import Dict, List, Any, Tuple, Set

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
SAMPLE_SIZE = 100

SKILL_ALIASES = {
    "py": "python", "python3": "python", "js": "javascript", "ts": "typescript",
    "tf": "tensorflow", "k8s": "kubernetes", "sklearn": "scikit-learn",
    "golang": "go", "nodejs": "node.js", "node": "node.js",
    "react.js": "react", "vue.js": "vue", "nextjs": "next.js",
    "llms": "llm", "large language models": "llm",
    "retrieval augmented generation": "rag",
    "amazon web services": "aws", "google cloud": "gcp",
    "c plus plus": "c++", "c sharp": "c#",
}

SKILL_SYNONYM_GROUPS = [
    {"fastapi", "flask", "django", "starlette"},
    {"react", "angular", "vue", "vue.js", "svelte"},
    {"python", "ruby", "perl"},
    {"java", "kotlin", "scala"},
    {"javascript", "typescript"},
    {"aws", "gcp", "azure"},
    {"postgresql", "mysql", "mariadb", "sqlite"},
    {"mongodb", "couchdb", "dynamodb"},
    {"redis", "memcached", "elasticsearch"},
    {"spark", "flink", "beam"},
    {"kafka", "rabbitmq", "nats"},
    {"airflow", "luigi", "prefect", "dagster"},
    {"tensorflow", "pytorch", "keras", "jax"},
    {"scikit-learn", "xgboost", "lightgbm", "catboost"},
    {"docker", "podman", "containerd"},
    {"kubernetes", "docker swarm", "nomad"},
    {"terraform", "pulumi", "cloudformation"},
]

_GROUP_INDEX: Dict[str, int] = {}
for _i, _group in enumerate(SKILL_SYNONYM_GROUPS):
    for _skill in _group:
        _GROUP_INDEX[_skill] = _i

REQUIRED_WEIGHT = 0.70
PREFERRED_WEIGHT = 0.30

WEIGHTS = {"skill": 0.30, "semantic": 0.22, "experience": 0.18,
           "platform": 0.12, "achievement": 0.10, "education": 0.08}

CONSULTING_FIRMS = {"tcs", "infosys", "wipro", "accenture", "cognizant",
                     "capgemini", "tech mahindra", "hcl", "lti", "mindtree"}

NON_TECH_KEYWORDS = {"marketing", "sales", "operations", "hr", "accountant",
                      "civil engineer", "mechanical engineer", "graphic designer",
                      "technical support", "writer", "recruiter", "talent acquisition"}

EDUCATION_SCORES = {"phd": 100, "doctorate": 100, "m.s.": 90, "ms": 90,
                    "m.sc": 90, "mba": 90, "masters": 90, "master": 90,
                    "b.e.": 80, "be": 80, "b.tech": 80, "bachelors": 80,
                    "associate": 70, "diploma": 60}

SENIORITY_LEVELS = {"intern": 1, "junior": 2, "mid": 3, "senior": 4,
                     "lead": 5, "staff": 6, "principal": 7}

TITLE_LEVEL_MAP = {
    "intern": "Intern", "trainee": "Intern",
    "junior": "Junior", "jr": "Junior", "associate": "Junior",
    "mid": "Mid", "mid-level": "Mid", "intermediate": "Mid",
    "senior": "Senior", "sr": "Senior", "sr.": "Senior",
    "lead": "Lead", "tech lead": "Lead", "team lead": "Lead",
    "staff": "Staff", "principal": "Principal", "distinguished": "Principal",
    "director": "Principal", "vp": "Principal",
}

_YOE_PATTERNS = [
    re.compile(r"(\d{1,2})\+?\s*[-\u2013]\s*(\d{1,2})\s*(?:years?|yrs?)", re.I),
    re.compile(r"(\d{1,2})\+?\s*(?:years?|yrs?)", re.I),
    re.compile(r"min(?:imum)?[\s:]*(\d{1,2})", re.I),
]


# ---------------------------------------------------------------------------
# Skill matching helpers
# ---------------------------------------------------------------------------
def normalise_skill(name: str) -> str:
    name = name.strip().lower()
    name = re.sub(r"[\s_]+", " ", name)
    return SKILL_ALIASES.get(name, name)


def are_skills_related(a: str, b: str) -> bool:
    if a == b:
        return True
    ga = _GROUP_INDEX.get(a)
    gb = _GROUP_INDEX.get(b)
    return ga is not None and gb is not None and ga == gb


def find_best_match(target: str, skills: List[str]) -> Tuple[str, float]:
    best, strength = "", 0.0
    for sk in skills:
        cs, rs = normalise_skill(sk), normalise_skill(target)
        if cs == rs:
            return sk, 1.0
        if are_skills_related(cs, rs) and 0.5 > strength:
            best, strength = sk, 0.5
    return best, strength


# ---------------------------------------------------------------------------
# JD Parser (simplified, self-contained)
# ---------------------------------------------------------------------------
KNOWN_SKILLS = {
    "python", "java", "javascript", "typescript", "react", "angular", "vue",
    "node.js", "django", "flask", "fastapi", "spring",
    "go", "rust", "c++", "c#", "swift", "kotlin",
    "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "aws", "gcp", "azure", "docker", "kubernetes", "terraform",
    "kafka", "rabbitmq", "airflow", "spark",
    "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
    "machine learning", "deep learning", "nlp", "computer vision",
    "hugging face", "langchain", "openai",
    "vector database", "pinecone", "weaviate", "milvus",
    "xgboost", "lightgbm",
    "sentence-transformers", "bge", "e5", "qdrant", "opensearch",
    "faiss", "ndcg", "mrr", "map",
    "lora", "qlora", "peft", "learning-to-rank",
    "llm fine-tuning", "distributed systems", "hr-tech",
    "embedding", "retrieval", "ranking", "information retrieval",
    "recommendation", "search", "fine-tuning",
}


def parse_jd(text: str) -> Dict[str, Any]:
    """Parse a job description into structured requirements."""
    lowered = text.lower()
    required = set()
    preferred = set()

    # Extract from "Things you absolutely need" section
    req_match = re.search(
        r"things you absolutely need\s*\n(.*?)(?=things (?:we|they)|$)",
        text, re.I | re.S,
    )
    if req_match:
        section = req_match.group(1).lower()
        for sk in KNOWN_SKILLS:
            if re.search(r"(?<!\w)" + re.escape(sk) + r"(?!\w)", section):
                required.add(sk)

    # Extract from "Things we'd like you to have" section
    pref_match = re.search(
        r"things we(?:'d| would) like you to have[^a-z]*(.*?)(?=things (?:we|they)|final note|$)",
        text, re.I | re.S,
    )
    if pref_match:
        section = pref_match.group(1).lower()
        for sk in KNOWN_SKILLS:
            if re.search(r"(?<!\w)" + re.escape(sk) + r"(?!\w)", section):
                preferred.add(sk)

    # Fallback: scan full text
    if not required:
        for sk in KNOWN_SKILLS:
            if re.search(r"(?<!\w)" + re.escape(sk) + r"(?!\w)", lowered):
                required.add(sk)

    # Experience
    experience = 0
    for pat in _YOE_PATTERNS:
        m = pat.search(text)
        if m:
            groups = m.groups()
            if len(groups) >= 2 and groups[1]:
                experience = min(int(groups[0]), int(groups[1]))
            else:
                experience = int(groups[0])
            break

    # Seniority
    seniority = "Mid"
    first_line = text.split("\n")[0].lower() if "\n" in text else text[:100].lower()
    for kw, level in sorted(TITLE_LEVEL_MAP.items(), key=lambda x: -len(x[0])):
        if re.search(r"(?<!\w)" + re.escape(kw) + r"(?!\w)", first_line):
            seniority = level
            break

    return {
        "required_skills": sorted(required),
        "preferred_skills": sorted(preferred),
        "experience": experience,
        "seniority": seniority,
    }


# ---------------------------------------------------------------------------
# Scoring functions
# ---------------------------------------------------------------------------
def skill_score(candidate_skills: Dict, required: List[str], preferred: List[str]) -> float:
    if not required and not preferred:
        return 50.0
    cand_names = list(candidate_skills.keys()) if isinstance(candidate_skills, dict) else list(candidate_skills)

    req_exact = req_related = 0
    for r in required:
        _, s = find_best_match(r, cand_names)
        if s >= 1.0:
            req_exact += 1
        elif s >= 0.5:
            req_related += 1
    req_score = (req_exact + 0.5 * req_related) / len(required) if required else 1.0

    pref_match = sum(1 for p in preferred if find_best_match(p, cand_names)[1] >= 0.5)
    pref_score = pref_match / len(preferred) if preferred else 0.0

    return round((REQUIRED_WEIGHT * req_score + PREFERRED_WEIGHT * pref_score) * 100, 2)


def experience_score(cand_years: float, req_years: int, cand_seniority: str, req_seniority: str) -> float:
    if req_years <= 0:
        base = 85.0 if cand_years >= 10 else 75.0 if cand_years >= 5 else 65.0 if cand_years >= 2 else 50.0
    else:
        ratio = cand_years / req_years
        if ratio >= 1.0:
            base = 85 + 15 * (1 - math.exp(-(ratio - 1) * 0.5))
        elif ratio >= 0.7:
            base = 60 + 25 * (ratio - 0.7) / 0.3
        elif ratio >= 0.4:
            base = 30 + 30 * (ratio - 0.4) / 0.3
        else:
            base = max(0, 30 * ratio / 0.4)

    bonus = 0.0
    if cand_seniority and req_seniority:
        c = SENIORITY_LEVELS.get(cand_seniority.lower(), 0)
        r = SENIORITY_LEVELS.get(req_seniority.lower(), 0)
        if c and r:
            diff = c - r
            if diff == 0:
                bonus = 5.0
            elif diff == 1:
                bonus = 3.0
            elif diff >= 2:
                bonus = 2.0
            elif diff == -1:
                bonus = 0.0
            else:
                bonus = -5.0

    return round(max(0, min(100, base + bonus)), 2)


def education_score(cand_edu: Dict) -> float:
    if not cand_edu:
        return 40.0
    level = str(cand_edu.get("degree_level", "")).lower()
    base = EDUCATION_SCORES.get(level, 50)
    tier = cand_edu.get("institution_tier", "tier_3")
    tier_bonus = {"tier_1": 10, "tier_2": 5, "tier_3": 0, "tier_4": 0}.get(tier, 0)
    return round(min(100, base + tier_bonus), 2)


def platform_score(redrob: Dict) -> float:
    if not redrob:
        return 40.0
    eng = redrob.get("engagement_score", 0)
    vis = redrob.get("visibility_score", 0)
    cred = redrob.get("credibility_score", 0)
    avail = redrob.get("availability_score", 0)
    return round(max(0, min(100, (eng + vis + cred + avail) * 25)), 2)


def achievement_score(cand: Dict) -> float:
    score = 0.0
    if cand.get("leadership_score", 0) > 0.5:
        score += 25
    if cand.get("impact_score", 0) > 0.5:
        score += 25
    history = cand.get("career_history", [])
    if len(history) >= 3:
        score += 25
    achievements = cand.get("achievements", [])
    if achievements:
        score += 25
    return round(min(100, score), 2)


def cosine_similarity(a: List[float], b: List[float]) -> float:
    a, b = np.array(a), np.array(b)
    dot = np.dot(a, b)
    norm = np.linalg.norm(a) * np.linalg.norm(b)
    return float(dot / norm) if norm > 0 else 0.0


# ---------------------------------------------------------------------------
# Ranking engine
# ---------------------------------------------------------------------------
def rank_candidates(jd_text: str, candidates: List[Dict], top_n: int = 20,
                    weights: Dict = None, job_embedding=None) -> List[Dict]:
    """Full ranking pipeline — self-contained."""
    if weights is None:
        weights = WEIGHTS

    parsed = parse_jd(jd_text)
    required = parsed["required_skills"]
    preferred = parsed["preferred_skills"]
    req_exp = parsed["experience"]
    req_seniority = parsed["seniority"]

    results = []
    for cand in candidates:
        cid = cand.get("candidate_id", "")
        skills = cand.get("skills", {})
        yoe = cand.get("total_experience_years", 0)
        cand_seniority = cand.get("seniority", "Mid")
        title = (cand.get("current_title") or "").lower()

        # Trap detection
        is_non_tech = any(kw in title for kw in NON_TECH_KEYWORDS)
        is_consulting = False
        career = cand.get("career_history", [])
        if career:
            firms = [c.get("company", "").lower() for c in career]
            if firms and all(any(cf in f for cf in CONSULTING_FIRMS) for f in firms):
                is_consulting = True

        # Compute scores
        s_skill = skill_score(skills, required, preferred)
        s_exp = experience_score(yoe, req_exp, cand_seniority, req_seniority)
        s_edu = education_score(cand.get("education", {}))
        s_plat = platform_score(cand.get("redrob_signals", {}))
        s_ach = achievement_score(cand)

        # Semantic similarity
        s_sem = 50.0  # neutral default
        cand_emb = cand.get("candidate_embedding")
        if job_embedding and cand_emb:
            s_sem = round(cosine_similarity(job_embedding, cand_emb) * 100, 2)

        # Weighted composite
        final = (
            s_skill * weights["skill"] +
            s_sem * weights["semantic"] +
            s_exp * weights["experience"] +
            s_plat * weights["platform"] +
            s_ach * weights["achievement"] +
            s_edu * weights["education"]
        )

        # Penalties
        if is_non_tech:
            final = -100.0
        if is_consulting:
            final -= 50.0
        if cand.get("is_honeypot"):
            final = -100.0

        final = round(max(0, min(100, final)), 2)

        # Build reasoning
        ai_keywords = {"machine learning", "deep learning", "nlp", "transformer",
                       "bert", "gpt", "llm", "tensorflow", "pytorch", "embedding",
                       "rag", "retrieval", "vector database", "hugging face", "fine-tuning"}
        if isinstance(skills, dict):
            ai_count = sum(1 for s in skills if any(k in s.lower() for k in ai_keywords))
        else:
            ai_count = 0

        matched_req = []
        for r in required:
            for sk in (skills.keys() if isinstance(skills, dict) else skills):
                if r.lower() in sk.lower() or sk.lower() in r.lower():
                    matched_req.append(r)
                    break

        parts = []
        if req_exp > 0 and yoe >= req_exp:
            parts.append(f"Meets {req_exp}+ year requirement ({yoe:.1f} YoE)")
        elif req_exp > 0:
            parts.append(f"Below {req_exp} year target ({yoe:.1f} YoE)")

        if ai_count >= 5:
            parts.append(f"Strong AI depth ({ai_count} skills)")
        elif ai_count > 0:
            parts.append(f"Some AI exposure ({ai_count} skills)")
        else:
            parts.append("No AI skills listed")

        if matched_req:
            parts.append(f"Covers: {', '.join(matched_req[:3])}")

        rr = cand.get("redrob_signals", {}).get("recruiter_response_rate", 0)
        if rr >= 0.7:
            parts.append("Highly responsive")
        if cand.get("redrob_signals", {}).get("open_to_work"):
            parts.append("Open to work")

        results.append({
            "candidate_id": cid,
            "final_score": final,
            "skill_score": s_skill,
            "semantic_score": s_sem,
            "experience_score": s_exp,
            "education_score": s_edu,
            "achievement_score": s_ach,
            "platform_score": s_plat,
            "strengths": matched_req[:5],
            "weaknesses": [f"Missing: {r}" for r in required if r not in matched_req][:3],
            "explanation": "; ".join(parts) + "." if parts else "No strong signals.",
            "seniority": cand_seniority,
        })

    # Sort with tiebreakers
    results.sort(key=lambda x: (x["final_score"], x["semantic_score"],
                                 x["skill_score"], x["experience_score"]), reverse=True)

    # Assign ranks
    for i, r in enumerate(results, 1):
        r["rank"] = i

    return results[:top_n]


# ---------------------------------------------------------------------------
# Candidate loading
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Loading candidates...")
def load_candidates(n: int) -> List[Dict]:
    candidates = []
    paths = [
        "processed_candidates_sample.jsonl",
        "processed_candidates.jsonl",
    ]
    data_path = None
    for p in paths:
        from pathlib import Path
        if Path(p).exists():
            data_path = p
            break
    if not data_path:
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
# Default JD
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
    st.markdown("Multi-factor AI-powered candidate ranking system.")

    with st.sidebar:
        st.header("Configuration")
        sample_size = st.slider("Candidate pool size", 50, 500, SAMPLE_SIZE, 50)
        top_n = st.slider("Top N to rank", 5, 100, 20, 5)

        st.divider()
        st.markdown("**Scoring Weights**")
        weights = {
            "skill": st.slider("Skill", 0.0, 0.5, 0.30, 0.05),
            "semantic": st.slider("Semantic", 0.0, 0.5, 0.22, 0.05),
            "experience": st.slider("Experience", 0.0, 0.5, 0.18, 0.05),
            "platform": st.slider("Platform", 0.0, 0.5, 0.12, 0.05),
            "achievement": st.slider("Achievement", 0.0, 0.5, 0.10, 0.05),
            "education": st.slider("Education", 0.0, 0.5, 0.08, 0.05),
        }
        total = sum(weights.values())
        if abs(total - 1.0) > 0.01:
            st.warning(f"Weights sum to {total:.2f} (should be 1.0)")
        else:
            st.success(f"Weights sum to {total:.2f}")

    tab_rank, tab_about = st.tabs(["Rank Candidates", "About"])

    with tab_rank:
        jd_text = st.text_area(
            "Job Description",
            value=DEFAULT_JD,
            height=250,
            help="Paste a job description. The system parses required skills, experience, and seniority.",
        )

        if st.button("Rank Candidates", type="primary", use_container_width=True):
            if not jd_text.strip():
                st.error("Please enter a job description.")
                return

            with st.spinner(f"Loading {sample_size} candidates..."):
                candidates = load_candidates(sample_size)

            if not candidates:
                st.error("No candidates found. Ensure processed_candidates_sample.jsonl is present.")
                return

            with st.spinner("Parsing job description..."):
                parsed_jd = parse_jd(jd_text)

            with st.expander("Parsed Job Description", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Required:** {', '.join(parsed_jd['required_skills'])}")
                    st.markdown(f"**Preferred:** {', '.join(parsed_jd['preferred_skills'])}")
                with col2:
                    st.markdown(f"**Experience:** {parsed_jd['experience']} years")
                    st.markdown(f"**Seniority:** {parsed_jd['seniority']}")

            with st.spinner("Ranking candidates..."):
                t0 = time.time()
                ranked = rank_candidates(
                    jd_text=jd_text,
                    candidates=candidates,
                    top_n=top_n,
                    weights=weights,
                )
                elapsed = time.time() - t0

            st.success(f"Ranked {len(ranked)} candidates in {elapsed:.1f}s")

            st.subheader(f"Top {len(ranked)} Candidates")
            rows = []
            for r in ranked:
                rows.append({
                    "Rank": r["rank"],
                    "ID": r["candidate_id"],
                    "Seniority": r["seniority"],
                    "Score": f"{r['final_score']:.1f}",
                    "Reasoning": r["explanation"][:120],
                })
            st.dataframe(rows, use_container_width=True, hide_index=True)

            if ranked:
                st.subheader("Score Breakdown — Top Candidate")
                top = ranked[0]
                st.bar_chart({
                    "Skill": top["skill_score"],
                    "Semantic": top["semantic_score"],
                    "Experience": top["experience_score"],
                    "Platform": top["platform_score"],
                    "Achievement": top["achievement_score"],
                    "Education": top["education_score"],
                })
                st.info(top["explanation"])

    with tab_about:
        st.markdown("""
        ## About

        **AI Recruiter** is a multi-factor candidate ranking system.

        ### How It Works
        1. **JD Parsing** — Extracts required skills, experience, seniority from free-text JDs
        2. **Trap Detection** — Penalizes non-tech titles, consulting-only backgrounds, honeypots
        3. **Multi-Factor Scoring** — 6 weighted dimensions: Skill (30%), Semantic (22%), Experience (18%), Platform (12%), Achievement (10%), Education (8%)
        4. **Explainable Output** — Each candidate gets a unique, data-driven reasoning

        ### Compute Constraints
        - CPU only, no GPU
        - Under 5 minutes for 100K candidates
        - No external API calls during ranking
        """)


if __name__ == "__main__":
    main()
