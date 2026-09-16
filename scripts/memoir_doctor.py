#!/usr/bin/env python3
"""Read-only consistency checks for the memoir interview repository.

Single source of truth: interview/log.md (answered Q&A) + interview/turns.md.
Everything else is derived and must agree with the log. This validator is run
as a protocol step before each commit and on resume; a CI job runs it on push
to main as a version-controlled backstop (local git hooks are not installed in
fresh or hosted clones).
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Pattern

try:  # `from scripts import memoir_doctor` (tests, repo root on path)
    from scripts import coverage_ledger
except ImportError:  # `python3 scripts/memoir_doctor.py` (scripts/ on path)
    import coverage_ledger


REQUIRED_FILES = [
    "AGENTS.md",
    "CLAUDE.md",
    "interview/agent-protocol.md",
    "interview/ops.md",
    "interview/state.md",
    "interview/_resume.md",
    "interview/log.md",
    "interview/volunteer-log.md",
    "interview/turns.md",
    "interview/coverage.md",
    "interview/form-readiness.md",
    "interview/gaps.md",
    "interview/privacy.md",
    "interview/remaining-plan.md",
    "interview/README.md",
    "interview/hypotheses.md",
    "interview/validations.md",
    "interview/synthesis.md",
    "interview/subject-notes.md",
]

# A pending-claim phrase: a Q asserted still-open ("in flight / asked / sent /
# unanswered"). In a canonical CURRENT-STATE ledger this is stale drift the
# moment that Q is answered (a real drift incident). Scoped to
# state.md / _resume.md only: append-only event logs (turns.md, budget.md) and
# point-in-time session-archive snapshots legitimately preserve these phrases as
# dated history, so scanning them would false-positive on correct records.
STALE_PENDING = re.compile(r"Q(\d+)[ \t]+(in flight|asked|sent|unanswered)", re.IGNORECASE)
STALE_SCAN_FILES = ["interview/state.md", "interview/_resume.md"]

LOG_OPERATIONAL_MARKERS: List[Pattern[str]] = [
    re.compile(pattern, flags=re.IGNORECASE)
    for pattern in [
        r"\*\*Disposition:\*\*",
        r"\*\*Withdrawn(?: / declined)?:\*\*",
        r"\*\*Clarified:\*\*",
        r"\buser pushback\b",
        r"\bprovenance ambiguity\b",
        r"\bNote:",
        r"\bwithdrawn\b",
        r"\bsoft-close\b",
        r"\bpivoting\b",
        r"\bclarified\b",
    ]
]

# Files that carry inference-tagged citations like [F-Q23], [I-Q17, Q29],
# [H-Q67]. log.md and turns.md are excluded: they legitimately reference
# unanswered/next questions that are not yet in the answered set.
CITATION_FILES = [
    "cast.md",
    "voice.md",
    "scenes.md",
    "threads.md",
    "coverage.md",
    "form-readiness.md",
    "facts.md",
    "chronology.md",
    "places.md",
    "gaps.md",
    "remaining-plan.md",
    "_resume.md",
    "hypotheses.md",
    "validations.md",
    "synthesis.md",
    "budget.md",
    "phase3-plan.md",
    "subject-notes.md",
]

# A bracketed inference tag: opens with F/I/H, then any non-] content.
INFERENCE_TAG = re.compile(r"\[(?:F|I|H)[^\]]*\]")
QNUM = re.compile(r"Q(\d+)")
# Bare volunteer-citation form (no brackets): F-vol-YYYY-MM-DD. Invisible to
# INFERENCE_TAG, so it is validated separately by date (A4 / A1-F1).
FVOL_TAG = re.compile(r"F-vol-(\d{4}-\d{2}-\d{2})")
# ISO date on a log Q-heading, e.g. "## Q12 — 2026-01-15".
LOG_DATE = re.compile(r"^## Q\d+\b[^\n]*?(\d{4}-\d{2}-\d{2})", re.MULTILINE)
# A log line carrying an operational LABEL (not verbatim answer prose). Only
# these lines are scanned for operational markers, so marker words inside a
# subject's verbatim answer body are not false-positives (A5 / A5-F4).
# Label-line prefixes scanned for operational markers. Widened in a later
# audit: pushback/provenance/correction label lines are real event types
# per turns.md, but the old 4-prefix list made those marker patterns
# unreachable — a `**Provenance ambiguity:** …` line in log.md passed clean.
# Answer bodies (**A:** …) still never match, so verbatim text stays exempt.
OPERATIONAL_LINE = re.compile(
    r"^\s*(?:\*\*)?(?:disposition|withdrawn|clarified|note|pushback|provenance|correction)\b",
    re.IGNORECASE,
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def safe_read(path: Path, issues: List[str]) -> Optional[str]:
    """Read a file, recording a structured issue instead of crashing (A3)."""
    try:
        return read_text(path)
    except (OSError, UnicodeDecodeError) as exc:
        issues.append(f"Cannot read {path}: {exc}")
        return None


def parse_log_dates(text: str) -> List[str]:
    return LOG_DATE.findall(text)


def parse_log_questions(text: str) -> List[int]:
    return [int(match) for match in re.findall(r"^## Q(\d+)\b", text, flags=re.MULTILINE)]


def parse_state_table(text: str) -> Dict[str, str]:
    fields: Dict[str, str] = {}
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        parts = [part.strip() for part in line.strip().strip("|").split("|")]
        if len(parts) != 2 or parts[0] in {"Field", "---"}:
            continue
        fields[parts[0]] = parts[1]
    return fields


def check_required_files(root: Path) -> List[str]:
    issues = []
    for relative in REQUIRED_FILES:
        if not (root / relative).is_file():
            issues.append(f"Missing required file: {relative}")
    return issues


def check_log_sequence(log_text: str) -> List[str]:
    issues = []
    numbers = parse_log_questions(log_text)
    if not numbers:
        return ["No answered Q headings found in interview/log.md"]

    seen = set()
    for number in numbers:
        if number in seen:
            issues.append(f"Duplicate question number: Q{number}")
        seen.add(number)

    expected = list(range(1, max(numbers) + 1))
    if numbers != expected:
        issues.append(f"Question headings are not sequential Q1-Q{max(numbers)}: found {numbers}")
    return issues


# Phase gate: once an interview is CLOSED, interview-
# turn machinery (next-question fiction, wide-pass card gate) must not stay a
# live obligation of every drafting session. The doctor reads the closed flag
# from state.md's own "Interview status" row — state.md stays the single
# canonical phase source.
INTERVIEW_CLOSED_ROW = re.compile(r"Interview status\s*\|[^\n]*\bCLOSED\b", re.IGNORECASE)
CLOSED_NEXT_Q = re.compile(r"^(?:—|-|none\b.*|n/a)$", re.IGNORECASE)


def interview_closed(state_text: str) -> bool:
    return bool(INTERVIEW_CLOSED_ROW.search(state_text))


def check_state_matches_log(state_text: str, log_text: str) -> List[str]:
    issues = []
    state = parse_state_table(state_text)
    questions = parse_log_questions(log_text)
    if not questions:
        return ["Cannot compare state to log: no Q headings found"]

    last = max(questions)
    closed = interview_closed(state_text)
    expected = {
        "Last answered question": f"Q{last}",
        "Questions answered": str(last),
        "Next question": f"Q{last + 1}",
    }
    for key, value in expected.items():
        actual = state.get(key)
        if key == "Next question" and closed and actual is not None:
            # Post-close, the would-be-next-number fiction is no longer
            # required: a closed marker is the honest value.
            if CLOSED_NEXT_Q.match(actual.strip()) or actual == value:
                continue
            issues.append(
                f"state.md Next question: interview is CLOSED — expected a closed "
                f"marker ('—', 'none…') or {value!r}, has {actual!r}"
            )
            continue
        if actual != value:
            issues.append(f"state.md {key} mismatch: has {actual!r}, expected {value!r}")
    return issues


def check_resume_matches_log(resume_text: str, log_text: str) -> List[str]:
    """_resume.md has drifted before; enforce its status figures."""
    issues = []
    questions = parse_log_questions(log_text)
    if not questions:
        return []
    last = max(questions)

    answered = re.search(r"Questions answered\s*\|\s*(\d+)", resume_text)
    if not answered:
        issues.append("_resume.md missing parseable 'Questions answered' field")
    elif int(answered.group(1)) != last:
        issues.append(
            f"_resume.md 'Questions answered' is {answered.group(1)}, expected {last}"
        )

    last_answered = re.search(r"Last answered\s*\|\s*Q?(\d+)", resume_text)
    if not last_answered:
        issues.append("_resume.md missing parseable 'Last answered' field")
    elif int(last_answered.group(1)) != last:
        issues.append(
            f"_resume.md 'Last answered' is Q{last_answered.group(1)}, expected Q{last}"
        )
    return issues


def check_citations(root: Path, log_text: str) -> List[str]:
    """Every [F/I/H-Qn] citation must resolve to an answered question in log.md;
    every bare F-vol-DATE citation must carry a real date no later than the
    latest log date (A4)."""
    issues: List[str] = []
    numbers = parse_log_questions(log_text)
    if not numbers:
        return []
    valid = set(numbers)
    last = max(numbers)
    # F-vol material is volunteered BETWEEN numbered questions, so a volunteer
    # date can legitimately be later than the last logged Q. Validate against
    # the latest date the verbatim record knows about (log.md Q-dates +
    # volunteer-log.md V-entry dates), which still catches a garbage/future typo.
    dates = list(parse_log_dates(log_text))
    vlog = root / "interview" / "volunteer-log.md"
    if vlog.is_file():
        vtext = safe_read(vlog, [])
        if vtext:
            dates.extend(VOLUNTEER_ENTRY.findall(vtext))
    max_date = max(dates) if dates else None

    for relative in CITATION_FILES:
        path = root / "interview" / relative
        if not path.is_file():
            continue
        text = safe_read(path, issues)
        if text is None:
            continue
        for tag in INFERENCE_TAG.findall(text):
            for cited in QNUM.findall(tag):
                number = int(cited)
                if number not in valid:
                    issues.append(
                        f"{relative}: citation Q{number} in {tag!r} not found in log "
                        f"(answered through Q{last})"
                    )
        for fvol_date in FVOL_TAG.findall(text):
            try:
                date.fromisoformat(fvol_date)
            except ValueError:
                issues.append(
                    f"{relative}: F-vol citation has malformed date {fvol_date!r}"
                )
                continue
            if max_date is not None and fvol_date > max_date:
                issues.append(
                    f"{relative}: F-vol citation date {fvol_date} is after the "
                    f"latest date in the verbatim record ({max_date})"
                )
    return issues


def check_stale_phrases(root: Path) -> List[str]:
    """Flag a pending-claim about an already-answered Q in a canonical
    current-state ledger (A2 / G013)."""
    issues: List[str] = []
    log_path = root / "interview/log.md"
    if not log_path.is_file():
        return issues
    log_text = safe_read(log_path, issues)
    if log_text is None:
        return issues
    numbers = parse_log_questions(log_text)
    if not numbers:
        return issues
    last = max(numbers)

    for relative in STALE_SCAN_FILES:
        path = root / relative
        if not path.is_file():
            continue
        text = safe_read(path, issues)
        if text is None:
            continue
        for match in STALE_PENDING.finditer(text):
            number = int(match.group(1))
            if number <= last:
                issues.append(
                    f"{relative}: stale pending-claim {match.group(0)!r} — "
                    f"Q{number} is already answered (log max Q{last})"
                )
    return issues


CARD_HEADING = re.compile(r"^## Q(\d+)\b.*$", re.MULTILINE)
ANY_HEADING = re.compile(r"^#{1,2} ", re.MULTILINE)


def _card_blocks(text: str) -> List[tuple]:
    """A card's block ends at the next heading of any kind, so a trailing
    drafts section (`# Prepared re-ask candidates` / `## RE-ASK ...`) is not
    absorbed into the last real card."""
    blocks = []
    for match in CARD_HEADING.finditer(text):
        boundary = ANY_HEADING.search(text, match.end())
        end = boundary.start() if boundary else len(text)
        blocks.append((int(match.group(1)), match.group(0), text[match.start():end]))
    return blocks


def check_validation_cards(root: Path, closed: bool = False) -> List[str]:
    """B4: the most-recent SENT validation card must carry a `Wide-pass:` line
    and a coverage/gap reference. E1: any card marked `rejected` must carry a
    `Rejection class:` line. Both are exact, forward-safe structural checks.
    Post-close, B4 is retired — no new question will
    ever be sent, so the newest-sent-card gate is dead machinery; E1 stays,
    as historical card hygiene is static and cheap."""
    issues: List[str] = []
    path = root / "interview/validations.md"
    if not path.is_file():
        return issues
    text = safe_read(path, issues)
    if text is None:
        return issues
    blocks = _card_blocks(text)

    sent = [] if closed else [
        (q, h, b) for q, h, b in blocks if re.search(r"\bsent\b", h, re.IGNORECASE)
    ]
    if sent:
        # "Most recent" = last sent card by DOCUMENT ORDER, not max Q number
        # (a re-derived card for a lower Q number is newer
        # than an older higher-numbered one; picking max-Q let it ship ungated).
        _, heading, body = sent[-1]
        if not re.search(r"Wide-pass:", body, re.IGNORECASE):
            issues.append(
                f"validations.md: most recent sent card {heading.strip()!r} is "
                "missing a 'Wide-pass:' line (B4)"
            )
        if not re.search(r"coverage debt served|gap id", body, re.IGNORECASE):
            issues.append(
                f"validations.md: most recent sent card {heading.strip()!r} names "
                "no Gap ID / coverage debt (B4)"
            )

    for _q, heading, body in blocks:
        # ASCII-hyphen and parenthesized forms count too (
        # '- rejected' / '(rejected)' used to evade the em-dash-only matcher).
        if re.search(r"[—-]\s*rejected\b|\(rejected\)", heading, re.IGNORECASE) and not re.search(
            r"Rejection class:", body, re.IGNORECASE
        ):
            issues.append(
                f"validations.md: rejected card {heading.strip()!r} is missing a "
                "'Rejection class:' line (E1)"
            )
    return issues


def check_log_topical_completeness(root: Path, log_text: str) -> List[str]:
    """C2 (WARNING, never FAIL): an answered Q with no [F/I/H-Qn] citation in
    any topical file is invisible to a cold agent (the topical files ARE the
    retrieval layer). Soft signal — surfaced as a capped warning to avoid
    alarm-fatigue (architecture review C4)."""
    answered = set(parse_log_questions(log_text))
    if not answered:
        return []
    cited: set = set()
    for relative in CITATION_FILES:
        path = root / "interview" / relative
        if not path.is_file():
            continue
        text = safe_read(path, [])
        if text is None:
            continue
        for tag in INFERENCE_TAG.findall(text):
            cited.update(int(n) for n in QNUM.findall(tag))
    uncited = sorted(answered - cited)
    if not uncited:
        return []
    shown = ", ".join(f"Q{n}" for n in uncited[:15])
    more = f" (+{len(uncited) - 15} more)" if len(uncited) > 15 else ""
    return [
        f"{len(uncited)} answered Q(s) not indexed into any topical file "
        f"(invisible to a cold agent): {shown}{more}"
    ]


# F-vol tags are scanned across ALL citation-bearing files, not a narrower
# hand-picked list (tags in synthesis/hypotheses/
# validations previously passed only because the same dates also appeared in
# scanned files — a new date used only there would silently skip C1).
VOLUNTEER_TAGGED_FILES = sorted(set(CITATION_FILES) | {"turns.md", "themes.md"})
VOLUNTEER_ENTRY = re.compile(r"^## V-(\d{4}-\d{2}-\d{2})-\d+", re.MULTILINE)


def check_volunteer_provenance(root: Path) -> List[str]:
    """C1 (exact, date-keyed): every distinct F-vol DATE present in the topical
    files must have a verbatim home — a `## V-<date>-N` entry in
    volunteer-log.md. The tag carries only a date (no per-item key), so this is
    date-level by design; per-item completeness is left to human judgment, not
    a fuzzy FAIL (architecture review C4)."""
    issues: List[str] = []
    dates: set = set()
    for name in VOLUNTEER_TAGGED_FILES:
        path = root / "interview" / name
        if not path.is_file():
            continue
        text = safe_read(path, issues)
        if text is None:
            continue
        dates.update(FVOL_TAG.findall(text))
    if not dates:
        return issues
    vlog = root / "interview" / "volunteer-log.md"
    if not vlog.is_file():
        issues.append(
            "volunteer-log.md is missing but F-vol material exists for "
            f"date(s): {', '.join(sorted(dates))} (C1)"
        )
        return issues
    vtext = safe_read(vlog, issues)
    if vtext is None:
        return issues
    homed = set(VOLUNTEER_ENTRY.findall(vtext))
    for missing in sorted(dates - homed):
        issues.append(
            f"F-vol material dated {missing} has no verbatim home "
            f"(## V-{missing}-N) in volunteer-log.md (C1)"
        )
    return issues


def check_ledger(root: Path) -> List[str]:
    """The derived coverage ledger must exist and equal a fresh computation.
    Drift = a skipped regeneration or a hand-edit (B2). Regenerate with
    `python3 scripts/coverage_ledger.py --write`."""
    issues: List[str] = []
    fresh = coverage_ledger.build_ledger(root)
    path = root / coverage_ledger.LEDGER_PATH
    if not path.is_file():
        issues.append(
            f"Derived ledger missing: {coverage_ledger.LEDGER_PATH} — run "
            "`python3 scripts/coverage_ledger.py --write`"
        )
        return issues
    on_disk = safe_read(path, issues)
    if on_disk is None:
        return issues
    if on_disk.rstrip("\n") != fresh.rstrip("\n"):
        issues.append(
            f"Derived ledger is stale: {coverage_ledger.LEDGER_PATH} differs "
            "from a fresh computation — run "
            "`python3 scripts/coverage_ledger.py --write` and commit it"
        )
    return issues


def check_log_operational_markers(log_text: str) -> List[str]:
    """Markers are scanned only on operational-LABEL lines, never inside a
    subject's verbatim answer body (A5 / A5-F4)."""
    issues = []
    operational = "\n".join(
        line for line in log_text.splitlines() if OPERATIONAL_LINE.match(line)
    )
    if not operational:
        return issues
    for marker in LOG_OPERATIONAL_MARKERS:
        if marker.search(operational):
            issues.append(f"Operational marker /{marker.pattern}/ found in interview/log.md")
    return issues


