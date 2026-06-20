"""
Job Description Parser

Extracts structured requirements from raw job description text.
Handles noisy formatting, inconsistent section headers, and free-form text.
"""

import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Skill alias normalisation (same as Part 1)
# ---------------------------------------------------------------------------
_SKILL_ALIASES: Dict[str, str] = {
    "js": "javascript", "ts": "typescript", "py": "python",
    "tf": "tensorflow", "k8s": "kubernetes", "node": "node.js",
    "nodejs": "node.js", "react.js": "react", "vue.js": "vue",
    "c sharp": "c#", "c plus plus": "c++", "golang": "go",
    "amazon web services": "aws", "google cloud": "gcp",
    "microsoft azure": "azure", "sklearn": "scikit-learn",
    "scikit learn": "scikit-learn", "postgres": "postgresql",
    "ci cd": "ci/cd", "cicd": "ci/cd", "dev ops": "devops",
    "machine-learning": "machine learning", "deep-learning": "deep learning",
    "restful api": "rest api", "rest apis": "rest api",
    "llms": "llm", "large language models": "llm",
    "retrieval augmented generation": "rag",
    "microservices": "microservices", "nextjs": "next.js",
}


def _normalise_skill(name: str) -> str:
    name = name.strip().lower()
    name = re.sub(r"[\s_]+", " ", name)
    return _SKILL_ALIASES.get(name, name)


# ---------------------------------------------------------------------------
# Known skill vocabulary (built from Part 1 data + common tech)
# ---------------------------------------------------------------------------
_KNOWN_SKILLS: set = set()

# We load them lazily from the processed candidates on first parse
_KNOWN_SKILLS_LOADED = False


def _load_known_skills(path: str = "") -> None:
    global _KNOWN_SKILLS, _KNOWN_SKILLS_LOADED
    if _KNOWN_SKILLS_LOADED:
        return
    # Minimal seed list for standalone parsing
    seed = [
        "python", "java", "javascript", "typescript", "react", "angular", "vue",
        "node.js", "django", "flask", "fastapi", "spring", "rails",
        "go", "rust", "c++", "c#", "swift", "kotlin",
        "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
        "aws", "gcp", "azure", "docker", "kubernetes", "terraform", "ansible",
        "kafka", "rabbitmq", "celery", "airflow", "spark", "hadoop",
        "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
        "machine learning", "deep learning", "nlp", "computer vision",
        "git", "ci/cd", "jenkins", "github actions", "gitlab ci",
        "graphql", "rest api", "grpc", "microservices",
        "linux", "bash", "shell scripting",
        "figma", "sketch", "adobe xd",
        "agile", "scrum", "jira",
        "tableau", "power bi", "excel",
        "blockchain", "solidity", "web3",
        "flutter", "react native", "dart",
        "sass", "tailwind", "webpack", "vite",
        "pytorch", "keras", "xgboost", "lightgbm",
        "hugging face", "langchain", "openai", "anthropic",
        "vector database", "pinecone", "weaviate", "milvus",
        "dbt", "snowflake", "bigquery", "redshift", "databricks",
        "prometheus", "grafana", "datadog",
        "html", "css",
        # JD-specific skills
        "sentence-transformers", "bge", "e5", "qdrant", "opensearch",
        "faiss", "ndcg", "mrr", "map", "a/b testing",
        "lora", "qlora", "peft", "learning-to-rank",
        "llm fine-tuning", "distributed systems", "hr-tech",
        "embedding", "retrieval", "ranking", "information retrieval",
        "recommendation", "search", "fine-tuning",
    ]
    _KNOWN_SKILLS = {_normalise_skill(s) for s in seed}
    if path:
        try:
            import json
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    rec = json.loads(line)
                    for sk in (rec.get("skills") or {}).keys():
                        _KNOWN_SKILLS.add(_normalise_skill(sk))
        except Exception as exc:
            logger.warning("Could not load known skills from %s: %s", path, exc)
    _KNOWN_SKILLS_LOADED = True


