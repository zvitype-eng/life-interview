import tempfile
import unittest
from pathlib import Path

from scripts import coverage_ledger


GAPS = """# Gaps Queue

| ID | Type | Priority | Source | Owner File | Repair Shape | Status |
|---|---|---:|---|---|---|---|
| G001 | relationship | **P0** | Q2, Q8 | cast.md | Dad as person | open |
| G002 | identity | P0 | Q5 | voice.md | Faith now | strong/near-retired (Q5 done) |
| G005 | identity | P0 | Q3 | threads.md | Worker interior | open |
| G028 | story | **P0** | F-vol-2026-06-10 | scenes.md | The box of pictures | open |
| G015 | process | P0 | Review 2026 | state.md | burn-down gate | open |
| G031 | world | P2 | F-vol-2026-06-10 | voice.md | Reading life blank; favorite books | open |
"""

VALIDATIONS = """# Validation Cards

## Q9 — 2026-01-09 — sent
Candidate: something
Job tag: deepen-identity
Coverage debt served: G005 (P0 — worker/maker interior).
Referents: x

## Q4 — 2026-01-04 — sent
Coverage debt served: G002 (P0).
"""

COVERAGE = """# Coverage Governance

## World Inventory

| Domain | Status | Notes |
|---|---|---|
| Places lived | STRONG | full sequence |
| Health (his own) | BLANK | never asked |
| Books / culture / media | BLANK | reading blank |
| Daily routines | PARTIAL | shabbos yes |
"""

LOG = "".join(f"## Q{n} — 2026-01-0{n}\n**A:** a\n\n" for n in range(1, 10))  # Q1..Q9


def _make_tree(tmp):
    root = Path(tmp)
    interview = root / "interview"
    interview.mkdir()
    (interview / "gaps.md").write_text(GAPS, encoding="utf-8")
    (interview / "validations.md").write_text(VALIDATIONS, encoding="utf-8")
    (interview / "coverage.md").write_text(COVERAGE, encoding="utf-8")
    (interview / "log.md").write_text(LOG, encoding="utf-8")
    return root


class CoverageLedgerTests(unittest.TestCase):
    def test_priority_emphasis_is_stripped(self):
        # **P0** must be read as P0, not silently dropped.
        rows = coverage_ledger.parse_gaps(GAPS)
        g001 = next(r for r in rows if r["id"] == "G001")
        self.assertEqual(g001["priority"], "P0")

    def test_status_classified_from_prose(self):
        rows = coverage_ledger.parse_gaps(GAPS)
        self.assertEqual(coverage_ledger.status_word("strong/near-retired (Q5 done)"), "strong")
        g005 = next(r for r in rows if r["id"] == "G005")
        self.assertEqual(g005["status_word"], "open")

    def test_last_touched_uses_gaps_and_validation_cards(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _make_tree(tmp)
            ledger = coverage_ledger.build_ledger(root)
        # G005: source Q3 + a Q9 card serving it -> last touched Q9, untouched 0.
        self.assertRegex(ledger, r"G005[^\n]*last touched Q9[^\n]*untouched 0")
        # G001: source Q2,Q8, no serving card -> last touched Q8, untouched 1.
        self.assertRegex(ledger, r"G001[^\n]*last touched Q8[^\n]*untouched 1")

    def test_never_asked_p0_surfaced_as_top_starved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _make_tree(tmp)
            ledger = coverage_ledger.build_ledger(root)
        # G028 is an open P0 sourced only from volunteered material (no numbered
        # Q) -> never asked -> it is the top-starved pointer.
        self.assertRegex(ledger, r"Top-starved P0:\W*G028")
        self.assertRegex(ledger, r"G028[^\n]*not yet asked")

    def test_process_gaps_are_not_question_targets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _make_tree(tmp)
            ledger = coverage_ledger.build_ledger(root)
        # G015 is a process gap: never the top-starved pointer (not askable),
        # and listed separately from the askable starvation rows.
        self.assertNotRegex(ledger, r"Top-starved P0:\W*G015")
        askable = ledger.split("## Process")[0].split("## Starvation")[1]
        self.assertNotIn("G015", askable)
        self.assertIn("G015", ledger)

    def test_retired_gap_excluded_from_starvation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _make_tree(tmp)
            ledger = coverage_ledger.build_ledger(root)
        # G002 is strong/near-retired -> not an open/partial starvation row.
        starv = ledger.split("## BLANK")[0]
        self.assertNotIn("G002", starv)

    def test_card_services_stop_at_section_boundary(self):
        # A "## RE-ASK" / "# Prepared" drafts section after the last ## Q card
        # must NOT be absorbed into that card's block (it would mis-attribute
        # draft gap references to a real question).
        text = (
            "# cards\n\n## Q1 — 2026-01-01 — sent\nCoverage debt served: G001.\n\n"
            "# Prepared re-ask candidates\n\n"
            "## RE-ASK A — x\nCoverage debt served: G999.\n"
        )
        served = coverage_ledger.parse_card_services(text)
        self.assertIn(1, served.get("G001", set()))
        self.assertNotIn(1, served.get("G999", set()))

    def test_blank_domains_and_ungapped_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _make_tree(tmp)
            ledger = coverage_ledger.build_ledger(root)
        # Health is BLANK with no gap naming it -> flagged.
        self.assertRegex(ledger, r"Health[^\n]*BLANK[^\n]*(no gap|no open gap|⚠)")
        # Books/media is BLANK but G031 names "books" -> not flagged ungapped.
        books_line = next(l for l in ledger.splitlines() if "Books" in l)
        self.assertNotIn("no gap", books_line)
        self.assertIn("G031", books_line)


    def test_retired_gap_does_not_claim_domain(self):
        # Audit 2026-07-03 M6: a retired/strong gap whose repair text mentions
        # a BLANK domain must NOT suppress the no-open-gap flag.
        retired_gaps = GAPS.replace(
            "| G031 | world | P2 | F-vol-2026-06-10 | voice.md | Reading life blank; favorite books | open |",
            "| G031 | world | P2 | F-vol-2026-06-10 | voice.md | Reading life blank; favorite books | retired (done) |",
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = _make_tree(tmp)
            (root / "interview" / "gaps.md").write_text(retired_gaps, encoding="utf-8")
            ledger = coverage_ledger.build_ledger(root)
        books_line = next(l for l in ledger.splitlines() if "Books" in l)
        self.assertNotIn("G031", books_line)
        self.assertRegex(books_line, r"no gap|no open gap|⚠")


if __name__ == "__main__":
    unittest.main()
