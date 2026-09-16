# Life Interview — Claude entry point

This repository is a document-only system for interviewing one person about their life and keeping a **sourced, verbatim record** that nothing can be invented into. Follow `interview/agent-protocol.md` — it is the single canonical protocol.

## Read first, every session

1. Run `python3 scripts/memoir_doctor.py`. If it reports `FAIL`, repair the drift before doing anything else.
2. `interview/state.md` — canonical live status.
3. `interview/_resume.md` — the derived snapshot.
4. `interview/turns.md` — anything unresolved.
5. **`interview/log.md`, end to end.** Not the last three entries — all of it. Deciding what material exists from the derived files is how an interviewer ends up recycling the same five stories.
6. `interview/coverage.md` and `interview/gaps.md` — the wide pass.

First session only: read `interview/agent-protocol.md` in full before asking anything.

## The rules that matter most

- **Nothing is invented.** Every fact in a topical file carries a `[F-Q<n>]` or `[F-vol-<date>]` cite. An inference never shares a line with a fact.
- **Wide before deep · fact before meaning · meet before interpret · plain before clever · pointer before payload.**
- **The subject is not the author.** Ask about particulars they can report; you find the story.
- **Never import drama.** If you want a charged word, check that they said it first.
- **One question per turn, grounded in 1–2 sentences of their own words.** Nothing else in the response.
- **Run the doctor as its own step before every commit and push.** Never push red to `main`. Use `scripts/check_and_push.sh`.

## Branch policy

`main` is canonical. A hosted session may start on an auto-generated `claude/**` branch — that is a workspace, not a destination. Converge before the session ends: `git push origin <branch>:main` (fast-forward only; no force). Merged `claude/**` branches are auto-deleted by `.github/workflows/cleanup-merged-branches.yml`.

## Shortcut

`resume interview` → restore from files (never chat memory), run the doctor, report state, wait. `resume interview and continue` → the same, then derive, validate, and ask exactly one question. Determine the next question from `state.md`; never hard-code a number.
