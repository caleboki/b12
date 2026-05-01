# B12 Application Submission

This repository contains a Python script and GitHub Actions workflow that programmatically submits a job application to B12's API endpoint.

## What's inside

- `submit.py` — Submits a canonicalized, HMAC-signed JSON payload to `https://b12.io/apply/submission`
- `.github/workflows/submit.yml` — Manually triggered GitHub Action that runs the submission script

## How it works

1. **Payload construction** — Builds a JSON object with alphabetically sorted keys and compact separators (`:,`), ensuring a deterministic canonical form.
2. **Timestamp** — Generates an ISO 8601 UTC timestamp with millisecond precision.
3. **HMAC-SHA256 signature** — Computes a hex digest of the canonical JSON body using a shared signing secret, then attaches it as `X-Signature-256: sha256={hex}`.
4. **CI link derivation** — When running in GitHub Actions, the repository and action-run links are derived automatically from the environment (no hardcoded URLs).
5. **Submission** — POSTs the payload and returns the receipt from the response.

## Running locally

```bash
python submit.py --dry-run \
  --repository-link "https://github.com/caleboki/b12" \
  --action-run-link "https://github.com/caleboki/b12/actions/runs/123456789"
```

## Tech stack

- Python 3.12
- `urllib` (stdlib)
- GitHub Actions
