"""Idempotent seed: skills, sample JDs, quiz and interview questions, learning resources, and an
admin account from ADMIN_EMAIL/ADMIN_PASSWORD. Job descriptions are illustrative samples, not
postings from real companies. Run: python -m app.seed"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.security import hash_password
from app.db.models import Assessment, JobDescription, LearningResource, QuestionBank, Skill, User
from app.ml.resume.taxonomy import TAXONOMY

SAMPLE_JDS = [
    {
        "company": "Sample Product Co. (illustrative)",
        "role": "Software Engineer I",
        "type": "product",
        "text": "Build and scale backend services used by millions. Strong data structures and "
        "algorithms, system design fundamentals, and one of Python, Java or Go. Experience with "
        "SQL databases, REST APIs, Git and Docker. You will design APIs, write tests, and "
        "improve latency and reliability.",
        "required_skills": [
            {"skill": "data structures", "weight": 1.0},
            {"skill": "algorithms", "weight": 1.0},
            {"skill": "system design", "weight": 0.8},
            {"skill": "python", "weight": 0.6},
            {"skill": "sql", "weight": 0.6},
            {"skill": "rest api", "weight": 0.5},
            {"skill": "git", "weight": 0.4},
            {"skill": "docker", "weight": 0.4},
            {"skill": "testing", "weight": 0.4},
        ],
    },
    {
        "company": "Sample Services Ltd. (illustrative)",
        "role": "Graduate Engineer Trainee",
        "type": "service",
        "text": "Join our delivery teams after a structured training programme. We look for "
        "strong aptitude and communication, programming fundamentals in Java or C++, OOP, "
        "DBMS and SQL basics, and willingness to learn new technologies. Teamwork and problem "
        "solving are essential.",
        "required_skills": [
            {"skill": "aptitude", "weight": 1.0},
            {"skill": "communication", "weight": 1.0},
            {"skill": "oop", "weight": 0.8},
            {"skill": "java", "weight": 0.6},
            {"skill": "dbms", "weight": 0.7},
            {"skill": "sql", "weight": 0.6},
            {"skill": "teamwork", "weight": 0.5},
            {"skill": "problem solving", "weight": 0.6},
        ],
    },
    {
        "company": "Sample Analytics Startup (illustrative)",
        "role": "Data Analyst / ML Intern",
        "type": "product",
        "text": "Analyse product data and build simple predictive models. Python with pandas, "
        "SQL, statistics, machine learning with scikit-learn, data visualisation, and clear "
        "communication of findings to stakeholders.",
        "required_skills": [
            {"skill": "python", "weight": 1.0},
            {"skill": "pandas", "weight": 0.8},
            {"skill": "sql", "weight": 0.8},
            {"skill": "statistics", "weight": 0.8},
            {"skill": "machine learning", "weight": 0.7},
            {"skill": "data analysis", "weight": 0.6},
            {"skill": "communication", "weight": 0.5},
        ],
    },
]

QUIZZES: dict[str, list[tuple[str, list[str], int]]] = {
    "data structures": [
        (
            "Average time to look up a key in a hash table?",
            ["O(1)", "O(log n)", "O(n)", "O(n log n)"],
            0,
        ),
        ("Which structure gives LIFO order?", ["Queue", "Stack", "Heap", "Deque only"], 1),
        (
            "A min-heap's root holds…",
            ["the largest key", "the median", "the smallest key", "a random key"],
            2,
        ),
        (
            "Inserting at the head of a singly linked list costs…",
            ["O(n)", "O(log n)", "O(1)", "O(n²)"],
            2,
        ),
    ],
    "algorithms": [
        ("Binary search requires the input to be…", ["sorted", "hashed", "unique", "small"], 0),
        ("Worst-case time of quicksort?", ["O(n log n)", "O(n²)", "O(n)", "O(log n)"], 1),
        (
            "BFS on an unweighted graph finds…",
            [
                "a minimum spanning tree",
                "shortest paths by edge count",
                "strongly connected components",
                "a topological order",
            ],
            1,
        ),
        ("Merge sort's extra space is typically…", ["O(1)", "O(log n)", "O(n)", "O(n²)"], 2),
    ],
    "dbms": [
        ("Which normal form removes partial dependencies?", ["1NF", "2NF", "3NF", "BCNF"], 1),
        ("ACID's 'I' stands for…", ["Integrity", "Isolation", "Indexing", "Idempotence"], 1),
        (
            "A primary key must be…",
            ["nullable", "unique and not null", "a string", "a foreign key"],
            1,
        ),
        (
            "Which join returns only matching rows from both tables?",
            ["LEFT JOIN", "FULL JOIN", "INNER JOIN", "CROSS JOIN"],
            2,
        ),
    ],
    "operating systems": [
        (
            "A deadlock needs mutual exclusion, hold-and-wait, no preemption and…",
            ["starvation", "circular wait", "paging", "thrashing"],
            1,
        ),
        (
            "Virtual memory mainly lets a process…",
            [
                "run faster",
                "use more address space than physical RAM",
                "avoid system calls",
                "skip scheduling",
            ],
            1,
        ),
        (
            "Threads of one process share…",
            ["stack", "registers", "address space", "program counter"],
            2,
        ),
        (
            "Round-robin scheduling uses a…",
            ["priority queue", "time quantum", "stack", "lottery"],
            1,
        ),
    ],
    "aptitude": [
        ("A train covers 120 km in 1.5 h. Speed?", ["60 km/h", "80 km/h", "90 km/h", "75 km/h"], 1),
        ("20% of 250 is…", ["25", "45", "50", "60"], 2),
        ("Next in series 2, 6, 12, 20, …?", ["28", "30", "32", "26"], 1),
        (
            "If 5 workers finish a job in 12 days, 6 workers take…",
            ["10 days", "9 days", "14 days", "11 days"],
            0,
        ),
    ],
    "oop": [
        (
            "Hiding internal state behind methods is…",
            ["inheritance", "encapsulation", "polymorphism", "abstraction only"],
            1,
        ),
        (
            "Method overriding is an example of…",
            ["compile-time polymorphism", "runtime polymorphism", "encapsulation", "composition"],
            1,
        ),
        (
            "'Prefer composition over inheritance' mainly reduces…",
            ["memory use", "tight coupling", "runtime speed", "file count"],
            1,
        ),
        (
            "An abstract class can…",
            [
                "never have methods",
                "not be instantiated directly",
                "only have static fields",
                "not be inherited",
            ],
            1,
        ),
    ],
}

INTERVIEW = [
    (
        "hr",
        None,
        "Tell me about yourself.",
        [
            "current studies and branch",
            "one or two key projects or internships",
            "skills relevant to the role",
            "why this role or company",
        ],
        "I'm a final-year computer science student. I've built two backend projects, including a "
        "REST API used by our college club, and interned at a startup where I improved query "
        "performance. I enjoy problem solving and I'm looking for a role where I can grow as a "
        "software engineer.",
    ),
    (
        "behavioral",
        None,
        "Describe a time you handled a conflict in a team project.",
        [
            "the situation and your role",
            "the action you took",
            "how you communicated",
            "the result and what you learned",
        ],
        "In my final-year project two teammates disagreed about the database. I set up a short "
        "meeting, listed requirements, and we benchmarked both options. We chose PostgreSQL, "
        "delivered on time, and I learned to settle debates with data.",
    ),
    (
        "technical",
        "dbms",
        "What is database normalisation and why does it matter?",
        [
            "reduces redundancy",
            "avoids update anomalies",
            "normal forms such as 1NF 2NF 3NF",
            "trade-off with joins and denormalisation for reads",
        ],
        "Normalisation organises tables to reduce redundancy and prevent insert, update and delete "
        "anomalies. 1NF removes repeating groups, 2NF removes partial dependencies, 3NF removes "
        "transitive dependencies. Heavily read systems sometimes denormalise for speed.",
    ),
    (
        "technical",
        "operating systems",
        "Explain the difference between a process and a thread.",
        [
            "process has its own address space",
            "threads share memory within a process",
            "context switch cost",
            "synchronisation needed for shared data",
        ],
        "A process is an independent program with its own address space. Threads run inside a "
        "process and share its memory, so they are cheaper to create and switch, but shared data "
        "needs synchronisation such as locks.",
    ),
    (
        "dsa",
        "algorithms",
        "How would you find whether a linked list has a cycle?",
        [
            "two pointers slow and fast",
            "fast moves two steps",
            "they meet if a cycle exists",
            "O(n) time and O(1) space",
        ],
        "Use Floyd's algorithm: a slow pointer moves one step and a fast pointer two steps. If "
        "there is a cycle they eventually meet; if fast reaches null there is none. It runs in "
        "O(n) time with O(1) extra space.",
    ),
    (
        "dsa",
        "data structures",
        "When would you use a hash map instead of a balanced BST?",
        [
            "average constant time lookup",
            "no ordering in hash map",
            "BST keeps keys sorted",
            "range queries favour BST",
        ],
        "A hash map gives average O(1) lookups when I only need membership or key-value access. A "
        "balanced BST gives O(log n) operations but keeps keys ordered, so it suits range queries "
        "or sorted iteration.",
    ),
]

RESOURCES = [
    (
        "data structures",
        "VisuAlgo: visualising data structures",
        "https://visualgo.net/en",
        "interactive",
        60,
    ),
    ("algorithms", "CP-Algorithms", "https://cp-algorithms.com/", "reference", 90),
    (
        "dynamic programming",
        "CP-Algorithms: introduction to DP",
        "https://cp-algorithms.com/dynamic_programming/intro-to-dp.html",
        "article",
        45,
    ),
    (
        "graphs",
        "CP-Algorithms: breadth-first search",
        "https://cp-algorithms.com/graph/breadth-first-search.html",
        "article",
        30,
    ),
    ("trees", "VisuAlgo: binary search trees", "https://visualgo.net/en/bst", "interactive", 30),
    (
        "recursion",
        "VisuAlgo: recursion trees",
        "https://visualgo.net/en/recursion",
        "interactive",
        30,
    ),
    (
        "system design",
        "The System Design Primer",
        "https://github.com/donnemartin/system-design-primer",
        "guide",
        120,
    ),
    (
        "operating systems",
        "Operating Systems: Three Easy Pieces",
        "https://pages.cs.wisc.edu/~remzi/OSTEP/",
        "book",
        120,
    ),
    (
        "computer networks",
        "Computer Networks: A Systems Approach",
        "https://book.systemsapproach.org/",
        "book",
        120,
    ),
    (
        "dbms",
        "PostgreSQL tutorial",
        "https://www.postgresql.org/docs/current/tutorial.html",
        "tutorial",
        60,
    ),
    (
        "sql",
        "PostgreSQL tutorial: the SQL language",
        "https://www.postgresql.org/docs/current/tutorial-sql.html",
        "tutorial",
        45,
    ),
    ("python", "The Python tutorial", "https://docs.python.org/3/tutorial/", "tutorial", 90),
    (
        "javascript",
        "MDN: JavaScript guide",
        "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide",
        "guide",
        90,
    ),
    ("react", "React: Learn", "https://react.dev/learn", "tutorial", 90),
    ("git", "Pro Git book", "https://git-scm.com/book/en/v2", "book", 60),
    ("docker", "Docker: get started", "https://docs.docker.com/get-started/", "tutorial", 60),
    (
        "machine learning",
        "scikit-learn tutorials",
        "https://scikit-learn.org/stable/tutorial/index.html",
        "tutorial",
        90,
    ),
    (
        "oop",
        "Java tutorial: OOP concepts",
        "https://docs.oracle.com/javase/tutorial/java/concepts/",
        "tutorial",
        45,
    ),
    ("java", "Java tutorials (Oracle)", "https://docs.oracle.com/javase/tutorial/", "tutorial", 90),
    (
        "aptitude",
        "IndiaBix aptitude practice",
        "https://www.indiabix.com/aptitude/questions-and-answers/",
        "practice",
        30,
    ),
    (
        "communication",
        "The STAR interview method",
        "https://www.themuse.com/advice/star-interview-method",
        "article",
        15,
    ),
    (
        "statistics",
        "OpenIntro Statistics (free textbook)",
        "https://www.openintro.org/book/os/",
        "book",
        120,
    ),
]


def seed(db: Session) -> None:
    if not db.scalar(select(Skill).limit(1)):
        db.add_all(
            Skill(name=n, category=c, aliases=a, prerequisites=p)
            for n, (c, a, p) in TAXONOMY.items()
        )
    if not db.scalar(select(JobDescription).limit(1)):
        db.add_all(JobDescription(**jd) for jd in SAMPLE_JDS)
    if not db.scalar(select(QuestionBank).limit(1)):
        for skill, items in QUIZZES.items():
            qs = [
                QuestionBank(
                    kind="quiz",
                    skill=skill,
                    category="technical",
                    prompt=p,
                    options=o,
                    answer_index=a,
                )
                for p, o, a in items
            ]
            db.add_all(qs)
            db.flush()
            db.add(
                Assessment(
                    title=f"{skill.title()} check", skill=skill, question_ids=[q.id for q in qs]
                )
            )
        for i, (cat, iskill, prompt, kps, ref) in enumerate(INTERVIEW):
            db.add(
                QuestionBank(
                    kind="interview",
                    category=cat,
                    skill=iskill or "",
                    difficulty=1 + i % 2,
                    prompt=prompt,
                    key_points=kps,
                    reference_answer=ref,
                )
            )
    if not db.scalar(select(LearningResource).limit(1)):
        db.add_all(
            LearningResource(skill=s, title=t, url=u, kind=k, minutes=m)
            for s, t, u, k, m in RESOURCES
        )
    s = get_settings()
    if (
        s.admin_email
        and s.admin_password
        and not db.scalar(select(User).where(User.email == s.admin_email.lower()))
    ):
        db.add(
            User(
                email=s.admin_email.lower(),
                full_name="Administrator",
                role="admin",
                password_hash=hash_password(s.admin_password),
            )
        )
    db.commit()


if __name__ == "__main__":
    from app.db.base import Base
    from app.db.session import get_engine, get_sessionmaker

    Base.metadata.create_all(get_engine())
    with get_sessionmaker()() as session:
        seed(session)
    print("seeded")