# ---------------------------------------------------------------------------
# Drafting fidelity gate (prose). The prose twin of the question-asking gate.
# The gate is MANDATORY for every book/**/*.md (a later audit inverted
# the old opt-in default, under which uncarded prose was silently invisible):
# a file must either carry a `Card: DC-<n>` header (and is then fully
# inspected) or declare itself non-draft with a first-line exemption token
# (RETRACTED / TEMPLATE / NON-CANONICAL / NOTES / SUPERSEDED). Neither → FAIL.
# Code enforces only what regex can DECIDE with near-zero false positives
# (provenance, forbidden sources, citation resolution, kinship-degree sourcing);
# the human `### Relationships asserted` block carries what code cannot judge.
# ---------------------------------------------------------------------------
DRAFT_CARD = re.compile(r"^(?:\*\*)?Card:(?:\*\*)?\s*DC-\d+\s*$", re.MULTILINE)
LEDGER_HEAD = re.compile(r"^##\s+Fidelity ledger", re.IGNORECASE | re.MULTILINE)
SUBBLOCK_HEAD = re.compile(r"^###\s+(.*)$", re.MULTILINE)
LEVEL2_HEAD = re.compile(r"^##\s+", re.MULTILINE)
SKIP_DRAFT_FIRSTLINE = re.compile(
    r"RETRACTED|TEMPLATE|NON-CANONICAL|NOTES|SUPERSEDED", re.IGNORECASE
)
REQUIRED_SUBBLOCKS = ["Sourced", "Invented", "Relationships asserted"]
# Derived/navigation files: never a valid source for a drafted fact. A prior
# agent's inference, written into these, is how "four boys" became "four
# brothers"; a draft may not re-launder it as provenance.
FORBIDDEN_DRAFT_SRC = [
    "scenes.md", "_resume.md", "state.md",
    "hypotheses.md", "gaps.md", "coverage.md",
]
F_CITE = re.compile(r"\[F[^\]]*\]")
IH_TAG = re.compile(r"\[(?:I|H)[^\]]*\]")
DEGREE = re.compile(
    r"\b(?:brothers?|sisters?|siblings?|half[- ]?(?:brother|sister)s?|"
    r"step[- ]?(?:brother|sister|sibling)s?|full[- ]?(?:brother|sister|sibling)s?)\b",
    re.IGNORECASE,
)
KINSHIP = re.compile(
    r"\b(?:brothers?|sisters?|siblings?|half[- ]?\w*|step[- ]?\w*|"
    r"mother|father|sons?|daughters?)\b",
    re.IGNORECASE,
)
NO_KINSHIP = re.compile(r"\[no kinship asserted\]", re.IGNORECASE)


