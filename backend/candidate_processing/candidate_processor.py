"""
Main orchestrator for candidate processing.

Coordinates all sub-modules and produces the final structured output
for each candidate.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from tqdm import tqdm

from .config import OUTPUT_FILE, EMBEDDING_MAX_CHARS
from .parser import load_candidates
from .skill_processor import SkillProcessor
from .education_analyzer import EducationAnalyzer
from .career_analyzer import CareerAnalyzer
from .trait_extractor import TraitExtractor
from .summary_generator import SummaryGenerator
from .embedding_generator import build_candidate_text, generate_embeddings
from .redrob_signal_extractor import extract_redrob_signals
from .utils import safe_float


class CandidateProcessor:
    """
    End-to-end candidate processing pipeline.

    Usage::

        processor = CandidateProcessor()
        results = processor.process()
        processor.save(results)
    """

    def __init__(self, input_path: Optional[Path] = None) -> None:
        self._input_path = input_path
        self._skill_processor = SkillProcessor()
        self._education_analyzer = EducationAnalyzer()
        self._career_analyzer = CareerAnalyzer()
        self._trait_extractor = TraitExtractor()
        self._summary_generator = SummaryGenerator()

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def process(
        self,
        candidates: Optional[List[Dict[str, Any]]] = None,
        show_progress: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Process all candidates through the full pipeline using multiprocessing.

        Parameters
        ----------
        candidates : list[dict], optional
            Pre-loaded candidate records.  When ``None`` they are loaded
            from the configured input file.
        show_progress : bool
            Whether to display a progress bar.

        Returns
        -------
        list[dict]
            Structured output for each candidate.
        """
        if candidates is None:
            candidates = load_candidates(self._input_path)

        import concurrent.futures
        import os

        num_workers = min(os.cpu_count() or 4, 16)
        results: List[Dict[str, Any]] = []

        if show_progress:
            with concurrent.futures.ProcessPoolExecutor(max_workers=num_workers) as executor:
                results = list(tqdm(
                    executor.map(_process_single_helper, candidates, chunksize=100),
                    total=len(candidates),
                    desc="Processing candidates"
                ))
        else:
            with concurrent.futures.ProcessPoolExecutor(max_workers=num_workers) as executor:
                results = list(executor.map(_process_single_helper, candidates, chunksize=100))

        return results

    def save(
        self,
        results: List[Dict[str, Any]],
        output_path: Optional[Path] = None,
    ) -> Path:
        """
        Write processed results to a JSONL file.

        Parameters
        ----------
        results : list[dict]
            Output of :meth:`process`.
        output_path : Path, optional
            Defaults to ``config.OUTPUT_FILE``.

        Returns
        -------
        Path
            Path to the written file.
        """
        path = output_path or OUTPUT_FILE
        with open(path, "w", encoding="utf-8") as fh:
            for record in results:
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(f"[INFO] Saved {len(results)} processed candidates to {path}")
        return path

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _process_single(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Run every stage for a single candidate record."""
        cid = record.get("candidate_id") or ""
        profile = record.get("profile") or {}
        career_history = record.get("career_history") or []
        education = record.get("education") or []
        skills_raw = record.get("skills") or []

        # 1. Skills
        skills = self._skill_processor.process(skills_raw)

        # 2. Education
        education_info = self._education_analyzer.analyze(education)

        # 3. Career
        career_info = self._career_analyzer.analyze(profile, career_history)

        # 4. Traits
        traits = self._trait_extractor.extract(
            profile=profile,
            career_history=career_history,
            skills=skills,
            education_info=education_info,
            career_info=career_info,
        )

        # 5. Summary
        summary = self._summary_generator.generate(
            profile=profile,
            career_info=career_info,
            education_info=education_info,
            skills=skills,
            domains=traits["domain_expertise"],
            leadership_score=traits["leadership_score"],
            impact_score=traits["impact_score"],
            seniority=traits["seniority"],
        )

        # 6. Redrob platform signals
        redrob_raw = record.get("redrob_signals") or {}
        redrob = extract_redrob_signals(redrob_raw)

        return {
            "candidate_id": cid,
            "profile_summary": summary,
            "skills": skills,
            "domains": traits["domain_expertise"],
            "leadership_score": traits["leadership_score"],
            "impact_score": traits["impact_score"],
            "career_growth_score": career_info["career_growth_score"],
            "promotion_count": career_info["promotion_count"],
            "education_score": education_info["education_score"],
            "seniority": traits["seniority"],
            "total_experience_years": career_info["total_experience_years"],
            "years_in_current_role": career_info["years_in_current_role"],
            "redrob_signals": redrob,
            "companies": [job.get("company", "") for job in career_history if job.get("company")],
            "candidate_embedding": [],  # filled in batch step
        }

    def generate_embeddings_batch(
        self,
        results: List[Dict[str, Any]],
        raw_candidates: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Add embeddings to already-processed results.

        This is separated so the sentence-transformer model is only
        loaded once and applied in a single batch.

        Parameters
        ----------
        results : list[dict]
            Output of :meth:`process`.
        raw_candidates : list[dict]
            Original raw records (needed to reconstruct text).

        Returns
        -------
        list[dict]
            Same list with ``candidate_embedding`` populated.
        """
        texts: List[str] = []
        for raw in raw_candidates:
            text = build_candidate_text(
                profile=raw.get("profile") or {},
                career_history=raw.get("career_history") or [],
                skills=raw.get("skills") or [],
                education=raw.get("education") or [],
            )
            texts.append(text)

        print("[INFO] Generating embeddings ...")
        embeddings = generate_embeddings(texts)

        for result, emb in zip(results, embeddings):
            result["candidate_embedding"] = emb.tolist() if hasattr(emb, "tolist") else list(emb)

        print(f"[INFO] Generated embeddings for {len(results)} candidates.")
        return results


def _process_single_helper(record: Dict[str, Any]) -> Dict[str, Any]:
    """Helper function for multiprocessing to avoid binding issues."""
    proc = CandidateProcessor()
    return proc._process_single(record)

