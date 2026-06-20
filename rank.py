#!/usr/bin/env python3
"""
rank.py - Generate submission CSV for the Redrob AI Challenge.

Loads processed candidates, ranks them against the job description,
and outputs a submission.csv with exactly 100 rows.

Usage:
    python rank.py
    python rank.py --candidates backend/processed_candidates.jsonl --out submission.csv --top-n 100
"""

import argparse
import csv
import json
import logging
import sys
import time
from pathlib import Path

# Ensure backend is importable
_backend_dir = str(Path(__file__).resolve().parent / "backend")
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def load_candidates(path: str, limit: int = None) -> list:
    """Load processed candidates from JSONL file."""
    candidates = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if not line.strip():
                continue
            cand = json.loads(line)
            # Normalize key: some files use 'id', some use 'candidate_id'
            if "candidate_id" not in cand and "id" in cand:
                cand["candidate_id"] = cand["id"]
            candidates.append(cand)
            if limit and i + 1 >= limit:
                break
    logger.info("Loaded %d candidates from %s", len(candidates), path)
    return candidates


def load_raw_candidates(path: str, ids: set) -> dict:
    """Load raw candidates to get redrob_signals for given IDs."""
    raw = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            cand = json.loads(line)
            cid = cand.get("candidate_id", "")
            if cid in ids:
                raw[cid] = cand
    logger.info("Loaded redrob_signals for %d candidates from raw data", len(raw))
    return raw


def detect_honeypot(cand: dict) -> bool:
    """Detect if a candidate is a honeypot profile (impossible dates, skill/duration discrepancies)."""
    # 1. Expert proficiency in multiple skills with 0 duration
    skills = cand.get("skills", [])
    expert_0_dur = 0
    for s in skills:
        if isinstance(s, dict):
            if s.get("proficiency") == "expert" and s.get("duration_months", 0) == 0:
                expert_0_dur += 1
    if expert_0_dur >= 3:
        return True

    # 2. Career history honeypots:
    # - total experience years vs company history
    yoe = cand.get("profile", {}).get("years_of_experience", 0)
    history = cand.get("career_history", [])
    
    # - Single role duration > total experience
    for job in history:
        if isinstance(job, dict):
            dur_yrs = job.get("duration_months", 0) / 12.0
            if dur_yrs > yoe + 0.5:
                return True
                
    # - Sum of durations in history is much greater than yoe
    total_history_months = sum(job.get("duration_months", 0) for job in history if isinstance(job, dict))
    if (total_history_months / 12.0) > yoe + 1.5:
        return True

    return False


def merge_redrob_signals(processed: list, raw: dict) -> list:
    """Merge redrob_signals from raw data into processed candidates."""
    for cand in processed:
        cid = cand.get("candidate_id", "")
        if cid in raw:
            cand["redrob_signals"] = raw[cid].get("redrob_signals", {})
            cand["is_honeypot"] = detect_honeypot(raw[cid])
            # Merge original raw profile fields
            profile = raw[cid].get("profile", {})
            cand["current_title"] = profile.get("current_title", "")
            cand["headline"] = profile.get("headline", "")
    return processed


def load_job_description(path: str) -> str:
    """Load job description from docx or txt file."""
    p = Path(path)
    if p.suffix == ".docx":
        try:
            from docx import Document
            doc = Document(str(p))
            return "\n".join(paragraph.text for paragraph in doc.paragraphs)
        except ImportError:
            logger.warning("python-docx not installed, trying to read as text")
            return p.read_text(encoding="utf-8")
    else:
        return p.read_text(encoding="utf-8")


def generate_reasoning(candidate: dict, response_rate: float = 0.0) -> str:
    """
    Generate a reasoning string for a candidate in the submission format.

    Format: "Title with X yrs; Y AI core skills; response rate 0.XX"
    """
    # Extract title from profile_summary (first part before "with")
    summary = candidate.get("profile_summary", "")
    title = summary.split(" with ")[0].split(" at ")[0].strip() if summary else "Unknown"
    if not title or title == "Unknown":
        # Fallback: try seniority + domain
        seniority = candidate.get("seniority", "")
        domains = candidate.get("domains", [])
        domain = domains[0] if domains else "Professional"
        title = f"{seniority} {domain}".strip() if seniority else domain

    # Experience years
    years = candidate.get("total_experience_years", 0)
    years_str = f"{years:.1f}" if years else "N/A"

    # Count AI core skills (skills with score > 0.6)
    skills = candidate.get("skills", {})
    if isinstance(skills, dict):
        ai_core = sum(1 for s, sc in skills.items() if sc > 0.6)
    elif isinstance(skills, list):
        ai_core = len(skills)
    else:
        ai_core = 0

    # Response rate from redrob_signals
    redrob = candidate.get("redrob_signals", {})
    rr = redrob.get("recruiter_response_rate", response_rate)

    return f"{title} with {years_str} yrs; {ai_core} AI core skills; response rate {rr:.2f}."


def normalize_score(score: float, all_scores: list) -> float:
    """Normalize a 0-100 score to 0-1 range."""
    if not all_scores:
        return 0.0
    min_s = min(all_scores)
    max_s = max(all_scores)
    if max_s == min_s:
        return 0.5
    return round((score - min_s) / (max_s - min_s), 4)


