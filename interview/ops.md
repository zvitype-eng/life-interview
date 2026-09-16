# Operations Index

A thin, portable index into `agent-protocol.md` for any agent (Claude, Codex, or another) working in this repo. Every rule lives once, in the protocol; entries here are pointers.

- **Branch policy** → `CLAUDE.md` → Branch Policy; `agent-protocol.md` → Commit Cadence.
- **Source-of-truth precedence** → `agent-protocol.md` → Source-of-Truth Precedence.
- **Raw log discipline** → Storage Rules.
- **The one-retelling rule** → Storage Rules → per-turn write discipline.
- **The five biases / the mantra** → Question Quality.
- **Ask facts, harvest the leak; the subject is not the author** → Question Quality.
- **Grounding prelude** → Grounding the Question.
- **Subject-led channels; World Inventory; starvation rule** → Subject-Led Channels.
- **The turn loop; wide-before-narrow read-set; gravity-well gate** → The Turn Loop.
- **Rejection loop** → The Rejection Loop.
- **Resume** → Resume Protocol.

## Validation Commands

```sh
python3 scripts/memoir_doctor.py                 # the gate — run as its own step, read the result
python3 scripts/coverage_ledger.py --write       # regenerate the derived ledger after editing gaps/validations/coverage
python3 scripts/question_packet.py Q<n>          # the WIDE-before-NARROW context packet for the next question
python3 -m unittest discover -s tests -v         # the doctor's own regression suite
scripts/check_and_push.sh                        # validate-before-push: clean tree + doctor OK, then push and fast-forward main
```