def _first_nonempty_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return line
    return ""


def _ledger_region(text: str) -> Optional[str]:
    """The Fidelity-ledger block: from its heading to the next level-2 heading
    (so a trailing `## What the draft is doing` note is not absorbed)."""
    head = LEDGER_HEAD.search(text)
    if not head:
        return None
    nxt = LEVEL2_HEAD.search(text, head.end())
    return text[head.end(): nxt.start() if nxt else len(text)]


def _subblock(ledger: str, name: str) -> Optional[str]:
    heads = list(SUBBLOCK_HEAD.finditer(ledger))
    for i, match in enumerate(heads):
        if name.lower() in match.group(1).lower():
            end = heads[i + 1].start() if i + 1 < len(heads) else len(ledger)
            return ledger[match.end():end]
    return None


def _carded_drafts(root: Path):
    book = root / "book"
    if not book.is_dir():
        return
    for path in sorted(book.glob("**/*.md")):
        text = safe_read(path, [])
        if text is None:
            continue
        if SKIP_DRAFT_FIRSTLINE.search(_first_nonempty_line(text)):
            continue
        if not DRAFT_CARD.search(text):
            continue
        yield path.relative_to(root), text


def check_uncarded_book_prose(root: Path) -> List[str]:
    """FAIL: a book/**/*.md that neither carries a `Card: DC-<n>` line nor
    declares a first-line exemption token. Inverts the old opt-in default —
    prose must not be able to dodge the fidelity gate by omitting the card
    (a draft once sat ungated with a fabrication
    history while the doctor printed OK)."""
    issues: List[str] = []
    book = root / "book"
    if not book.is_dir():
        return issues
    for path in sorted(book.glob("**/*.md")):
        text = safe_read(path, issues)
        if text is None:
            continue
        rel = path.relative_to(root)
        if SKIP_DRAFT_FIRSTLINE.search(_first_nonempty_line(text)):
            continue
        if not DRAFT_CARD.search(text):
            issues.append(
                f"{rel}: book file has neither a 'Card: DC-<n>' line nor a "
                "first-line exemption token (RETRACTED / TEMPLATE / "
                "NON-CANONICAL / NOTES / SUPERSEDED) — uncarded prose cannot "
                "bypass the fidelity gate"
            )
    return issues


