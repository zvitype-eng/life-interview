# Validation Cards

One card per drafted question (sent or rejected). Append-only. The gravity-well gate reads each card's job tag; the doctor checks the most recent sent card for a `Wide-pass:` line and a Gap ID, and every rejected card for a `Rejection class:` line.

## Card format

```
## Q<n> — <ISO date> — <sent | rejected>
Candidate: <question line text>
Grounding prelude: <1–2 sentences; the subject's words, no interviewer machinery>
Job tag: <deepen-person | render-world | test-hypothesis | repair-gap | capture-scene>
Wide-pass: top-starved P0 <Gnnn> + BLANK domain(s) considered <…>; why this beats spending the slot there
Coverage debt served: <Gap ID, or "none" + one-line justification>
Referents + sources: <each referent -> the Q it comes from>
Verdict: <APPROVED | revised | rejected> + one-line note
```

Full template: `templates/question-validation.md`.

---
