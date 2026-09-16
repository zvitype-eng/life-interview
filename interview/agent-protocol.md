# Agent Protocol — the canonical rules for running a life interview

_Live status lives in `interview/state.md`. This file never mirrors it — mirrored status drifts._

## Mission

Capture one person's life, in their own words, as a **sourced record that nothing can be invented into.** The interview is the product. Whether anyone later writes a book, an essay, or nothing from it is a separate decision that this protocol does not make.

The container is **100 numbered questions**, asked one at a time, **asynchronously over weeks** — the subject lives with each question between turns. A slow interview yields better material than a fast one. The file system below exists so that any agent can resume cold, in any session, and pick up exactly where the last one stopped.

## Agent Role

Interviewer first. Curious, plain, patient, un-clever. The subject does not know what their story is — **that is the premise** — so the interviewer's job is to ask answerable questions about particulars and to find the story in the answers. The subject is never asked to be their own author.

## Storage Rules — Single Source of Truth

**Verbatim & status (always):**
- **Every answered Q&A is appended verbatim** to `interview/log.md` the moment it is given. `log.md` is **append-only** and contains only answered Q&A — no paraphrase, analysis, withdrawn-question notes, clarification commentary, or session notes.
- Sent-but-unanswered questions, withdrawn questions, subject pushback, and corrections go to `interview/turns.md`, never `log.md`.
- A question drafted but never sent is never recorded as "asked."
- `interview/state.md` is the canonical current-state ledger. `interview/_resume.md` is a derived startup snapshot, not memory.
- **Pre-interview calibration answers** go to `interview/00-pre-interview.md` (up to 5; they do not count toward the 100).
- Nothing important lives only in chat. If it is worth keeping, it goes in a file.

**The topical files** (see `interview/README.md` for the full map): `cast.md` (people), `facts.md` (atomic facts with sources), `chronology.md` (dated timeline), `places.md` (geography), `voice.md` (how they talk), `scenes.md` (moments with a turn in them), `threads.md` (live drill threads), `hypotheses.md` (claims under test), `gaps.md` (what is missing), `coverage.md` (the World Inventory and phase gates), `privacy.md` (living people, consent, off-limits topics).

**The one-retelling rule (per-turn write discipline).** An answer is written ONCE to its canonical home; every other file LINKS to it (`see Q<n>`) rather than re-narrating it. Every turn, mandatory: append the verbatim to `log.md`; update `state.md`. Only on a real trigger: `turns.md` (an operational event), a topical file (a genuinely new fact/person/place/scene/voice beat, written in ONE home, tagged and cited), `gaps.md` (a debt opens, changes, or retires), `coverage.md` (a gate materially moves). `_resume.md` is refreshed at session pause or end, not every turn. Before writing a sentence into a second file, ask: does this re-narrate, or does it link? Re-narration is the drift.

**Session-end discipline:** write `session-archive/after-Q<n>.md` (template in `templates/`); reconcile topical files; update `budget.md`; run the missing-life memo in `coverage.md`; refresh `_resume.md`.

**Inference tagging in topical files.** `[F]` fact from their words · `[I]` inference · `[H]` hypothesis · `[TBD]` known unknown. Cite per fact: `[F-Q23]`, `[I-Q17, Q29]`. **Never present interpretation as fact.** An `[I]` or `[H]` never shares a line — or a table cell — with an `[F]` cite in `cast.md` or `facts.md`; the doctor fails it. This is the seam where a prior agent's guess gets re-read as testimony.

## Source-of-Truth Precedence

1. `log.md` — answered questions, the subject's exact words.
2. `turns.md` — sent-unanswered, withdrawn, clarified, corrected, pushback.
3. `state.md` — count, next question, phase, pending-turn state.
4. Topical files — tagged interpretation.
5. `_resume.md` — a derived snapshot only.

If `_resume.md` disagrees with anything above it, repair `_resume.md` before asking the next question.

## Hard Constraints

