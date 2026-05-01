#!/usr/bin/env python3
"""B12 application submission script.

Posts a canonicalized JSON payload to https://b12.io/apply/submission
with an HMAC-SHA256 signature header.
"""

import argparse
import hashlib
import hmac
import json
import os
import sys
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError

# Configuration
SIGNING_SECRET = b"hello-there-from-b12"
SUBMISSION_URL = "https://b12.io/apply/submission"


def get_iso_timestamp() -> str:
    """Return current UTC time in ISO 8601 format with milliseconds."""
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"


def build_payload(name: str, email: str, resume_link: str, repository_link: str, action_run_link: str) -> dict:
    """Build the submission payload."""
    return {
        "action_run_link": action_run_link,
        "email": email,
        "name": name,
        "repository_link": repository_link,
        "resume_link": resume_link,
        "timestamp": get_iso_timestamp(),
    }


def canonicalize_json(payload: dict) -> bytes:
    """Return compact, UTF-8 encoded JSON with alphabetically sorted keys."""
    return json.dumps(payload, separators=(",", ":"), sort_keys=True, ensure_ascii=False).encode("utf-8")


def compute_signature(body: bytes) -> str:
    """Compute HMAC-SHA256 hex digest of the body using the signing secret."""
    return hmac.new(SIGNING_SECRET, body, hashlib.sha256).hexdigest()


def submit(payload: dict) -> str:
    """POST the payload to B12 and return the receipt."""
    body = canonicalize_json(payload)
    signature = compute_signature(body)

    req = Request(
        SUBMISSION_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-Signature-256": f"sha256={signature}",
        },
        method="POST",
    )

    try:
        with urlopen(req) as resp:
            response_body = resp.read().decode("utf-8")
    except HTTPError as e:
        error_body = e.read().decode("utf-8")
        print(f"HTTP Error {e.code}: {error_body}", file=sys.stderr)
        raise

    data = json.loads(response_body)
    if not data.get("success"):
        raise RuntimeError(f"Submission failed: {response_body}")

    return data["receipt"]


def main():
    parser = argparse.ArgumentParser(description="Submit B12 application")
    parser.add_argument("--name", default=os.getenv("B12_NAME", "Caleb Oki"))
    parser.add_argument("--email", default=os.getenv("B12_EMAIL", "caleboki@gmail.com"))
    parser.add_argument("--resume-link", default=os.getenv("B12_RESUME_LINK", "https://docs.google.com/document/d/1WA294l2IZAHUvKcOk11OENFTgN40Lmi4/edit?usp=sharing"))
    parser.add_argument("--repository-link", default=os.getenv("B12_REPOSITORY_LINK"))
    parser.add_argument("--action-run-link", default=os.getenv("B12_ACTION_RUN_LINK"))
    parser.add_argument("--dry-run", action="store_true", help="Print payload and signature without sending")
    args = parser.parse_args()

    # Derive CI links from GitHub Actions environment variables if available
    server_url = os.getenv("GITHUB_SERVER_URL", "https://github.com")
    repository = os.getenv("GITHUB_REPOSITORY")
    run_id = os.getenv("GITHUB_RUN_ID")

    repository_link = args.repository_link
    if repository_link is None and repository:
        repository_link = f"{server_url}/{repository}"

    action_run_link = args.action_run_link
    if action_run_link is None and repository and run_id:
        action_run_link = f"{server_url}/{repository}/actions/runs/{run_id}"

    if repository_link is None:
        print("Error: --repository-link or GITHUB_REPOSITORY env var is required", file=sys.stderr)
        sys.exit(1)

    if action_run_link is None:
        print("Error: --action-run-link or GITHUB_RUN_ID env var is required", file=sys.stderr)
        sys.exit(1)

    payload = build_payload(
        name=args.name,
        email=args.email,
        resume_link=args.resume_link,
        repository_link=repository_link,
        action_run_link=action_run_link,
    )

    body = canonicalize_json(payload)
    signature = compute_signature(body)

    print(f"Payload: {body.decode('utf-8')}")
    print(f"Signature: sha256={signature}")

    if args.dry_run:
        print("Dry run - not submitting")
        sys.exit(0)

    receipt = submit(payload)
    print(f"Receipt: {receipt}")


if __name__ == "__main__":
    main()
