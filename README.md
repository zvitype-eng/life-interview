# Life Interview

A system for interviewing one person about their life — over weeks, one question at a time — and keeping a record of it that **nothing can be invented into.**

## Use it

```
git clone <this repo> my-fathers-life
cd my-fathers-life
claude            # or codex, or any agent that reads CLAUDE.md / AGENTS.md
> start interview
```

The agent asks a few calibration questions, then Q1. Every answer is stored verbatim. Every fact it extracts is cited back to the question it came from. A validator refuses to commit anything that breaks that chain.

Run it in a **private** repository. It will hold raw, private material about real people.

## What it does

- **Asks one question at a time**, grounded in what the subject already said, over as many sessions as it takes. The subject lives with each question between turns.
- **Keeps the verbatim** in `interview/log.md`, append-only. Anything the subject volunteers outside the questions goes in `interview/volunteer-log.md`, also verbatim.
- **Builds a cited record** — people, facts, places, timeline, scenes, voice — where every line points back to a `Q<n>`.
- **Refuses to invent.** `scripts/memoir_doctor.py` fails any commit where a cited question doesn't exist, an inference shares a line with a fact, a family relationship isn't on the roster, or a volunteered fact has no verbatim home. Sixty-plus tests pin the validator. CI runs it on every push.
- **Tracks what's missing.** A World Inventory and a starvation rule make sure an untouched era claims a slot before the interview drills its favorite thread any further.
- **Lets the subject drive.** A volunteer channel and a reverse-interview ("do you know about X?") — because the subject knows where the story is, and the files only know where it has been.

## What it doesn't do

It does not write the book. The output is the record. Writing from it is a separate decision, and if you make it, the fidelity ledger in `interview/templates/scene-fidelity.md` keeps that honest too.

## Where the method came from

Every rule in `interview/agent-protocol.md` was learned from a real 115-question interview: which questions produced facts and which produced stories, which biases lost whole eras of a life, why the best material arrived unprompted, and how an AI interviewer confabulates unless a validator stops it. The protocol is the distilled version. Read it once; it is the product.

## Layout

```
CLAUDE.md, AGENTS.md          agent entry points
interview/agent-protocol.md   the rules (read once, fully)
interview/log.md              verbatim Q&A — the record of record
interview/volunteer-log.md    verbatim volunteered material
interview/state.md            live status
interview/{cast,facts,chronology,places,voice,scenes,threads}.md   the cited record
interview/{coverage,gaps,privacy,hypotheses,...}.md                governance
scripts/memoir_doctor.py      the validator
scripts/check_and_push.sh     validate-before-push
tests/                        the validator's regression suite
```

## License

MIT.