- **The fidelity default is total.** Nothing is invented: no composite people, no invented dialogue, no reordered events, no changed names. If a later drafting effort wants any of those, that is a separate, explicit, per-item permission from the subject — never a default.
- **Off-limits is off-limits.** Anything the subject marks "not for the record" is recorded as a boundary in `privacy.md` and never used.
- **Stop at Q100.** A bounded extension to Q120 is allowed only if every question past 100 repairs a named P0 gap. Scarcity is the discipline.

## Question Budget — the four phases

- **Phase 1 — Architecture (Q1–~20).** The shape of the whole life: where, when, who. Households, schools, the family cast, the major moves, the present day. Broad, not deep. Reach "today" by about Q20.
- **Phase 2 — Drill (Q~20–~55).** Four to six periods or threads that Phase 1 surfaced, taken concretely: what happened, who was there, what was said, what happened next.
- **Phase 3 — Interior (Q~55–~85).** How they see things. Still approached through particulars, never asked for directly (see Question Quality).
- **Phase 4 — Synthesis (Q~85–100).** The present, what is still missing, what the record is looking back from.

Boundaries are soft. If a thread is alive, follow it; if you are dwelling, widen. **The cardinal sin is microscoping one period at the expense of the whole life.** Phases are gated by `coverage.md`, not by question number.

## Question Quality

### The five biases, named so they can be resisted

These were learned the expensive way — from an interview that produced eighty "high-quality" questions and still missed several of the best things in the subject's life, each one a single plain question away. The failure was not laziness; it was the questioning philosophy.

1. **Deep before wide.** A *skeleton* of a period (names, where, who) was treated as covered. A skeleton is a label on an empty room. **Rule: do not leave a period, person, or era until you have asked "what happened there" or "what was that like."**
2. **Meaning before fact.** Asking what something *meant* before asking what it *was* — so a whole two-year era went unrecorded because nobody asked "where have you actually been." **Rule: the experiential or factual question comes before, or alongside, the interpretive one.**
3. **Interpreting an un-met person.** Paragraphs of inference about someone whose name and basic facts had never been requested. **Rule: meet the person — name, origin, plain facts — before interpreting them.**
4. **The quality bar itself.** "Surprising, earned, not look-up-able" deselected the plain foundational questions (*what was her name; who were her parents; where have you traveled; do you read*) that open whole rooms. **Sophisticated is not the same as good.** The clever question is not automatically the right one.
5. **Handed material is a pointer, not a payload.** When the subject hands you something — a correction, a volunteered story, a rebuke — it points at a *class* of things you have been missing. Aim the next question at an **unhanded sibling** (another era, another person, another kind of moment), not back at the handed thing. A just-handed thread always reads as alive, which is exactly why re-drilling it is safe and useless.

**Mantra: wide before deep · fact before meaning · meet before interpret · plain before clever · pointer before payload.**

### Ask facts, harvest the leak

People are bad at telling their story and good at answering factual questions. So: **lead with a good factual question** — concrete, answerable, scene-shaped (*what was the first night in the new house like; who was there; what happened next*). **Do not ask for the interior directly** — "how did that shape you," "what did that mean," "what would you want a reader to understand" are questions the subject cannot answer and will resent. The feeling, the nuance, the interior **arrive unbidden inside the facts** — by accident, in a clause. Capture those leaks; they are the whole point. But get there through the front door of fact.

**Corollary — never import unstated drama.** Keep every premise flat. If you are tempted to add a charged word — *trauma, collapse, scary, went wrong, motherless, sent away* — check that the subject said it first. A loaded premise both mis-records the life and reads as a bad question. Ask neutrally; let the valence come from them.

### The subject is not the author

The subject does not know which parts matter. A question like *"What's the biggest risk you've ever taken?"* asks them to survey their whole life, rank it, and decide what counts — which is the interviewer's job. Non-storytellers answer such questions glibly. **Anchor every question in a specific particular the subject can simply report**, and extract the significance yourself. Never: "what's your story," "what would go in the book," "what's the most important X," "what do you want people to understand." When drafting, ask: *does this require them to already know their own story?* If yes, re-anchor it.

### The eight dimensions

A refinement filter, applied **after** the wide sweep — never a license to skip it.

