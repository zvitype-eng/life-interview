# Interview Files — the map

Precedence when files disagree: `log.md` → `turns.md` → `state.md` → topical files → `_resume.md`.

## Core

| File | Role | Update |
|---|---|---|
| `agent-protocol.md` | The canonical rules. Read fully, once. | when the method changes |
| `ops.md` | Portable pointer index into the protocol | rarely |
| `log.md` | Verbatim answered Q&A | after every answer |
| `volunteer-log.md` | Verbatim volunteered material (`V-<date>-<n>`) | when the subject volunteers |
| `turns.md` | Operational events (sent-unanswered, withdrawn, pushback, corrections) | on an event |
| `state.md` | Live status — the only canonical status | after every answer |
| `_resume.md` | Derived startup snapshot | session pause/end |
| `00-pre-interview.md` | Calibration questions (not counted) | once |
| `subject-notes.md` | The subject's between-session inbox | when they add |
| `validations.md` | One card per drafted question | per question |

## Governance

| File | Role | Update |
|---|---|---|
| `coverage.md` | Phase gates, World Inventory, coverage debts, missing-life memo | every 10 / session end |
| `gaps.md` | Normalized queue of open gaps | when a gap opens/changes/closes |
| `privacy.md` | Living people, off-limits topics, consent, the publication gate | when a boundary is stated |
| `hypotheses.md` | Claims under test | recalibration / synthesis |
| `synthesis.md` | Synthesis Pass log | every 10 / session end |
| `budget.md` | Slot accounting | session end |
| `remaining-plan.md` | Lane map for the remaining budget | phase boundaries |
| `form-readiness.md` | If ever written up: which forms the material supports | every 10 / session end |
| `derived/coverage-ledger.md` | **Computed** starvation ledger — do not hand-edit; regenerate with `scripts/coverage_ledger.py --write` | after editing gaps/validations/coverage |

## Topical

| File | Role |
|---|---|
| `facts.md` | Atomic facts with sources |
| `cast.md` | People, and the household rosters that license kinship words |
| `chronology.md` | Dated timeline |
| `places.md` | Geography |
| `voice.md` | How they talk |
| `scenes.md` | Moments with a turn in them |
| `threads.md` | Live drill threads |

## Templates and archive

`templates/` — the validation card, scene readiness, session archive, turn event, scene fidelity ledger. `session-archive/` — one synthesis per session (`after-Q<n>.md`).
