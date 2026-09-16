#!/usr/bin/env python3
"""Compute the coverage/starvation ledger from the canonical interview files.

This is a *derived* view (B1): it parses `gaps.md`, `validations.md`, and the
`coverage.md` World Inventory and emits, as human-readable Markdown, what is
starved — so the WIDE pass is a computed fact, not honour-system. It encodes
nothing the doctor cannot recompute; it points *into* the source and never
substitutes for reading it. `memoir_doctor.py` regenerates it and FAILs on
drift (B2).

Parser notes grounded in the live corpus:
- `gaps.md` Priority cells are inconsistent (`P0` vs bolded `**P0**`).
- `gaps.md` Status is free prose, not an enum (classified by leading word).
- `gaps.md` Source mixes `Q12, Q34` with `F-vol-...`/`Review ...` tokens.
- validation cards record the gap they serve as `Coverage debt served: G005`.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

LEDGER_PATH = "interview/derived/coverage-ledger.md"

GAP_ROW = re.compile(r"^\|\s*(G\d+)\s*\|", re.MULTILINE)
QNUM = re.compile(r"Q(\d+)")
GID = re.compile(r"G\d+")
CARD_HEADING = re.compile(r"^## Q(\d+)\b", re.MULTILINE)
COVERAGE_SERVED = re.compile(r"Coverage debt served:\s*(.+)")
LOG_Q = re.compile(r"^## Q(\d+)\b", re.MULTILINE)
PRIORITY = re.compile(r"P\d")
WORLD_STATUS = re.compile(r"\b(STRONG|PARTIAL|THIN|BLANK)\b")

_STOPWORDS = {"his", "own", "the", "and", "side", "per", "era", "life", "tree"}
ACTIVE_STATUSES = {"open", "partial"}
# Gap types that are NOT interview-question targets — process/protocol, form,
# safety, and meta gaps are tracked but never drive next-question selection, so
# they are listed apart and excluded from the top-starved pointer.
NON_ASKABLE_TYPES = {"process", "form", "safety", "meta"}


def read(root: Path, name: str) -> str:
    path = root / "interview" / name
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def status_word(raw: str) -> str:
    match = re.match(r"\s*([A-Za-z]+)", raw)
    return match.group(1).lower() if match else ""


def parse_gaps(text: str) -> List[Dict]:
    rows: List[Dict] = []
    for line in text.splitlines():
        if not GAP_ROW.match(line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 7:
            continue
        gap_id, gap_type, priority, source, _owner, repair, status = cells[:7]
        pmatch = PRIORITY.search(priority)
        rows.append(
            {
                "id": gap_id,
                "type": gap_type.lower(),
                "priority": pmatch.group(0) if pmatch else "",
                "source_qs": [int(n) for n in QNUM.findall(source)],
                "status_word": status_word(status),
                "raw_status": status,
                "repair": repair,
                "source_raw": source,
            }
        )
    return rows


ANY_HEADING = re.compile(r"^#{1,2} ", re.MULTILINE)


def parse_card_services(text: str) -> Dict[str, Set[int]]:
    """Map gap id -> set of validation-card Q numbers that served it. A card's
    block ends at the next heading of ANY kind, so a trailing drafts section
    (e.g. `# Prepared re-ask candidates` / `## RE-ASK ...`) is not absorbed
    into the last real card."""
    served: Dict[str, Set[int]] = {}
    for match in CARD_HEADING.finditer(text):
        q = int(match.group(1))
        boundary = ANY_HEADING.search(text, match.end())
        end = boundary.start() if boundary else len(text)
        block = text[match.end():end]
        for line in COVERAGE_SERVED.findall(block):
            for gid in GID.findall(line):
                served.setdefault(gid, set()).add(q)
    return served


def parse_world_inventory(text: str) -> List[Tuple[str, str]]:
    """Return (domain, STATUS) rows from the World Inventory table."""
    domains: List[Tuple[str, str]] = []
    in_section = False
    for line in text.splitlines():
        if line.startswith("## "):
            in_section = "World Inventory" in line
            continue
        if not in_section or not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue
        domain, status_cell = cells[0], cells[1]
        if domain in {"Domain", "---"} or domain.startswith("---"):
            continue
        smatch = WORLD_STATUS.search(status_cell)
        if not smatch:
            continue
        domains.append((domain, smatch.group(1)))
    return domains


def log_max(text: str) -> int:
    nums = [int(n) for n in LOG_Q.findall(text)]
    return max(nums) if nums else 0


def _domain_keywords(domain: str) -> List[str]:
    words = re.findall(r"[A-Za-z]+", domain.lower())
    return [w for w in words if len(w) >= 4 and w not in _STOPWORDS]


def _gap_for_domain(domain: str, gaps: List[Dict]) -> Optional[str]:
    keywords = _domain_keywords(domain)
    if not keywords:
        return None
    # Whole-word match only: substring matching falsely links e.g. the "media"
    # domain to "immediate" in an unrelated gap.
    pattern = re.compile(r"\b(?:" + "|".join(re.escape(k) for k in keywords) + r")\b")
    for gap in gaps:
        # Only ACTIVE gaps count as coverage governance :
        # a retired/strong gap whose repair text mentions the domain used to
        # claim a BLANK domain and suppress the ⚠ no-open-gap flag.
        if gap["status_word"] not in ACTIVE_STATUSES:
            continue
        hay = f"{gap['repair']} {gap['source_raw']}".lower()
        if pattern.search(hay):
            return gap["id"]
    return None


def build_ledger(root: Path) -> str:
    gaps = parse_gaps(read(root, "gaps.md"))
    services = parse_card_services(read(root, "validations.md"))
    domains = parse_world_inventory(read(root, "coverage.md"))
    max_q = log_max(read(root, "log.md"))

    # Starvation rows for active (open/partial) P0/P1 gaps.
    active = [
        g for g in gaps
        if g["priority"] in {"P0", "P1"} and g["status_word"] in ACTIVE_STATUSES
    ]
    rows = []
    for gap in active:
        touched = set(gap["source_qs"]) | services.get(gap["id"], set())
        last = max(touched) if touched else None
        untouched = (max_q - last) if last is not None else None
        rows.append({**gap, "last": last, "untouched": untouched})

    # Rank: never-asked first, then largest untouched-count; P0 ahead of P1.
    def sort_key(r):
        never = r["last"] is None
        return (
            0 if r["priority"] == "P0" else 1,
            0 if never else 1,
            -(r["untouched"] or 0),
            r["id"],
        )

    rows.sort(key=sort_key)

    askable_rows = [r for r in rows if r["type"] not in NON_ASKABLE_TYPES]
    process_rows = [r for r in rows if r["type"] in NON_ASKABLE_TYPES]

    p0_rows = [r for r in askable_rows if r["priority"] == "P0"]
    top = p0_rows[0]["id"] if p0_rows else "none"

    out: List[str] = []
    out.append("# Coverage / Starvation Ledger — DERIVED, do not edit")
    out.append("")
    out.append(
        "Regenerated by `scripts/memoir_doctor.py` from `gaps.md` + "
        "`validations.md` + `coverage.md`. If the on-disk copy differs from a "
        "fresh computation, the doctor FAILs. This is a navigation layer into "
        "the source — never a substitute for reading it."
    )
    out.append("")
    out.append(f"**Log max:** Q{max_q}")
    out.append(f"**Top-starved P0:** {top}")
    out.append("")
    out.append("## Starvation — active (open/partial) P0/P1 question targets")
    out.append("")

    def render(row) -> str:
        if row["last"] is None:
            detail = "not yet asked"
        else:
            detail = f"last touched Q{row['last']}, untouched {row['untouched']}"
        return f"- {row['id']} ({row['priority']}, {row['status_word']}) — {detail}"

    if not askable_rows:
        out.append("_(none)_")
    for r in askable_rows:
        out.append(render(r))
    out.append("")
    out.append("## Process / form / meta gaps (tracked, not question targets)")
    out.append("")
    if not process_rows:
        out.append("_(none)_")
    for r in process_rows:
        out.append(render(r))
    out.append("")
    out.append("## BLANK World-Inventory domains")
    out.append("")
    blanks = [(d, s) for d, s in domains if s == "BLANK"]
    if not blanks:
        out.append("_(none)_")
    for domain, _ in blanks:
        gid = _gap_for_domain(domain, gaps)
        if gid:
            out.append(f"- {domain}: BLANK — gap {gid}")
        else:
            out.append(f"- {domain}: BLANK — ⚠ no open gap names this domain")
    out.append("")
    return "\n".join(out)


def write_ledger(root: Path) -> Path:
    """Write the freshly computed ledger to its canonical derived path."""
    path = root / LEDGER_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_ledger(root) + "\n", encoding="utf-8")
    return path


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument(
        "--write",
        action="store_true",
        help=f"Write the ledger to {LEDGER_PATH} instead of printing it",
    )
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    if args.write:
        path = write_ledger(root)
        print(f"wrote {path}")
    else:
        print(build_ledger(root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