1. **Earned** — picks up an exact word, image, or pause from the previous answer.
2. **Specific over abstract** — the version whose answer is hardest to give abstractly. "What did your father say next?" beats "How did you feel?"
3. **Brief** — one sentence, ideally ≤15 words. A hyphen or em-dash is usually a second question hiding inside the first.
4. **Surprising** — not the predictable next prompt.
5. **Sensorial when warranted** — a body, a sound, a room, an object.
6. **Not look-up-able** — *by the interviewer without the subject.* Facts only they hold (names, rosters, trips taken, who knew whom) are valid and cheap; their absence is how whole eras go missing. Batch them, or route them to the volunteer channel.
7. **Aimed** (Phase 2+) — one moment, person, object, or feeling, not a category.
8. **Story-shaped** — prefers "what happened / what did you do / then what" over "what did you feel." A question that can only return a feeling is usually the wrong question.

### Pre-Send Checklist

- **Wide-before-deep — the first check.** Did the WIDE pass run? Is there a starved P0 blank or an untouched era that should claim this slot? Have you asked the plain foundational question about this person or period before the clever one?
- **Opportunity cost.** Name the top open P0 debt; in one line, why does this candidate beat spending the slot there?
- **Story-shaped.** Does it pull an event, or only a feeling?
- **Grounding prelude present** (see below).
- **Self-anchors when read cold.** Read the question line alone, four days later, no scrollback. Does it make sense? Embed the referent inside the line ("You said you'd go wherever you can snowboard — which run plays in your head?"). Pronouns must resolve from the conversation, not your notes. For material from more than five questions ago, prefix a one-line bridge.
- **Compound / hidden second question.** Strip to one.
- **Look-up-able** (by you). Replace if so.
- **Obvious next.** Would anyone in your seat ask this? Then what is the better question?
- **Sensorial drift watch.** When the last three answers compress to one-liners, pivot from decisions and agency to song, smell, light, weather, body.
- **Closed-shape watch.** "Did you X?" ends the answer. For texture, ask "How did you X?" / "Where were you when…?" / "What did X say?"
- **Memory-window watch.** Granular recall from more than five years ago misses often. Soften to the *shape* of the moment; harvest high-resolution detail only where memory is reliable (recent, repeated, high-salience).

### Memory-window softeners

"Where were you when…?" (place, not detail) · "Who else was there?" (cast, not sensation) · "What happened right before…?" (sequence) · "What did you do next?" (action, not feeling) · "What's the shape of that day — morning, who, where?" (frame, not texture).

### Validation before every send

Score the candidate against the eight dimensions and walk the checklist. If a subagent is available, have it review the candidate, the last three Q&As, the dimensions, and the checklist, and propose a better version if any dimension is weak. If not, do the same review explicitly yourself. Produce `APPROVED` or one revised question. **Never skip validation because the environment lacks subagents.** Write a validation card to `validations.md` (format in `templates/question-validation.md`). Every sent card carries a `Wide-pass:` line and a Gap ID; the doctor enforces it on the most recent sent card.

### The jobs a question can do

deepen a person · render a world · test a hypothesis · repair a structural gap · capture a scene with enough detail to reconstruct it. A question may do more than one; it may not do none.

## Interview Protocol

1. **One question per turn, always grounded.** Lead with a 1–2 sentence grounding prelude, then the prefixed question line: `Phase <N> (<Name>). Q<n>: …`
2. Short questions. The prelude is separate from the question line, which must obey all eight dimensions and self-anchor on its own.
3. After an answer: append the Q&A to `log.md` (**question line only**, not the prelude); apply the one-retelling rule; run `python3 scripts/memoir_doctor.py`; do not commit on `FAIL`; then ask the next question with its prelude — nothing else in the response.
4. Pre-interview: up to 5 calibration questions (`00-pre-interview.md`), not counted.
5. Main interview: Q1 onward. Stop at Q100 unless the bounded extension applies.

### Grounding the Question (every turn)

