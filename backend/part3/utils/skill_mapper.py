"""
Skill normalization and synonym mapping.

Handles aliases (py -> python), related skills (FastAPI ~ Flask),
and fuzzy matching for skill comparison.
"""

import re
from typing import Dict, Set, List, Optional


# ---------------------------------------------------------------------------
# Direct aliases: multiple names for the same tool/technology
# ---------------------------------------------------------------------------
SKILL_ALIASES: Dict[str, str] = {
    # Languages
    "py": "python",
    "python3": "python",
    "js": "javascript",
    "ts": "typescript",
    "c sharp": "c#",
    "c plus plus": "c++",
    "golang": "go",
    # Frameworks
    "react.js": "react",
    "vue.js": "vue",
    "nextjs": "next.js",
    "nodejs": "node.js",
    "node": "node.js",
    "angular.js": "angular",
    # Cloud
    "amazon web services": "aws",
    "google cloud": "gcp",
    "google cloud platform": "gcp",
    "microsoft azure": "azure",
    "ms azure": "azure",
    # Data
    "sklearn": "scikit-learn",
    "scikit learn": "scikit-learn",
    "postgres": "postgresql",
    "postgres sql": "postgresql",
    "mssql": "sql server",
    "ms sql": "sql server",
    # DevOps
    "k8s": "kubernetes",
    "ci cd": "ci/cd",
    "cicd": "ci/cd",
    "dev ops": "devops",
    # ML/AI
    "tensorflow": "tensorflow",
    "tf": "tensorflow",
    "pytorch": "pytorch",
    "machine-learning": "machine learning",
    "deep-learning": "deep learning",
    "llms": "llm",
    "large language models": "llm",
    "retrieval augmented generation": "rag",
    "natural language processing": "nlp",
    # APIs
    "restful api": "rest api",
    "rest apis": "rest api",
    "restful apis": "rest api",
    # Misc
    "microservices": "microservices",
    "micro-service": "microservices",
}


# ---------------------------------------------------------------------------
# Related skills: skills that are "close enough" to count as partial matches
# Each entry maps a skill to a group of related skills.
# ---------------------------------------------------------------------------
SKILL_SYNONYM_GROUPS: List[Set[str]] = [
    # Web frameworks
    {"fastapi", "flask", "django", "starlette", "sanic", "tornado"},
    {"express", "express.js", "koa", "hapi", "fastify"},
    {"react", "angular", "vue", "vue.js", "svelte", "preact"},
    {"next.js", "nuxt", "gatsby", "remix"},
    # Languages in same family
    {"python", "ruby", "perl", "php"},
    {"java", "kotlin", "scala", "clojure"},
    {"javascript", "typescript", "coffeescript"},
    {"c", "c++", "c#", "rust", "go"},
    # Cloud providers
    {"aws", "gcp", "azure"},
    {"s3", "gcs", "blob storage"},
    {"ec2", "compute engine", "virtual machines"},
    # Databases
    {"postgresql", "mysql", "mariadb", "sqlite"},
    {"mongodb", "couchdb", "dynamodb"},
    {"redis", "memcached", "elasticsearch"},
    {"sql server", "oracle db", "db2"},
    # Data processing
    {"spark", "flink", "beam"},
    {"kafka", "rabbitmq", "nats", "pulsar"},
    {"airflow", "luigi", "prefect", "dagster"},
    {"snowflake", "bigquery", "redshift", "databricks"},
    # ML frameworks
    {"tensorflow", "pytorch", "keras", "jax"},
    {"scikit-learn", "xgboost", "lightgbm", "catboost"},
    {"transformers", "huggingface", "hugging face"},
    # Container/orchestration
    {"docker", "podman", "containerd"},
    {"kubernetes", "docker swarm", "nomad", "ecs"},
    # IaC
    {"terraform", "pulumi", "cloudformation"},
    {"ansible", "chef", "puppet", "saltstack"},
    # Monitoring
    {"prometheus", "grafana", "datadog", "new relic"},
    {"elk", "elasticsearch", "splunk"},
    # Mobile
    {"android", "ios"},
    {"flutter", "react native", "xamarin"},
    {"swift", "objective-c"},
    {"kotlin", "java"},
]


# ---------------------------------------------------------------------------
# Build reverse lookup: skill -> group index
# ---------------------------------------------------------------------------
_GROUP_INDEX: Dict[str, int] = {}
for _i, _group in enumerate(SKILL_SYNONYM_GROUPS):
    for _skill in _group:
        _GROUP_INDEX[_skill] = _i


def normalise_skill(name: str) -> str:
    """
    Normalise a skill name to lowercase, canonical form.

    Parameters
    ----------
    name : str
        Raw skill name.

    Returns
    -------
    str
        Normalised skill name.
    """
    name = name.strip().lower()
    name = re.sub(r"[\s_]+", " ", name)
    return SKILL_ALIASES.get(name, name)


def are_skills_related(skill_a: str, skill_b: str) -> bool:
    """
    Check if two skills are related (in the same synonym group).

    Parameters
    ----------
    skill_a : str
        First skill (normalised).
    skill_b : str
        Second skill (normalised).

    Returns
    -------
    bool
        True if skills are in the same synonym group.
    """
    if skill_a == skill_b:
        return True
    group_a = _GROUP_INDEX.get(skill_a)
    group_b = _GROUP_INDEX.get(skill_b)
    if group_a is not None and group_b is not None:
        return group_a == group_b
    return False


def skill_match_strength(
    candidate_skill: str,
    required_skill: str,
) -> float:
    """
    Return match strength between a candidate skill and required skill.

    Returns
    -------
    float
        1.0 for exact match, 0.5 for related match, 0.0 for no match.
    """
    cs = normalise_skill(candidate_skill)
    rs = normalise_skill(required_skill)
    if cs == rs:
        return 1.0
    if are_skills_related(cs, rs):
        return 0.5
    return 0.0


def find_best_skill_match(
    target: str,
    candidate_skills: List[str],
) -> tuple:
    """
    Find the best matching skill in a candidate's skill list.

    Parameters
    ----------
    target : str
        The skill we're looking for.
    candidate_skills : list[str]
        Candidate's skill names.

    Returns
    -------
    tuple of (best_match: str, strength: float)
    """
    target_norm = normalise_skill(target)
    best_match = ""
    best_strength = 0.0

    for sk in candidate_skills:
        strength = skill_match_strength(sk, target)
        if strength > best_strength:
            best_strength = strength
            best_match = sk

    return best_match, best_strength