# ---------------------------------------------------------------------------
# Section header detection
# ---------------------------------------------------------------------------
_SECTION_PATTERNS = {
    "required_skills": re.compile(
        r"(must[\s-]*have|required|essential|core[\s-]*skills|"
        r"key[\s-]*skills|required[\s-]*skills|minimum[\s-]*qualifications|"
        r"things you absolutely need|what you(?:'d| would) actually be doing|"
        r"skills inventory)",
        re.IGNORECASE,
    ),
    "preferred_skills": re.compile(
        r"(nice[\s-]*to[\s-]*have|preferred|desired|bonus|plus|"
        r"good[\s-]*to[\s-]*have|preferred[\s-]*skills|"
        r"things we(?:'d| would) like you to have|things we like)",
        re.IGNORECASE,
    ),
    "experience": re.compile(
        r"(experience|years[\s-]*of|yoe|exp[\s.:]*|min[\s.]*(?:experience|years))",
        re.IGNORECASE,
    ),
    "seniority": re.compile(
        r"(seniority|level|grade|rank|position[\s-]*level)",
        re.IGNORECASE,
    ),
    "domains": re.compile(
        r"(domain|industry|sector|vertical|field|domain[\s-]*expertise)",
        re.IGNORECASE,
    ),
    "anti_patterns": re.compile(
        r"(things we explicitly do not want|what we(?:'d| would) not|"
        r"who we(?:'re| are) not looking for|disqualifiers)",
        re.IGNORECASE,
    ),
}

_TITLE_LEVEL_MAP: Dict[str, str] = {
    "intern": "Intern", "trainee": "Intern",
    "junior": "Junior", "jr": "Junior", "associate": "Junior",
    "mid": "Mid", "mid-level": "Mid", "intermediate": "Mid",
    "senior": "Senior", "sr": "Senior", "sr.": "Senior",
    "lead": "Lead", "tech lead": "Lead", "team lead": "Lead",
    "staff": "Staff", "principal": "Principal", "distinguished": "Principal",
    "director": "Principal", "vp": "Principal",
}

# Patterns for extracting years of experience
_YOE_PATTERNS = [
    re.compile(r"(\d{1,2})\+?\s*[-–]\s*(\d{1,2})\s*(?:years?|yrs?)", re.IGNORECASE),  # range like 5-9 years
    re.compile(r"(\d{1,2})\+?\s*(?:years?|yrs?)", re.IGNORECASE),
    re.compile(r"(?:experience|exp)[\s:]*(\d{1,2})\+?\s*(?:years?|yrs?)?", re.IGNORECASE),
    re.compile(r"(\d{1,2})\+?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:experience|exp)", re.IGNORECASE),
    re.compile(r"min(?:imum)?[\s:]*(\d{1,2})", re.IGNORECASE),
]