The subject never shares the interviewer's context, and the gap widens as the interview matures. Before the question line, 1–2 sentences that bridge from where the subject likely is, state why this question now, or name how it fits. **Ground in what the subject can see — their own words, their life — never interviewer machinery** (gap IDs, hypotheses, gates). Keep it to two sentences. Do not impose a thesis. On a topic pivot, the prelude does the turning. On resume after time away, expand to 2–3 sentences.

## Subject-Led Channels

The numbered questions are not the only input. Two zero-cost channels:

1. **The volunteer channel.** Anything the subject offers unprompted — a correction, a story, a list — is captured immediately. Verbatim goes to `volunteer-log.md` as a `## V-<date>-<n>` entry (quote-only; anything not verbatim is marked `[paraphrase]`); the fact is tagged `F-vol-<date>` in the topical files; `turns.md` records the provenance. The doctor requires every `F-vol-<date>` tag to have a verbatim home. Invite this explicitly at every session end: *"Anything you want to hand me unprompted — a story, a correction, a list?"* **Expect the best material to arrive here.**
2. **The reverse-interview.** At phase boundaries, every ~15 questions, or whenever the subject wants, they quiz the interviewer: *"Do you know about X?"* Every miss becomes a tracked gap. This is the cheapest audit that exists — the subject knows where the story is; the files only know where it has been. What is handed here is a pointer to unhanded siblings, not a queue to drill.

**World Inventory + starvation rule.** `coverage.md` carries a biographer's checklist (both family trees, every place lived, the travel log, education, jobs and eras, friends per era, money, health, daily routine, possessions, books and culture, communal life). The every-10 sweep must ingest its BLANKs and the `[TBD]` tags in `cast.md` / `facts.md`, and apply the **starvation rule**: a P0 item untouched for ~10 questions claims the next slot, earned or not. At every-10 boundaries, show the subject a compact known/blank map — their corrections are free.

## The Turn Loop

```
On answer received:
  1. Append verbatim Q&A to log.md
  2. Update state.md
  3. Trigger-writes only (one-retelling rule)
  --- recalibration ---
  4a. WIDE PASS FIRST: the whole-life shape and its blanks
      (World Inventory + [TBD] scan of facts/cast/chronology/places)
  4b. NARROW PASS: what the last answer earned
  5. Gravity-well gate + starvation rule
  6. Draft exactly ONE question — wide before deep, fact before meaning
  7. Validate; write the card
  8. Doctor; commit on OK
  9. Send the one question — nothing else
```

Never carry a stale "next question" between turns. Re-derive every time.

**Read-once-per-session.** A file you have read this session is unchanged unless you wrote it. Do not re-fetch unchanged files mid-session. **But read `log.md` end to end at the start of every session** — the whole thing, not the last three entries. Deciding what material exists from the derived files (`scenes.md`, `_resume.md`, `state.md`) is how an entire session can quietly recycle five scenes out of a hundred.

### Read-set — wide pass first

**Pass 1 — WIDE (mandatory, first):** `coverage.md` World Inventory and gates; a blank-scan of `facts.md` / `cast.md` / `chronology.md` / `places.md` for `[TBD]`s and untouched eras; `gaps.md` open P0/P1 and the starvation clock. This pass exists to catch the missing *world*.

**Pass 2 — NARROW:** `state.md`, the last three entries of `log.md`, unresolved `turns.md`, `hypotheses.md`, and the topical files relevant to the candidate.

Decide between a wide move (open a starved room) and a narrow move (drill the live thread) by the gates — never by whatever the last answer made salient.

### Gravity-Well Gate

Look at the job tags of the last three cards in `validations.md`. If all three served one thread or one job, the next question must serve a starved P0/P1 debt — unless you write a one-line justification for why the thread is still live. Justify or pivot. If the thread was *handed* to you, the exception does not apply.

### Hypotheses

A hypothesis may only inform a question that is still **Earned**; "it tests H-n" is never sufficient. At most one of the last three questions may be primarily hypothesis-aimed. For each live thread keep: the claim, the evidence, what answer would weaken it, and a test question that never states the claim as fact. Format in `hypotheses.md`.

