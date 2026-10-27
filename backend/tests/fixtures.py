"""Author-constructed resume / JD fixtures. Gap labels are defined by construction (we wrote the
resumes knowing which skills they contain), not by independent human annotators."""

STRONG_RESUME = """Asha Rao
asha.rao@example.com | +91 98765 43210

Summary
Final-year CSE student who builds reliable backend services.

Education
B.Tech Computer Science, CGPA 8.6, 2022-2026

Experience
Backend Intern, Example Labs
• Built REST API endpoints in Python and FastAPI serving 2k users
• Reduced p95 latency by 40% by adding PostgreSQL indexes
• Wrote unit tests with pytest and set up GitHub Actions CI

Projects
• Campus marketplace: designed a system with React, Node.js and SQL; 500 users
• Implemented graph algorithms (BFS, Dijkstra) for route planning, 3x faster than baseline
• Deployed services with Docker on AWS EC2

Skills
Python, Java, SQL, Data Structures, Algorithms, Git, Docker, React, System Design

Certifications
AWS Cloud Practitioner
"""

WEAK_RESUME = """Ravi
I am a hard working student. I know computers and I like to learn new things.
I did a project in college about a website. I am good at teamwork.
"""

# (resume, jd_index into seed.SAMPLE_JDS, expected gap skills by construction)
GAP_CASES = [
    (STRONG_RESUME, 0, set()),
    (STRONG_RESUME, 1, {"aptitude", "communication", "oop", "dbms", "problem solving", "teamwork"}),
    (
        WEAK_RESUME,
        0,
        {
            "data structures",
            "algorithms",
            "system design",
            "python",
            "sql",
            "rest api",
            "git",
            "docker",
            "testing",
        },
    ),
    (
        WEAK_RESUME,
        2,
        {
            "python",
            "pandas",
            "sql",
            "statistics",
            "machine learning",
            "data analysis",
            "communication",
        },
    ),
]