def check_draft_fidelity(root: Path, log_text: str) -> List[str]:
    """Prose gate (FAIL): a carded book draft must carry a Fidelity ledger with
    Sourced / Invented / Relationships-asserted sub-blocks; its citations must
    resolve to answered Qs; it may not source a fact from a derived navigation
    file; and any kinship DEGREE it asserts must cite cast.md (or assert none)."""
    issues: List[str] = []
    numbers = parse_log_questions(log_text)
    valid = set(numbers)
    last = max(numbers) if numbers else 0
    for rel, text in _carded_drafts(root):
        ledger = _ledger_region(text)
        if ledger is None:
            issues.append(f"{rel}: carded draft is missing a '## Fidelity ledger' block")
            continue
        for name in REQUIRED_SUBBLOCKS:
            if _subblock(ledger, name) is None:
                issues.append(f"{rel}: Fidelity ledger missing '### {name}' sub-block")
        for tag in INFERENCE_TAG.findall(text):
            for cited in QNUM.findall(tag):
                if int(cited) not in valid:
                    issues.append(
                        f"{rel}: citation Q{cited} in {tag!r} not found in log "
                        f"(answered through Q{last})"
                    )
        for name in ("Sourced", "Relationships asserted"):
            block = _subblock(ledger, name) or ""
            for fname in FORBIDDEN_DRAFT_SRC:
                if fname in block:
                    issues.append(
                        f"{rel}: '### {name}' cites derived file {fname!r} — drafts "
                        "may only source facts from log.md / cast.md / facts.md"
                    )
        rel_block = _subblock(ledger, "Relationships asserted")
        if rel_block is not None:
            for line in rel_block.splitlines():
                if not line.strip() or line.lstrip().startswith("#"):
                    continue
                if DEGREE.search(line) and not NO_KINSHIP.search(line) and "cast.md" not in line:
                    issues.append(
                        f"{rel}: relationship line {line.strip()[:60]!r} asserts a "
                        "kinship degree without a cast.md citation (or "
                        "'[no kinship asserted]')"
                    )
    return issues


