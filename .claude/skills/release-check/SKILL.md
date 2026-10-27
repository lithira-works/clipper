---
name: release-check
description: Pre-merge / pre-release checklist for Clipper - lint, tests, type checks, builds, docs sync, changelog, security and version bump. Use before opening a PR, merging to main, or tagging a release.
---

# Release check

Run the steps in order. Stop and report at the first failure, and include the exact error output.

1. **Static checks and tests**
   ```bash
   cd apps/api && uv run ruff check app tests && uv run ruff format --check app tests && uv run pytest -q
   cd apps/web && npm run typecheck && npm run build
   ```
2. **Contract sync.** Diff `apps/api/app/schemas.py` against `apps/web/src/lib/types.ts`, and
   `apps/api/app/edl.py` against `apps/web/src/lib/edl.ts` (once they exist). Every field and enum
   value must match. If the EDL changed in a breaking way, `version` must be bumped.
3. **Docs sync**
   - New or changed endpoints appear in `docs/API.md`.
   - Pipeline changes appear in `docs/ARCHITECTURE.md`.
   - Scoring changes appear in `docs/VIRAL_SCORING.md`.
   - New env vars appear in `.env.example` and `docs/DEPLOYMENT.md`.
   - Status markers (✅/🔨/🗺️) in `docs/ARCHITECTURE.md` match reality, and finished tickets are ticked in `TODO.md`.
   - Significant decisions have an ADR in `docs/adr/`.
   - Prompt, weight or model changes include an `eval-moments` comparison in the PR.
4. **Security**
   - No secrets in the diff (`git diff | grep -iE "sk-ant|api_key\s*="`).
   - URL validation is still YouTube-only.
   - Caption text still goes through `captions._clean`.
   - Containers still run as non-root.
   - `secrets/` and `.env` are not staged.
5. **Docker**: run `docker compose build`. For releases, also run one real job end to end.
6. **Changelog and TODO**
   - Move `[Unreleased]` entries in `CHANGELOG.md` under a new version with today's date.
   - Tick the finished items in `TODO.md`.
7. **Version.** Bump it in all three places, which must match:
   - `apps/api/pyproject.toml`
   - `apps/api/app/__init__.py`
   - `apps/web/package.json`

Report the result as a short checklist with pass or fail for each step.
