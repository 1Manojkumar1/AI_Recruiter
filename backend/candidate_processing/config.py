"""
Configuration module for the Candidate Processing Pipeline.
Centralizes all tunable parameters, thresholds, and mappings.
"""

from pathlib import Path
from typing import Dict

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR: Path = Path(__file__).resolve().parent.parent
DATA_DIR: Path = BASE_DIR
INPUT_FILE: Path = DATA_DIR / "candidates.jsonl"
OUTPUT_FILE: Path = DATA_DIR / "processed_candidates.jsonl"

# ---------------------------------------------------------------------------
# Education scoring
# ---------------------------------------------------------------------------
EDUCATION_TIER_SCORES: Dict[str, float] = {
    "tier_1": 1.0,
    "tier_2": 0.8,
    "tier_3": 0.6,
    "tier_4": 0.4,
}

DEGREE_LEVEL_BONUS: Dict[str, float] = {
    "phd": 0.15,
    "doctorate": 0.15,
    "m.s.": 0.10,
    "ms": 0.10,
    "m.sc": 0.10,
    "m.sc.": 0.10,
    "m.e.": 0.10,
    "me": 0.10,
    "m.tech": 0.10,
    "mtech": 0.10,
    "mba": 0.10,
    "m.eng": 0.10,
    "b.e.": 0.0,
    "be": 0.0,
    "b.tech": 0.0,
    "btech": 0.0,
    "b.sc": 0.0,
    "b.sc.": 0.0,
    "bachelor": 0.0,
    "bachelor of engineering": 0.0,
    "bachelor of science": 0.0,
}

# ---------------------------------------------------------------------------
# Skill scoring weights
# ---------------------------------------------------------------------------
PROFICIENCY_WEIGHTS: Dict[str, float] = {
    "expert": 1.0,
    "advanced": 0.85,
    "intermediate": 0.65,
    "beginner": 0.4,
}

ENDORSEMENT_MAX_FOR_SCALING: int = 50
ENDORSEMENT_WEIGHT: float = 0.25
PROFICIENCY_WEIGHT: float = 0.55
EXPERIENCE_WEIGHT: float = 0.20

# ---------------------------------------------------------------------------
# Career / seniority thresholds
# ---------------------------------------------------------------------------
JUNIOR_MAX_YEARS: float = 2.0
MID_MAX_YEARS: float = 5.0
SENIOR_MAX_YEARS: float = 10.0
LEAD_MAX_YEARS: float = 15.0

LEADERSHIP_KEYWORDS: list = [
    "led team", "led a team", "managed team", "managed a team",
    "team lead", "tech lead", "engineering manager", "direct report",
    "mentored", "mentoring", "coaching", "managed engineers",
    "led engineers", "leadership", "supervised", "oversaw",
    "directly managed", "people management", "team lead",
    "project lead", "program lead", "managed a group",
    "headed", "directed", "guided team", "supervising",
]

IMPACT_KEYWORDS: list = [
    "reduced", "improved", "increased", "saved", "built scalable",
    "optimized", "streamlined", "automated", "cut costs", "revenue",
    "performance", "latency", "throughput", "deployed", "scaled",
    "launched", "delivered", "shipped", "migrated", "transformed",
    "cost reduction", "efficiency", "reduced latency", "improved performance",
    "saved costs", "increased revenue", "built scalable systems",
    "reduced cost", "improved accuracy", "reduced time", "accelerated",
    "boosted", "enhanced", "lowered", "eliminated", "decreased",
    "drove adoption", "grew", "expanded", "achieved", "exceeded",
]

PROMOTION_KEYWORDS: list = [
    "promoted", "promotion", "advanced to", "elevated to",
    "moved to senior", "moved to lead", "stepped up",
]