def check_draft_kinship_unaccounted(root: Path) -> List[str]:
    """WARN (capped): a kinship word in the prose that is not enumerated in the
    '### Relationships asserted' block — a prompt to confirm it asserts no
    unsourced kinship. Stays a WARN: clause-level entailment is undecidable, so
    the human enumeration is the real guard and the regex only a backstop."""
    warnings: List[str] = []
    for rel, text in _carded_drafts(root):
        head = LEDGER_HEAD.search(text)
        prose = text[:head.start()] if head else text
        rel_block = (_subblock(_ledger_region(text) or "", "Relationships asserted") or "").lower()
        for word in sorted({m.group(0).lower() for m in KINSHIP.finditer(prose)}):
            if word not in rel_block:
                warnings.append(
                    f"{rel}: kinship word {word!r} appears in the prose but is not "
                    "enumerated in '### Relationships asserted' — confirm it asserts "
                    "no unsourced kinship"
                )
    return warnings[:8]


INLINE_CODE = re.compile(r"`[^`]*`")


def check_no_inference_on_fact_lines(root: Path) -> List[str]:
    """FAIL: an [I]/[H] read sharing a line with an [F] fact cite in
    cast.md/facts.md. This is the exact seam that collapsed (an inference
    appended to a quoted fact, then re-read as fact); keeping fact bullets pure
    [F] means a skimming agent cannot lift an inference as testimony. Exempts
    inline-code spans, so the `[F]`/`[I]` tag LEGEND is not flagged. Markdown
    table rows are enforced at the CELL level (the old
    whole-row exemption left the invariant open in facts.md's dominant format;
    a fact-column + inference-column row stays legal, same-cell laundering
    does not)."""
    issues: List[str] = []
    for name in ("cast.md", "facts.md"):
        path = root / "interview" / name
        if not path.is_file():
            continue
        text = safe_read(path, [])
        if text is None:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            scrubbed = INLINE_CODE.sub("", line)
            if line.lstrip().startswith("|"):
                for cell in scrubbed.split("|"):
                    if (F_CITE.search(cell) or FVOL_TAG.search(cell)) and IH_TAG.search(cell):
                        issues.append(
                            f"{name}:{i}: a table cell mixes an [F] fact cite with an "
                            "[I]/[H] inference tag — split into separate cells/rows "
                            "(clean-[F] invariant, cell-level)"
                        )
                        break
                continue
            if (F_CITE.search(scrubbed) or FVOL_TAG.search(scrubbed)) and IH_TAG.search(scrubbed):
                issues.append(
                    f"{name}:{i}: an [I]/[H] inference shares a line with an [F] "
                    "fact cite — move the inference to its own line (clean-[F] invariant)"
                )
    return issues