class JobParser:
    """Parse a raw job description string into structured requirements."""

    def __init__(self, candidates_path: str = "") -> None:
        _load_known_skills(candidates_path)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse(self, jd_text: str) -> Dict[str, Any]:
        """
        Parse a job description string.

        Parameters
        ----------
        jd_text : str
            Raw job description text.

        Returns
        -------
        dict with keys: ``required_skills``, ``preferred_skills``,
        ``experience``, ``seniority``, ``domains``, ``raw_text``.
        """
        if not jd_text or not jd_text.strip():
            return self._empty_result()

        text = jd_text.strip()

        # Try structured extraction first (for JDs with "skills inventory" sections)
        required_skills, preferred_skills = self._extract_skills_from_inventory(text)

        if not required_skills:
            # Fallback to section-based extraction
            sections = self._split_sections(text)
            required_skills = self._extract_skills(
                sections.get("required_skills", []),
                text,
            )
            preferred_skills = self._extract_skills(
                sections.get("preferred_skills", []),
                text,
                exclude=required_skills,
            )

        # If still no skills, scan full text
        if not required_skills and not preferred_skills:
            required_skills = self._extract_skills([], text)

        experience = self._extract_experience(text)
        seniority = self._extract_seniority(text)
        domains = self._extract_domains(text)

        return {
            "required_skills": sorted(required_skills),
            "preferred_skills": sorted(preferred_skills),
            "experience": experience,
            "seniority": seniority,
            "domains": sorted(domains),
            "raw_text": text,
        }

    def _extract_skills_from_inventory(self, text: str) -> tuple:
        """Extract skills from 'skills inventory' style sections."""
        required = set()
        preferred = set()

        # Look for "Things you absolutely need" section
        req_match = re.search(
            r"things you absolutely need\s*\n(.*?)(?=things (?:we|they)|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if req_match:
            section = req_match.group(1)
            for sk in _KNOWN_SKILLS:
                pattern = r"(?<!\w)" + re.escape(sk) + r"(?!\w)"
                if re.search(pattern, section.lower()):
                    required.add(sk)

        # Look for "Things we'd like you to have" section (including the "but won't reject you for" part)
        pref_match = re.search(
            r"things we(?:'d| would) like you to have[^a-z]*(.*?)(?=things (?:we|they)|final note|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if pref_match:
            section = pref_match.group(1)
            for sk in _KNOWN_SKILLS:
                pattern = r"(?<!\w)" + re.escape(sk) + r"(?!\w)"
                if re.search(pattern, section.lower()):
                    preferred.add(sk)

        return required, preferred

    # ------------------------------------------------------------------
    # Section splitting
    # ------------------------------------------------------------------

    def _split_sections(self, text: str) -> Dict[str, List[str]]:
        lines = text.split("\n")
        sections: Dict[str, List[str]] = {}
        current_section: Optional[str] = None

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            # Check if this line is a section header
            matched_section = None
            for section_name, pattern in _SECTION_PATTERNS.items():
                if pattern.search(stripped):
                    matched_section = section_name
                    break

            if matched_section:
                current_section = matched_section
                sections.setdefault(current_section, [])
                # Also capture content after the colon on the same line
                # e.g. "Preferred: Kafka, AWS" -> content is "Kafka, AWS"
                after_colon = re.split(r":\s*", stripped, maxsplit=1)
                if len(after_colon) > 1 and after_colon[1].strip():
                    sections[current_section].append(after_colon[1].strip())
            elif current_section:
                sections[current_section].append(stripped)
            else:
                # No section yet — try to infer from content
                sections.setdefault("_preamble", []).append(stripped)

        return sections

    # ------------------------------------------------------------------
    # Skill extraction
    # ------------------------------------------------------------------

    def _extract_skills(
        self,
        lines: List[str],
        full_text: str,
        exclude: Optional[set] = None,
    ) -> set:
        exclude = exclude or set()
        skills: set = set()

        # Extract from specific section lines
        for line in lines:
            cleaned = self._clean_skill_line(line)
            if cleaned:
                for token in cleaned:
                    ns = _normalise_skill(token)
                    if ns not in exclude and self._is_likely_skill(ns, token):
                        skills.add(ns)

        # Always scan full text for known skills (narrative JDs don't use bullet lists)
        lowered = full_text.lower()
        for sk in _KNOWN_SKILLS:
            if sk in lowered and sk not in exclude and sk not in skills:
                # Avoid matching partial words
                pattern = r"(?<!\w)" + re.escape(sk) + r"(?!\w)"
                if re.search(pattern, lowered):
                    skills.add(sk)

        return skills

    def _clean_skill_line(self, line: str) -> List[str]:
        """Extract skill tokens from a single line like '- Python' or '• Docker'."""
        # Skip lines that look like sentences (contain pronouns, verbs, etc.)
        narrative_indicators = [
            "we ", "you ", "if ", "your ", "this ", "that ", "the ", "and ",
            "but ", "or ", "not ", "with ", "for ", "are ", "is ", "have ",
            "will ", "would ", "should ", "can ", "could ", "need ",
        ]
        line_lower = line.lower().strip()
        if any(ind in line_lower for ind in narrative_indicators):
            return []
        # Skip lines that are too long to be a skill
        if len(line.strip()) > 60:
            return []

        line = re.sub(r"^[\s\-\•\*\►\>\:\.]+", "", line)
        line = re.sub(r"[\s\-\•\*\►\>\:\.]+$", "", line)
        if not line:
            return []
        # Split on commas, slashes, or newlines
        parts = re.split(r"[,;/\n]", line)
        return [p.strip() for p in parts if p.strip()]

    def _is_likely_skill(self, normalised: str, raw: str) -> bool:
        """Heuristic check whether a token is likely a skill name."""
        if normalised in _KNOWN_SKILLS:
            return True
        # If it's short and looks like a tech term
        if len(normalised) >= 2 and re.match(r"^[a-z0-9\+\#\.\-/ ]+$", normalised):
            return True
        return False

    # ------------------------------------------------------------------
    # Experience extraction
    # ------------------------------------------------------------------

    def _extract_experience(self, text: str) -> int:
        for pattern in _YOE_PATTERNS:
            match = pattern.search(text)
            if match:
                try:
                    groups = match.groups()
                    if len(groups) >= 2 and groups[1]:
                        # Range pattern: take the minimum
                        return min(int(groups[0]), int(groups[1]))
                    return int(groups[0])
                except (ValueError, IndexError):
                    continue
        return 0

    # ------------------------------------------------------------------
    # Seniority extraction
    # ------------------------------------------------------------------

    def _extract_seniority(self, text: str) -> str:
        lowered = text.lower()
        # First, check if the job title contains a seniority level
        # Look for patterns like "Senior AI Engineer" or "Lead Developer" at the start
        title_match = re.search(
            r"(?:job\s*title|position)[:\s]*([^\n]+)",
            lowered,
        )
        title_text = title_match.group(1) if title_match else ""
        if not title_text:
            # Try first line (often the title)
            first_line = lowered.split("\n")[0] if "\n" in lowered else lowered[:100]
            title_text = first_line

        # Check title for seniority
        for keyword, level in sorted(_TITLE_LEVEL_MAP.items(), key=lambda x: -len(x[0])):
            pattern = r"(?<!\w)" + re.escape(keyword) + r"(?!\w)"
            if re.search(pattern, title_text):
                return level

        # Fallback: check full text
        for keyword, level in sorted(_TITLE_LEVEL_MAP.items(), key=lambda x: -len(x[0])):
            pattern = r"(?<!\w)" + re.escape(keyword) + r"(?!\w)"
            if re.search(pattern, lowered):
                return level
        return "Mid"  # default

    # ------------------------------------------------------------------
    # Domain extraction
    # ------------------------------------------------------------------

    _DOMAIN_VOCAB: Dict[str, List[str]] = {
        "FinTech": ["fintech", "financial", "banking", "payments", "finance"],
        "Healthcare": ["healthcare", "health", "medical", "clinical", "biotech"],
        "E-commerce": ["ecommerce", "e-commerce", "retail", "marketplace"],
        "AI/ML": ["ai", "artificial intelligence", "machine learning", "ml", "deep learning"],
        "Cloud": ["cloud", "saas", "paas", "infrastructure"],
        "Cybersecurity": ["security", "cybersecurity", "infosec"],
        "Data Engineering": ["data engineering", "data pipeline", "analytics"],
        "Mobile": ["mobile", "android", "ios"],
        "Enterprise": ["enterprise", "b2b", "corporate"],
        "Consumer": ["consumer", "b2c", "social", "gaming"],
        "AdTech": ["adtech", "advertising", "programmatic"],
        "EdTech": ["edtech", "education", "e-learning"],
        "Logistics": ["logistics", "supply chain", "transportation"],
        "Media": ["media", "entertainment", "streaming"],
    }

    def _extract_domains(self, text: str) -> set:
        lowered = text.lower()
        domains: set = set()
        for domain, keywords in self._DOMAIN_VOCAB.items():
            for kw in keywords:
                if kw in lowered:
                    domains.add(domain)
                    break
        return domains

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _empty_result(self) -> Dict[str, Any]:
        return {
            "required_skills": [],
            "preferred_skills": [],
            "experience": 0,
            "seniority": "Mid",
            "domains": [],
            "raw_text": "",
        }
