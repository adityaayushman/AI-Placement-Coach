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


def fail(message: str) -> None:
    """Print a GitHub Actions error annotation (visible via the Checks API without admin rights
    on the repo, unlike the run's raw logs) and exit non-zero."""
    print(f"::error title=deploy-hf-space failed::{message}")
    sys.exit(1)


def main() -> None:
    # Defensive .strip(): a trailing newline or space pasted into a GitHub secret/variable is a
    # common, otherwise-silent cause of "invalid token" / "repo not found" errors.
    token = (os.environ.get("HF_TOKEN") or "").strip()
    space = (os.environ.get("HF_SPACE") or "").strip()
    if not token or not space:
        fail("HF_TOKEN and/or HF_SPACE is not set (check repo Settings > Secrets and variables).")
    if space.count("/") != 1:
        fail(f"HF_SPACE should look like 'username/space-name', got {space!r}.")

    from huggingface_hub import HfApi
    from huggingface_hub.utils import HfHubHTTPError

    api = HfApi(token=token)
    try:
        whoami = api.whoami()
    except HfHubHTTPError as exc:
        fail(
            f"HF_TOKEN was rejected by Hugging Face ({exc}). Create a new token with the "
            "'Write' role at huggingface.co/settings/tokens and update the HF_TOKEN secret."
        )
    else:
        print(f"Authenticated to Hugging Face as {whoami.get('name', '?')}")

    # The space may already exist (created manually via the web UI, which sidesteps an
    # account-level 402 some new accounts hit when creating Spaces via the API).
    try:
        # space_hardware is explicit: omitting it has been reported to make the API treat the
        # new Space as needing paid hardware (402 Payment Required) instead of defaulting to the
        # free CPU tier. cpu-basic is that free tier.
        api.create_repo(
            repo_id=space,
            repo_type="space",
            space_sdk="docker",
            space_hardware="cpu-basic",
            exist_ok=True,
        )
    except HfHubHTTPError as exc:
        fail(
            f"Could not create/access space {space!r}: {exc}. Check that HF_SPACE's username "
            "matches the account that owns HF_TOKEN, that the token has write access, and that "
            "the account has no pending payment-method requirement at "
            "https://huggingface.co/settings/billing."
        )

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
    except HfHubHTTPError as exc:
        fail(f"Upload to the space failed: {exc}")
    finally:
        readme.unlink(missing_ok=True)

    print(f"Deployed to https://huggingface.co/spaces/{space}")


if __name__ == "__main__":
    main()