def interview_not_started(state_text: str, log_text: str) -> bool:
    """A fresh clone before Q1: state.md says zero answered AND the log has no
    Q headings. That is a valid state, not drift — the sequence/state checks
    are skipped for it. A non-zero count against an empty log is still a FAIL
    (a claimed answer with no verbatim home)."""
    answered = parse_state_table(state_text).get("Questions answered", "").strip()
    return answered == "0" and not parse_log_questions(log_text)


def run_checks(root: Path) -> List[str]:
    issues: List[str] = []
    issues.extend(check_required_files(root))

    log_path = root / "interview/log.md"
    state_path = root / "interview/state.md"
    resume_path = root / "interview/_resume.md"

    log_text = (safe_read(log_path, issues) or "") if log_path.is_file() else ""
    state_text = safe_read(state_path, issues) if state_path.is_file() else None
    fresh = bool(state_text) and interview_not_started(state_text, log_text)

    if log_text:
        if not fresh:
            issues.extend(check_log_sequence(log_text))
        issues.extend(check_log_operational_markers(log_text))
        issues.extend(check_citations(root, log_text))

    if state_text is not None and log_text and not fresh:
        issues.extend(check_state_matches_log(state_text, log_text))
    closed = interview_closed(state_text) if state_text else False

    if resume_path.is_file() and log_text:
        resume_text = safe_read(resume_path, issues)
        if resume_text is not None:
            issues.extend(check_resume_matches_log(resume_text, log_text))

    issues.extend(check_stale_phrases(root))
    issues.extend(check_ledger(root))
    issues.extend(check_validation_cards(root, closed=closed))
    issues.extend(check_volunteer_provenance(root))
    issues.extend(check_uncarded_book_prose(root))
    issues.extend(check_draft_fidelity(root, log_text))
    issues.extend(check_no_inference_on_fact_lines(root))
    return issues


def run_warnings(root: Path) -> List[str]:
    """Non-blocking signals — surfaced, never a FAIL (keeps the doctor's
    near-zero false-positive authority; architecture review C4)."""
    warnings: List[str] = []
    log_path = root / "interview/log.md"
    if log_path.is_file():
        log_text = safe_read(log_path, [])
        if log_text:
            warnings.extend(check_log_topical_completeness(root, log_text))
    warnings.extend(check_draft_kinship_unaccounted(root))
    return warnings


def format_issues(issues: Iterable[str]) -> str:
    return "\n".join(f"- {issue}" for issue in issues)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", help="Repository root to check")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    issues = run_checks(root)
    warnings = run_warnings(root)
    if issues:
        print("memoir_doctor: FAIL")
        print(format_issues(issues))
        if warnings:
            print("memoir_doctor: WARN")
            print(format_issues(warnings))
        return 1
    print("memoir_doctor: OK")
    if warnings:
        print("memoir_doctor: WARN")
        print(format_issues(warnings))
    return 0


if __name__ == "__main__":
    sys.exit(main())
