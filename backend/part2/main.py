"""
Part 2: AI Candidate Ranking Engine

Entry point. Takes a job description, retrieves and ranks candidates,
and outputs explainable results.

Usage::

    python -m backend.part2.main --jd "Looking for Senior Python Developer..."
    python -m backend.part2.main --jd-file job_description.txt
    python -m backend.part2.main --interactive
"""

import sys
import json
import time
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.part2.job_parser import JobParser
from backend.part2.embedding import generate_job_embedding
from backend.part2.faiss_search import load_index, retrieve_candidates, get_all_candidates
from backend.part2.ranking_engine import rank_candidates
from backend.part2.explainer import generate_explanation, format_ranking_output

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Example job descriptions
# ---------------------------------------------------------------------------
EXAMPLE_JDS = {
    "senior_backend": """
Looking for Senior Backend Engineer.

Must Have:
Python
FastAPI
Docker
Microservices
SQL

Preferred:
Kafka
AWS
Redis

Experience:
5+ years

Domain:
FinTech
""",

    "ml_engineer": """
AI/ML Engineer - Machine Learning Systems

Must Have:
Python
PyTorch
TensorFlow
Machine Learning
Deep Learning

Preferred:
Kubernetes
MLOps
NLP
Transformers

Experience:
3+ years

Domain:
AI/ML
""",

    "data_engineer": """
Senior Data Engineer

Must Have:
Python
SQL
Spark
Airflow
Data Pipelines

Preferred:
AWS
Snowflake
dbt

Experience:
4+ years

Domain:
Data Engineering
Cloud
""",
}


def run_ranking(
    jd_text: str,
    top_k: int = 100,
    top_n: int = 20,
) -> list:
    """
    End-to-end ranking pipeline.

    Parameters
    ----------
    jd_text : str
        Raw job description text.
    top_k : int
        Number of candidates to retrieve from FAISS.
    top_n : int
        Number of candidates to return after ranking.

    Returns
    -------
    list[dict]
        Ranked candidates with explanations.
    """
    t0 = time.time()

    # 1. Parse job description
    logger.info("Parsing job description...")
    parser = JobParser()
    job_parsed = parser.parse(jd_text)
    logger.info(
        "  Required skills: %s | Experience: %d yrs | Seniority: %s | Domains: %s",
        job_parsed["required_skills"],
        job_parsed["experience"],
        job_parsed["seniority"],
        job_parsed["domains"],
    )

    # 2. Generate job embedding
    logger.info("Generating job embedding...")
    job_emb = generate_job_embedding(jd_text)
    logger.info("  Embedding shape: %s", job_emb.shape)

    # 3. Load FAISS index
    logger.info("Loading FAISS index...")
    load_index()

    # 4. Retrieve candidates
    logger.info("Retrieving top %d candidates...", top_k)
    retrieved = retrieve_candidates(job_emb, top_k=top_k)
    logger.info("  Retrieved %d candidates", len(retrieved))

    # 5. Get all candidates data
    all_cands = get_all_candidates()

    # 6. Rank
    logger.info("Ranking candidates...")
    ranked = rank_candidates(
        job_parsed=job_parsed,
        job_embedding=job_emb,
        retrieved_candidates=retrieved,
        all_candidates=all_cands,
        top_n=top_n,
    )

    elapsed = time.time() - t0
    logger.info("  Ranked %d candidates in %.2fs", len(ranked), elapsed)

    return ranked


def main() -> None:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="AI Candidate Ranking Engine (Part 2)")
    parser.add_argument("--jd", type=str, default=None, help="Job description text")
    parser.add_argument("--jd-file", type=str, default=None, help="Path to job description file")
    parser.add_argument("--example", type=str, default=None, choices=list(EXAMPLE_JDS.keys()),
                        help="Use an example JD")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode")
    parser.add_argument("--top-k", type=int, default=100, help="FAISS retrieval count")
    parser.add_argument("--top-n", type=int, default=20, help="Final ranking count")
    parser.add_argument("--output", type=str, default=None, help="Save results to JSON file")
    args = parser.parse_args()

    # Determine JD text
    jd_text = None
    if args.jd:
        jd_text = args.jd
    elif args.jd_file:
        jd_text = Path(args.jd_file).read_text(encoding="utf-8")
    elif args.example:
        jd_text = EXAMPLE_JDS[args.example]
    elif args.interactive:
        print("Enter job description (end with empty line):")
        lines = []
        while True:
            line = input()
            if not line:
                break
            lines.append(line)
        jd_text = "\n".join(lines)
    else:
        # Default: use first example
        jd_text = EXAMPLE_JDS["senior_backend"]
        print(f"[INFO] No JD provided. Using example: senior_backend\n")

    # Run ranking
    ranked = run_ranking(jd_text, top_k=args.top_k, top_n=args.top_n)

    # Print results
    output = format_ranking_output(ranked)
    print(output)

    # Save if requested
    if args.output:
        save_data = []
        for rc in ranked:
            explanation = generate_explanation(rc)
            save_data.append({
                "rank": explanation["rank"],
                "candidate_id": explanation["candidate_id"],
                "score": explanation["score"],
                "reasons": explanation["reasons"],
                "breakdown": {
                    "semantic_similarity": rc["semantic_similarity"],
                    "skill_score": rc["skill_score"],
                    "experience_score": rc["experience_score"],
                    "domain_score": rc["domain_score"],
                    "achievement_score": rc["achievement_score"],
                    "education_score": rc["education_score"],
                    "growth_score": rc["growth_score"],
                },
            })
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)
        print(f"\n[INFO] Saved results to {args.output}")


if __name__ == "__main__":
    main()
