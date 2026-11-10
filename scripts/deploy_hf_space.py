"""Push backend/ to a Hugging Face Space (Docker SDK) as this app's API.

Needs HF_TOKEN (a Space-scoped write token) and HF_SPACE ("username/space-name") as env vars.
Run by .github/workflows/deploy-hf-space.yml on every push to main; can also be run locally:

    HF_TOKEN=hf_xxx HF_SPACE=yourname/ai-placement-coach-api python scripts/deploy_hf_space.py
"""

import os
import sys
from pathlib import Path

README = """---
title: AI Placement Coach API
emoji: \U0001f393
colorFrom: yellow
colorTo: pink
sdk: docker
app_port: 7860
pinned: false
---

FastAPI backend for AI Placement Coach. Source and docs:
https://github.com/adityaayushman/AI-Placement-Coach
"""


def main() -> None:
    token = os.environ.get("HF_TOKEN")
    space = os.environ.get("HF_SPACE")
    if not token or not space:
        sys.exit("Set HF_TOKEN and HF_SPACE (e.g. 'username/ai-placement-coach-api').")

    from huggingface_hub import HfApi

    api = HfApi(token=token)
    api.create_repo(repo_id=space, repo_type="space", space_sdk="docker", exist_ok=True)

    root = Path(__file__).resolve().parents[1] / "backend"
    readme = root / "README_SPACE.md"
    readme.write_text(README, encoding="utf-8")
    try:
        api.upload_folder(
            folder_path=str(root),
            repo_id=space,
            repo_type="space",
            path_in_repo=".",
            commit_message="Deploy backend to Space",
            ignore_patterns=[".venv/**", "__pycache__/**", "*.pyc", "tests/**", "models-eval/**"],
        )
        # The Space reads its card from README.md at the repo root; our app has its own README
        # for `/docs`-adjacent context, so the Space metadata is uploaded under that name instead.
        api.upload_file(
            path_or_fileobj=str(readme),
            path_in_repo="README.md",
            repo_id=space,
            repo_type="space",
            commit_message="Space metadata",
        )
    finally:
        readme.unlink(missing_ok=True)

    print(f"Deployed to https://huggingface.co/spaces/{space}")


if __name__ == "__main__":
    main()
