"""
Quick verification script for the processed candidates.
Run: python -m backend.test_output
"""

import json
import sys
from collections import Counter


def main():
    filepath = "C:/AI_Recruiter/backend/processed_candidates.jsonl"

    results = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                results.append(json.loads(line))

    print(f"\n{'='*60}")
    print(f"  VERIFICATION REPORT")
    print(f"{'='*60}")
    print(f"  Total candidates processed: {len(results)}")

    # --- Required fields check ---
    required_fields = [
        "candidate_id", "profile_summary", "skills", "domains",
        "leadership_score", "impact_score", "career_growth_score",
        "promotion_count", "education_score", "seniority",
        "total_experience_years", "years_in_current_role",
        "candidate_embedding",
    ]
    missing = Counter()
    for r in results:
        for field in required_fields:
            if field not in r:
                missing[field] += 1

    print(f"\n--- Field Completeness ---")
    if missing:
        for field, count in missing.most_common():
            print(f"  MISSING '{field}': {count}/{len(results)}")
    else:
        print(f"  All {len(required_fields)} required fields present in ALL candidates.")

    # --- Seniority distribution ---
    seniority = Counter(r.get("seniority", "?") for r in results)
    print(f"\n--- Seniority Distribution ---")
    for level in ["Junior", "Mid", "Senior", "Lead", "Principal"]:
        count = seniority.get(level, 0)
        pct = count / len(results) * 100
        bar = "#" * int(pct / 2)
        print(f"  {level:<12} {count:>6} ({pct:5.1f}%) {bar}")

    # --- Experience stats ---
    years = [r.get("total_experience_years", 0) for r in results]
    print(f"\n--- Experience Stats ---")
    print(f"  Min:    {min(years):.1f} years")
    print(f"  Max:    {max(years):.1f} years")
    print(f"  Avg:    {sum(years)/len(years):.1f} years")
    years_sorted = sorted(years)
    print(f"  Median: {years_sorted[len(years_sorted)//2]:.1f} years")

    # --- Skills stats ---
    skill_counts = [len(r.get("skills", {})) for r in results]
    print(f"\n--- Skills per Candidate ---")
    print(f"  Avg: {sum(skill_counts)/len(skill_counts):.1f} skills")
    print(f"  Max: {max(skill_counts)} skills")

    # --- Domains stats ---
    domain_counts = [len(r.get("domains", {})) for r in results]
    print(f"\n--- Domains per Candidate ---")
    print(f"  Avg: {sum(domain_counts)/len(domain_counts):.1f} domains")

    # --- Embedding stats ---
    emb_lengths = [len(r.get("candidate_embedding", [])) for r in results]
    has_emb = sum(1 for e in emb_lengths if e > 0)
    print(f"\n--- Embeddings ---")
    print(f"  Candidates with embeddings: {has_emb}/{len(results)}")
    if has_emb > 0:
        emb_lens = [e for e in emb_lengths if e > 0]
        print(f"  Embedding dimension: {emb_lens[0]}")

    # --- Score distributions ---
    print(f"\n--- Score Distributions ---")
    for score_field in ["leadership_score", "impact_score", "career_growth_score", "education_score"]:
        vals = [r.get(score_field, 0) for r in results]
        nonzero = sum(1 for v in vals if v > 0)
        avg = sum(vals) / len(vals)
        print(f"  {score_field:<25} avg={avg:.3f}  nonzero={nonzero}/{len(results)}")

    # --- Sample outputs ---
    print(f"\n--- Sample Candidates (first 3) ---")
    for r in results[:3]:
        print(f"\n  ID: {r.get('candidate_id', r.get('id', 'UNKNOWN'))}")
        print(f"  Summary: {r['profile_summary'][:120]}...")
        print(f"  Seniority: {r['seniority']} | Years: {r['total_experience_years']}")
        print(f"  Top Skills: {list(r['skills'].keys())[:5]}")
        print(f"  Top Domains: {list(r['domains'].keys())[:3]}")
        print(f"  Leadership: {r['leadership_score']} | Impact: {r['impact_score']}")
        print(f"  Promotions: {r['promotion_count']} | Edu Score: {r['education_score']}")
        emb = r.get("candidate_embedding", [])
        print(f"  Embedding: [{len(emb)} floats] first 5: {emb[:5]}")

    # --- Quality checks ---
    print(f"\n--- Quality Checks ---")
    issues = []
    for r in results:
        if r.get("total_experience_years", 0) <= 0:
            issues.append(f"{r['id']}: zero experience years")
        if len(r.get("skills", {})) == 0:
            issues.append(f"{r['id']}: no skills extracted")
        if r.get("seniority") not in ["Junior", "Mid", "Senior", "Lead", "Principal"]:
            issues.append(f"{r['id']}: invalid seniority '{r.get('seniority')}'")

    if issues:
        for issue in issues[:10]:
            print(f"  [WARN] {issue}")
        if len(issues) > 10:
            print(f"  ... and {len(issues) - 10} more")
    else:
        print(f"  All quality checks passed!")

    print(f"\n{'='*60}")
    print(f"  VERIFICATION COMPLETE")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
