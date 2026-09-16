#!/usr/bin/env python3
"""Print a read-only pre-question context packet — WIDE pass before NARROW.

The WIDE pass (what is starved, across the whole life) is assembled first and
from real source: the computed coverage ledger, the open/partial gap rows, and
a [TBD] grep across the topical files. Only then comes the NARROW pass (the
live thread). This ordering is the corrective for the deep-over-wide diagnosis in agent-protocol.md
(deep-over-wide lost whole eras). The packet HARD-ERRORS if the derived ledger
is missing — there is no silent "nothing starved" fallback (audit A2-F2).
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List

try:  # `from scripts import question_packet` (tests, repo root on path)
    from scripts import coverage_ledger
except ImportError:  # `python3 scripts/question_packet.py` (scripts/ on path)
    import coverage_ledger

TOPICAL_FILES = ["facts.md", "cast.md", "chronology.md", "places.md"]


@dataclass
class QAEntry:
    number: int
    body: str


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def extract_last_qas(log_text: str, count: int = 5) -> List[QAEntry]:
    matches = list(re.finditer(r"^## Q(\d+)\b.*$", log_text, flags=re.MULTILINE))
    entries: List[QAEntry] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(log_text)
        entries.append(QAEntry(number=int(match.group(1)), body=log_text[start:end].strip()))
    return entries[-count:]


def load_state(root: Path) -> str:
    return read_text(root / "interview/state.md").strip()


def extract_pending_turns(turns_text: str) -> str:
    matches = list(re.finditer(r"^## \d{4}-\d{2}-\d{2} — Q\d+.*$", turns_text, flags=re.MULTILINE))
    sections = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(turns_text)
        sections.append(turns_text[start:end])
    relevant = [
        section.strip()
        for section in sections
        if "provenance ambiguity" in section.lower()
        or "sent-but-unanswered" in section.lower()
        or "do not reuse" in section.lower()
    ]
    if not relevant:
        return "No unresolved pending-turn warning found."
    return "\n\n".join(relevant[-3:])


def load_ledger(root: Path) -> str:
    """Load the derived coverage ledger. HARD-ERROR if absent — the WIDE pass
    must not silently proceed without computed starvation data (A2-F2)."""
    path = root / "interview" / "derived" / "coverage-ledger.md"
    if not path.is_file():
        raise FileNotFoundError(
            "WIDE pass cannot run: the coverage ledger is missing "
            "(interview/derived/coverage-ledger.md). Run "
            "`python3 scripts/coverage_ledger.py --write` (or the doctor) first."
        )
    return read_text(path).strip()


def extract_open_gaps(root: Path) -> str:
    path = root / "interview" / "gaps.md"
    if not path.is_file():
        return "No gaps.md found."
    rows = coverage_ledger.parse_gaps(read_text(path))
    active = [r for r in rows if r["status_word"] in coverage_ledger.ACTIVE_STATUSES]
    if not active:
        return "No open/partial gaps."
    lines = [
        f"- {r['id']} ({r['priority']}, {r['type']}, {r['status_word']}): {r['repair'][:100]}"
        for r in active
    ]
    return "\n".join(lines)


def extract_tbd(root: Path) -> str:
    hits = []
    for name in TOPICAL_FILES:
        path = root / "interview" / name
        if not path.is_file():
            continue
        for lineno, line in enumerate(read_text(path).splitlines(), start=1):
            if "[TBD]" in line:
                hits.append(f"{name}:{lineno}: {line.strip()[:100]}")
    return "\n".join(hits) if hits else "No [TBD] markers found."


def extract_last_cards(root: Path, count: int = 5) -> str:
    path = root / "interview" / "validations.md"
    if not path.is_file():
        return "No validations.md found."
    text = read_text(path)
    headings = list(re.finditer(r"^## Q\d+.*$", text, flags=re.MULTILINE))
    boundary = re.compile(r"^#{1,2} ", flags=re.MULTILINE)
    blocks = []
    for match in headings:
        start = match.start()
        nb = boundary.search(text, match.end())
        end = nb.start() if nb else len(text)
        block = text[start:end]
        kept = [
            line
            for line in block.splitlines()
            if line.startswith("## Q")
            or re.match(r"\s*(Job tag|Coverage debt served|Gravity-well)", line)
        ]
        blocks.append("\n".join(kept).strip())
    if not blocks:
        return "No validation cards."
    return "\n\n".join(blocks[-count:])


def extract_rejection_profile(turns_text: str) -> str:
    """E2: summarize logged rejection classes into a per-subject taste profile.
    A class recurring >=2 times is flagged for promotion to a standing rule
    (e.g. Q71+Q77 -> 'abstract marriage questions abandoned')."""
    classes = [m.lower() for m in re.findall(r"Rejection class:\s*(\w+)", turns_text, re.IGNORECASE)]
    if not classes:
        return "No classified rejections logged yet (none)."
    counts: dict = {}
    for cls in classes:
        counts[cls] = counts.get(cls, 0) + 1
    lines = [f"- {cls}: {n}" for cls, n in sorted(counts.items(), key=lambda kv: -kv[1])]
    recurring = [cls for cls, n in counts.items() if n >= 2]
    if recurring:
        lines.append(
            "- recurring (>=2 -> promote to a standing rule): " + ", ".join(sorted(recurring))
        )
    return "\n".join(lines)


def parse_question_number(question_label: str) -> int:
    match = re.search(r"Q?(\d+)", question_label)
    if not match:
        raise ValueError(f"Could not parse question label: {question_label}")
    return int(match.group(1))


def extract_lane(remaining_plan_text: str, question_label: str) -> str:
    question_number = parse_question_number(question_label)
    for line in remaining_plan_text.splitlines():
        match = re.search(r"\|\s*Q(\d+)-Q(\d+)\s*\|", line)
        if not match:
            continue
        start, end = int(match.group(1)), int(match.group(2))
        if start <= question_number <= end:
            return line
    return "No remaining-plan lane found for this question."


def build_packet(root: Path, question_label: str) -> str:
    interview = root / "interview"
    ledger = load_ledger(root)  # hard-errors if missing
    open_gaps = extract_open_gaps(root)
    tbd = extract_tbd(root)
    state = load_state(root)
    turns_text = read_text(interview / "turns.md")
    turns = extract_pending_turns(turns_text)
    rejection_profile = extract_rejection_profile(turns_text)
    last_qas = extract_last_qas(read_text(interview / "log.md"), count=5)
    last_cards = extract_last_cards(root, count=5)
    lane = extract_lane(read_text(interview / "remaining-plan.md"), question_label)

    parts = [
        f"# Pre-Question Packet — {question_label}",
        "## WIDE PASS — what is starved (read first)",
        "### Coverage / Starvation Ledger",
        ledger,
        "### Open / partial gaps (full list)",
        open_gaps,
        "### [TBD] markers across topical files (untagged holes)",
        tbd,
        "## NARROW PASS — the live thread",
        "### Canonical State",
        state,
        "### Pending Turn Warning",
        turns,
        "### Last 5 Answered Q&A",
        "\n\n".join(entry.body for entry in last_qas),
        "### Last 5 Validation Cards (gravity-well gate)",
        last_cards,
        "### Rejection profile (taste — avoid repeating a recurring miss)",
        rejection_profile,
        "## Sensitivity",
        "Nothing is off-limits (subject said so at pre-interview). Pursue charged material — with care, not avoidance. Be sensitive in phrasing on heavy material; never steer away from it.",
        "## Remaining-Plan Lane",
        lane,
        "## Validation Checklist",
        "- Candidate self-anchors when read cold.",
        "- Every referent has a source quote.",
        "- Wide-pass recorded: top-starved P0 + any BLANK domain considered.",
        "- Heavy material handled with care, not avoided.",
        "- Book-capability job named.",
        "- Coverage/gap job named.",
        "- Seven question-quality dimensions scored.",
        "- Candidate approved or revised before sending.",
    ]
    return "\n\n".join(parts)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question", nargs="?", default="Q87", help="Question label, e.g. Q87")
    parser.add_argument("--root", default=".", help="Repository root")
    args = parser.parse_args(argv)

    print(build_packet(Path(args.root).resolve(), args.question))
    return 0


if __name__ == "__main__":
    sys.exit(main())