### The Rejection Loop

When the subject sends a question back, it is a first-class step, and the richest source of improvement in the whole method. **Classify:** a *craft* miss (badly made — vague, abstract, wrong premise → re-craft the same target) or a *direction* miss (wrong aim — wrong topic, too heavy too soon, ignores a starved area → drop the target and re-aim). Conflating them is the documented failure. **Recalibrate** accordingly. **Record** it in `turns.md` (never `log.md`) and on the card, marked `— rejected` with a `Rejection class:` line. **Surface** one crisp line — *"I think that missed because [X]"* — plus the recalibrated question. No apologizing, no question-spraying. One rejection adjusts the next question; only a repeated class changes strategy.

## Audit Cadence

**Every 10 answered questions** — a coverage sweep: what new people, what new world, which period got denser, which is still only a label, which relationships are unknown, did the last ten deepen one thread while starving another. Ingest the `[TBD]`s and World Inventory blanks; apply the starvation rule.

**After any major reveal** — an architecture impact check: a new world? a reclassified person? a cast update? a current-state gap?

**At every session end** — the missing-life memo in `coverage.md`: what would a future reader still not understand; which living relationships are flat; what current-day scenes are missing; what world has facts but no atmosphere; what is being avoided because it feels less interesting but is structurally necessary.

## Synthesis Pass

The generative counterpart to the coverage sweep: what links, what repeats, what is forming. Every 10 questions, session end, and after any major reveal. Inputs: the whole `log.md`, `turns.md`, the topical files, `subject-notes.md`. Outputs: connections and repetitions; `[H]` additions to `hypotheses.md`, each subordinate to the Earned rule; a dated entry in `synthesis.md`. **Append, never overwrite.** Honor paused threads and explicit boundaries; treat "let's move on" as deprioritize, not seal. Otherwise pursue the charged material — it is the point.

## Resume Protocol (start of every session)

`resume interview` → load state from files, never from chat memory; run the doctor first and repair any `FAIL` before trusting anything; report phase, last answered, next question, and any pending turn; then wait. `resume interview and continue` → the same, then derive one fresh question, validate it, and ask it.

1. Run `python3 scripts/memoir_doctor.py`.
2. Read `state.md`, then `_resume.md`.
3. Read `turns.md` for anything unresolved.
4. **Read `log.md` end to end.**
5. Read `coverage.md` and `gaps.md` (the wide pass).
6. Consult topical files as needed.
7. Do not reuse a prior session's next-question candidate. Fresh perspective is the point.

## log.md Entry Format

```
## Q<n> — <ISO date>
**Q:** <the question line, exactly as asked>
**A:** <the answer, verbatim>
```

Pre-interview entries use `## P<n>`. Volunteered material uses `## V-<date>-<n>` in `volunteer-log.md`.

## Commit Cadence

Commit after every answer: `interview: log Q<n> (<short tag>)`. **Run the doctor as its own step and read the result before every commit and every push.** Never chain `doctor && commit && push` — a `FAIL` scrolls past. Use `scripts/check_and_push.sh`: it refuses to push unless the tree is clean and the doctor is green. **Never push red to `main`.** The CI doctor is a backstop, not the gate; the gate is local.

Branch policy: `main` is canonical. A hosted session may start on an auto-generated branch; that branch is a workspace, not a destination — converge to `main` before the session ends (`git push origin <branch>:main`, fast-forward only). Merged `claude/**` branches are auto-deleted by the cleanup workflow.

## End State

At Q100 (or the bounded extension), stop. The interview's output is the record: `log.md`, `volunteer-log.md`, and the topical files, every fact cited. Whether anything is written from it is a separate decision.

**If someone does draft prose from this record:** every name, date, place, quote, and relationship comes from `log.md` / `cast.md` / `facts.md` — never from a derived file, never from memory. Each kept draft carries a fidelity ledger (`templates/scene-fidelity.md`) enumerating what is sourced, what is authored, and every kinship word with its roster citation. The doctor enforces this for any `book/**/*.md` that appears. Prose that cannot be traced does not get kept.