# ---------------------------------------------------------------------------
# Domain classification keyword maps
# ---------------------------------------------------------------------------
DOMAIN_KEYWORDS: Dict[str, list] = {
    "Backend": [
        "python", "java", "go", "golang", "node.js", "nodejs", "ruby",
        "rust", "c++", "c#", ".net", "spring", "django", "fastapi", "flask",
        "express", "rest", "grpc", "api", "microservice", "sql", "postgres",
        "mysql", "mongodb", "redis", "kafka", "rabbitmq", "celery",
        "backend", "server-side", "distributed systems", "system design",
    ],
    "Frontend": [
        "javascript", "typescript", "react", "angular", "vue", "vue.js",
        "next.js", "nextjs", "html", "css", "sass", "tailwind", "webpack",
        "vite", "svelte", "frontend", "ui", "ux", "web components",
        "responsive design", "accessibility", "figma",
    ],
    "AI/ML": [
        "machine learning", "deep learning", "tensorflow", "pytorch",
        "keras", "scikit-learn", "sklearn", "nlp", "natural language",
        "computer vision", "opencv", "transformers", "hugging face",
        "llm", "large language model", "rag", "retrieval augmented",
        "data science", "neural network", "xgboost", "lightgbm",
        "mlops", "ml pipeline", "feature engineering", "model training",
        "ai", "artificial intelligence", "generative ai", "genai",
        "langchain", "openai", "anthropic", "vector database",
        "embedding", "fine-tuning", "fine tuning", "huggingface",
    ],
    "Cloud": [
        "aws", "amazon web services", "gcp", "google cloud",
        "azure", "cloud architecture", "serverless", "lambda",
        "ec2", "s3", "cloudformation", "cloud run", "cloud functions",
        "cloud infrastructure", "multi-cloud", "cloud native",
    ],
    "DevOps": [
        "docker", "kubernetes", "k8s", "terraform", "ansible",
        "jenkins", "gitlab ci", "github actions", "ci/cd",
        "cicd", "devops", "infrastructure as code", "iac",
        "prometheus", "grafana", "elk", "datadog", "monitoring",
        "argo cd", "argocd", "helm", "istio",
    ],
    "Data Engineering": [
        "spark", "apache spark", "airflow", "etl", "data pipeline",
        "data warehouse", "snowflake", "bigquery", "redshift",
        "databricks", "hadoop", "hive", "presto", "trino",
        "dbt", "data lake", "streaming", "kafka streams",
        "data engineering", "delta lake", "iceberg",
    ],
    "Cybersecurity": [
        "security", "cybersecurity", "penetration testing",
        "vulnerability", "owasp", "siem", "firewall", "encryption",
        "identity management", "oauth", "jwt", "soc", "compliance",
        "gdpr", "hipaa", "zero trust",
    ],
    "Mobile": [
        "android", "ios", "swift", "kotlin", "react native",
        "flutter", "dart", "xamarin", "ionic", "mobile development",
        "mobile app", "ios development", "android development",
    ],
    "Product": [
        "product management", "product manager", "roadmap",
        "stakeholder", "user research", "a/b testing", "analytics",
        "metrics", "kpi", "okr", "agile", "scrum", "jira",
        "product strategy", "go-to-market", "gtm",
    ],
    "Data Science": [
        "data analysis", "data analyst", "power bi", "tableau",
        "statistics", "statistical modeling", "regression",
        "classification", "clustering", "visualization",
        "pandas", "numpy", "matplotlib", "seaborn",
    ],
}

# ---------------------------------------------------------------------------
# Seniority level titles (used for promotion detection)
# ---------------------------------------------------------------------------
SENIORITY_TITLES_ORDERED: list = [
    "intern", "trainee", "junior", "associate",
    "software engineer", "engineer", "developer",
    "senior", "senior engineer", "senior software engineer",
    "staff", "staff engineer", "principal",
    "lead", "tech lead", "team lead",
    "manager", "engineering manager",
    "director", "vp", "vice president",
]

# ---------------------------------------------------------------------------
# Embedding config
# ---------------------------------------------------------------------------
EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
EMBEDDING_BATCH_SIZE: int = 64
EMBEDDING_MAX_CHARS: int = 2000

# ---------------------------------------------------------------------------
# Processing config
# ---------------------------------------------------------------------------
BATCH_SIZE: int = 100
