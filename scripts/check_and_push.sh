#!/usr/bin/env bash
# Validate-before-push gate — the "never push red to main" rule.
# (See interview/agent-protocol.md -> "Commit Cadence".)
#
# Runs memoir_doctor against the COMMITTED snapshot and pushes the current
# branch + fast-forwards main ONLY if the doctor reports OK. This is what
# stops the "memoir-doctor: All jobs have failed" emails: a red state can
# never reach main, because the push is gated locally first.
#
# Usage: commit your work, then:  scripts/check_and_push.sh
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

# 1. Validated state must equal pushed state: refuse if the tree isn't clean.
#    `git status --porcelain` covers staged, unstaged, AND untracked files —
#    `git diff` alone never sees untracked files, so a forgotten `git add` of a
#    brand-new required file could pass the doctor locally (which reads the
#    working tree) while the pushed commit lacked the file → red CI on main
#    Untracked-but-ignored files stay exempt.
if [ -n "$(git status --porcelain)" ]; then
  echo "==> Working tree not clean (uncommitted or untracked files present)." >&2
  echo "    Commit (or ignore) everything first, so the doctor validates" >&2
  echo "    exactly the snapshot you push:" >&2
  git status --porcelain >&2
  exit 1
fi

# 2. Gate on the doctor. Its output is shown; a FAIL aborts before any push.
echo "==> Running memoir_doctor (gate)..."
if ! python3 scripts/memoir_doctor.py; then
  echo "" >&2
  echo "==> memoir_doctor FAILED — refusing to push. Fix the drift, commit, re-run." >&2
  exit 1
fi

# 3. Doctor is OK -> push the session branch and fast-forward main.
branch="$(git rev-parse --abbrev-ref HEAD)"
echo "==> Doctor OK. Pushing '$branch' and fast-forwarding main..."
git push -u origin "$branch"
git push origin "$branch:main"
echo "==> Done. main advanced to a doctor-green commit."
