"""
Entry point for the Candidate Processing Pipeline.

Usage::

    python -m backend.main [--limit N] [--no-embeddings]
"""

import sys
import time
from pathlib import Path

# Ensure the backend package is importable when run from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.candidate_processing.parser import load_candidates
from backend.candidate_processing.candidate_processor import CandidateProcessor
from backend.candidate_processing.config import INPUT_FILE


def main() -> None:
    """Run the full pipeline."""
    import argparse

    parser = argparse.ArgumentParser(description="Candidate Processing Pipeline")
    parser.add_argument(
        "--input", type=str, default=None,
        help="Path to candidates.jsonl (default: config.INPUT_FILE)",
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Process only the first N candidates (useful for testing)",
    )
    parser.add_argument(
        "--no-embeddings", action="store_true",
        help="Skip embedding generation (faster for debugging)",
    )
    args = parser.parse_args()

    input_path = Path(args.input) if args.input else INPUT_FILE
    t0 = time.time()

    # 1. Load
    print("=" * 60)
    print("  Candidate Processing Pipeline")
    print("=" * 60)
    candidates = load_candidates(input_path, limit=args.limit)
    print(f"  Loaded {len(candidates)} candidates in {time.time() - t0:.2f}s\n")

    # 2. Process
    proc = CandidateProcessor(input_path=input_path)
    t1 = time.time()
    results = proc.process(candidates, show_progress=True)
    print(f"  Processed {len(results)} candidates in {time.time() - t1:.2f}s\n")

    # 3. Embeddings
    if not args.no_embeddings:
        t2 = time.time()
        results = proc.generate_embeddings_batch(results, candidates)
        print(f"  Embeddings generated in {time.time() - t2:.2f}s\n")

    # 4. Save
    out = proc.save(results)

    # 5. Summary
    total = time.time() - t0
    print(f"\n{'=' * 60}")
    print(f"  Done! {len(results)} candidates processed in {total:.2f}s")
    print(f"  Output: {out}")
    print(f"{'=' * 60}")

    # Quick sanity check: print one sample
    if results:
        sample = results[0]
        print("\n--- Sample output (first candidate) ---")
        for k, v in sample.items():
            if k == "candidate_embedding":
                print(f"  {k}: [{len(v)} floats]")
            else:
                print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