def generate_submission(
    candidates_path: str,
    raw_candidates_path: str,
    job_description_path: str,
    output_path: str,
    top_n: int = 100,
    limit: int = None,
):
    """Generate the submission CSV."""
    t0 = time.time()

    # 1. Load candidates
    candidates = load_candidates(candidates_path, limit=limit)

    # 2. Load raw candidates for redrob_signals
    candidate_ids = {c.get("candidate_id", "") for c in candidates}
    raw = load_raw_candidates(raw_candidates_path, candidate_ids)

    # 3. Merge redrob_signals
    candidates = merge_redrob_signals(candidates, raw)

    # 4. Load job description
    jd_text = load_job_description(job_description_path)
    logger.info("Loaded job description: %d chars", len(jd_text))

    # 5. Parse JD
    from part2.job_parser import JobParser
    parser = JobParser()
    parsed_jd = parser.parse(jd_text)
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

    # 6. Generate job embedding
    from app.services.embedding_service import generate_embedding
    job_embedding = generate_embedding(jd_text)

    # Stage 1: Fast Filter (no semantic embedding search)
    # Rank all candidates using metadata/structured signals first to select a top pool of 500 candidates
    from part3.services.ranking_service import rank_candidates
    
    logger.info("Stage 1: Ranking all %d candidates using metadata/structured signals...", len(candidates))
    # Passing job_embedding=None makes the ranking engine skip/use neutral semantic scores
    stage1_pool = rank_candidates(
        job_description=structured_jd,
        candidates=candidates,
        job_embedding=None,
        top_n=500,  # Retrieve top 500 candidates
    )
    
    # Map the top 500 back to full candidate dictionaries
    cand_map = {c.get("candidate_id", ""): c for c in candidates}
    stage1_candidates = [cand_map[r["candidate_id"]] for r in stage1_pool if r["candidate_id"] in cand_map]
    
    # Stage 2: Refinement (semantic re-ranking)
    # Generate embeddings on-the-fly ONLY for the top 500 candidates if they are missing
    from candidate_processing.embedding_generator import build_candidate_text, generate_embeddings
    candidates_needing_emb = [c for c in stage1_candidates if not c.get("candidate_embedding")]
    if candidates_needing_emb:
        logger.info("Stage 2: Generating embeddings for %d top-tier candidates...", len(candidates_needing_emb))
        texts = []
        for c in candidates_needing_emb:
            profile_summary = c.get("profile_summary", "")
            skills_str = ", ".join(c.get("skills", {}).keys()) if isinstance(c.get("skills"), dict) else ""
            domains_str = ", ".join(c.get("domains", {}).keys()) if isinstance(c.get("domains"), dict) else ""
            texts.append(f"{profile_summary} {skills_str} {domains_str}"[:2000])
        embeddings = generate_embeddings(texts)
        for c, emb in zip(candidates_needing_emb, embeddings):
            c["candidate_embedding"] = emb.tolist() if hasattr(emb, "tolist") else list(emb)
            
    logger.info("Stage 2: Re-ranking top candidates with semantic similarity...")
    ranked = rank_candidates(
        job_description=structured_jd,
        candidates=stage1_candidates,
        job_embedding=job_embedding,
        top_n=top_n,
    )

    logger.info("Ranked %d candidates in %.1fs", len(ranked), time.time() - t0)

    # 8. Normalize scores to 0-1 and handle ties
    raw_scores = [r["final_score"] for r in ranked]

    # Build candidate lookup map
    cand_map = {c.get("candidate_id", ""): c for c in candidates}

    # Build submission rows
    rows = []
    for cand in ranked:
        norm_score = normalize_score(cand["final_score"], raw_scores)
        orig_cand = cand_map.get(cand["candidate_id"], {})
        reasoning = generate_reasoning(orig_cand)
        rows.append({
            "candidate_id": cand["candidate_id"],
            "rank": 0,  # assigned after sorting
            "score": norm_score,
            "reasoning": reasoning,
        })

    # Sort rows by score descending, then candidate_id ascending
    rows.sort(key=lambda x: (-x["score"], x["candidate_id"]))

    # Assign ranks based on sorted order
    for i, row in enumerate(rows):
        row["rank"] = i + 1

    # 9. Ensure exactly top_n rows
    if len(rows) > top_n:
        rows = rows[:top_n]
    elif len(rows) < top_n:
        logger.warning("Only %d candidates ranked, need %d", len(rows), top_n)

    # 10. Validate ranks are 1-100 with no duplicates
    seen_ranks = set()
    for row in rows:
        assert row["rank"] not in seen_ranks, f"Duplicate rank {row['rank']}"
        seen_ranks.add(row["rank"])
    assert len(seen_ranks) == top_n, f"Expected {top_n} unique ranks, got {len(seen_ranks)}"

    # 11. Write CSV
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["candidate_id", "rank", "score", "reasoning"])
        writer.writeheader()
        writer.writerows(rows)

    elapsed = time.time() - t0
    logger.info("Submission written to %s (%d rows, %.1fs)", output_path, len(rows), elapsed)
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Generate submission CSV for Redrob AI Challenge")
    parser.add_argument(
        "--candidates",
        default="backend/processed_candidates.jsonl",
        help="Path to processed_candidates.jsonl (default: backend/processed_candidates.jsonl)",
    )
    parser.add_argument(
        "--raw-candidates",
        default="[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl",
        help="Path to raw candidates.jsonl for redrob_signals",
    )
    parser.add_argument(
        "--job-description",
        default="[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/job_description.docx",
        help="Path to job description file",
    )
    parser.add_argument(
        "--out",
        default="submission.csv",
        help="Output CSV path (default: submission.csv)",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=100,
        help="Number of top candidates (default: 100)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of candidates to process (for testing)",
    )
    args = parser.parse_args()

    generate_submission(
        candidates_path=args.candidates,
        raw_candidates_path=args.raw_candidates,
        job_description_path=args.job_description,
        output_path=args.out,
        top_n=args.top_n,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()
