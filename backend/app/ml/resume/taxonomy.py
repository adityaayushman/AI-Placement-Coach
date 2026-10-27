"""Curated skills taxonomy: canonical name -> (category, aliases, prerequisites).

Hand-written seed list for engineering placements; admins extend it via the `skills` table."""

TAXONOMY: dict[str, tuple[str, list[str], list[str]]] = {
    # Programming languages
    "python": ("language", ["python3", "py"], []),
    "java": ("language", ["core java", "java se"], []),
    "c++": ("language", ["cpp", "c plus plus"], []),
    "c": ("language", ["c language", "ansi c"], []),
    "javascript": ("language", ["js", "ecmascript", "es6"], []),
    "typescript": ("language", ["ts"], ["javascript"]),
    "go": ("language", ["golang"], []),
    "sql": ("data", ["mysql", "postgresql", "postgres", "sqlite", "t-sql", "pl/sql"], []),
    # CS fundamentals
    "data structures": ("dsa", ["dsa", "data structure"], ["programming basics"]),
    "algorithms": ("dsa", ["algorithm", "algorithmic"], ["data structures"]),
    "dynamic programming": ("dsa", ["dp", "memoization"], ["algorithms", "recursion"]),
    "recursion": ("dsa", ["recursive"], ["programming basics"]),
    "graphs": ("dsa", ["graph algorithms", "bfs", "dfs", "dijkstra"], ["data structures"]),
    "trees": ("dsa", ["binary tree", "bst", "binary search tree"], ["data structures"]),
    "programming basics": ("fundamentals", ["programming fundamentals"], []),
    "oop": ("fundamentals", ["object oriented", "object-oriented programming", "oops"], []),
    "operating systems": ("fundamentals", ["os", "operating system"], []),
    "dbms": ("fundamentals", ["database management", "database systems", "rdbms"], []),
    "computer networks": ("fundamentals", ["networking", "cn", "tcp/ip"], []),
    "system design": (
        "design",
        ["low level design", "high level design", "lld", "hld"],
        ["data structures", "dbms", "computer networks"],
    ),
    # Web / backend
    "react": ("web", ["react.js", "reactjs"], ["javascript"]),
    "node.js": ("web", ["node", "nodejs", "express", "express.js"], ["javascript"]),
    "html": ("web", ["html5"], []),
    "css": ("web", ["css3", "tailwind", "sass"], ["html"]),
    "rest api": ("web", ["rest", "restful", "api design"], []),
    "django": ("web", [], ["python"]),
    "flask": ("web", [], ["python"]),
    "fastapi": ("web", [], ["python"]),
    "spring boot": ("web", ["spring"], ["java"]),
    # Data / ML
    "machine learning": ("ml", ["ml", "scikit-learn", "sklearn"], ["python", "statistics"]),
    "deep learning": (
        "ml",
        ["neural networks", "pytorch", "tensorflow", "keras"],
        ["machine learning"],
    ),
    "nlp": ("ml", ["natural language processing", "transformers", "bert"], ["machine learning"]),
    "statistics": ("ml", ["probability", "statistical analysis"], []),
    "pandas": ("data", ["numpy"], ["python"]),
    "data analysis": ("data", ["data analytics", "excel", "power bi", "tableau"], []),
    # Tools / infra
    "git": ("tools", ["github", "gitlab", "version control"], []),
    "linux": ("tools", ["unix", "bash", "shell scripting"], []),
    "docker": ("tools", ["containers", "containerization"], ["linux"]),
    "kubernetes": ("tools", ["k8s"], ["docker"]),
    "aws": ("cloud", ["amazon web services", "ec2", "s3", "lambda"], []),
    "azure": ("cloud", ["microsoft azure"], []),
    "gcp": ("cloud", ["google cloud"], []),
    "ci/cd": ("tools", ["github actions", "jenkins", "continuous integration"], ["git"]),
    "testing": ("tools", ["unit testing", "pytest", "junit", "jest"], []),
    # Service-company emphasis
    "aptitude": ("aptitude", ["quantitative aptitude", "logical reasoning", "verbal ability"], []),
    "communication": ("soft", ["communication skills", "presentation", "public speaking"], []),
    "teamwork": ("soft", ["collaboration", "team player"], []),
    "problem solving": ("soft", ["analytical skills", "problem-solving"], []),
}

# Per-company-type skill weights used for gap ranking and recommendations.
COMPANY_WEIGHTS: dict[str, dict[str, float]] = {
    "product": {
        "dsa": 1.0,
        "design": 0.9,
        "language": 0.7,
        "fundamentals": 0.7,
        "web": 0.5,
        "ml": 0.5,
        "data": 0.5,
        "tools": 0.4,
        "cloud": 0.4,
        "aptitude": 0.3,
        "soft": 0.5,
    },
    "service": {
        "aptitude": 1.0,
        "soft": 0.9,
        "fundamentals": 0.9,
        "language": 0.7,
        "dsa": 0.5,
        "data": 0.5,
        "web": 0.5,
        "tools": 0.4,
        "design": 0.3,
        "ml": 0.3,
        "cloud": 0.4,
    },
}


def category_of(skill: str) -> str:
    entry = TAXONOMY.get(skill)
    return entry[0] if entry else "general"


def prerequisites_of(skill: str) -> list[str]:
    entry = TAXONOMY.get(skill)
    return entry[2] if entry else []


def skill_weight(skill: str, company_type: str) -> float:
    return COMPANY_WEIGHTS.get(company_type, COMPANY_WEIGHTS["product"]).get(
        category_of(skill), 0.4
    )
