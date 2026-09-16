import tempfile
import unittest
from pathlib import Path

from scripts import question_packet


class QuestionPacketTests(unittest.TestCase):
    def test_extract_last_qas_returns_last_three_entries(self):
        log = "\n\n".join(
            f"## Q{i} — 2026-01-0{i}\n**Q:** Question {i}\n**A:** Answer {i}"
            for i in range(1, 5)
        )

        entries = question_packet.extract_last_qas(log, count=3)

        self.assertEqual([entry.number for entry in entries], [2, 3, 4])
        self.assertIn("Answer 4", entries[-1].body)

    def test_extract_lane_finds_q68_range(self):
        plan = """| Range | Job | Guardrail |
|---|---|---|
| Q68-Q70 | Finish travel | Max two more travel questions. |
| Q71-Q76 | Present | Austin. |
"""

        lane = question_packet.extract_lane(plan, "Q68")

        self.assertIn("Q68-Q70", lane)
        self.assertIn("Finish travel", lane)

    def _packet_tree(self, root):
        interview = root / "interview"
        interview.mkdir()
        (interview / "state.md").write_text(
            "| Field | Value |\n|---|---|\n| Next question | Q11 |\n", encoding="utf-8"
        )
        (interview / "turns.md").write_text(
            "## 2026-05-29 — Q11 — provenance ambiguity\nDo not reuse.\n", encoding="utf-8"
        )
        (interview / "log.md").write_text(
            "".join(f"## Q{i} — 2026-01-0{i % 10}\n**Q:** Q{i}\n**A:** Answer {i}\n\n" for i in range(1, 11)),
            encoding="utf-8",
        )
        (interview / "gaps.md").write_text(
            "| ID | Type | Priority | Source | Owner | Repair | Status |\n"
            "|---|---|---|---|---|---|---|\n"
            "| G028 | story | **P0** | F-vol-2026-01-09 | scenes.md | The box of pictures | open |\n"
            "| G005 | identity | P0 | Q3 | threads.md | Worker interior | open |\n",
            encoding="utf-8",
        )
        (interview / "validations.md").write_text(
            "# cards\n\n## Q10 — 2026-01-09 — sent\nJob tag: deepen-person\n"
            "Coverage debt served: G005 (P0).\n",
            encoding="utf-8",
        )
        (interview / "coverage.md").write_text(
            "## World Inventory\n\n| Domain | Status | Notes |\n|---|---|---|\n"
            "| Health | BLANK | never asked |\n",
            encoding="utf-8",
        )
        (interview / "facts.md").write_text(
            "His stepmother's first husband is [TBD].\n", encoding="utf-8"
        )
        (interview / "remaining-plan.md").write_text(
            "| Range | Job | Guardrail |\n|---|---|---|\n| Q11-Q20 | Synthesis | go gently. |\n",
            encoding="utf-8",
        )
        return interview

    def test_rejection_profile_flags_repeated_class(self):
        # E2: >=2 rejections of the same class -> a recurring pattern to promote.
        turns = (
            "## 2026-01-01 — Q5 — rejected\nRejection class: direction\n\n"
            "## 2026-01-02 — Q6 — rejected\nRejection class: direction\n\n"
            "## 2026-01-03 — Q7 — rejected\nRejection class: craft\n"
        )
        profile = question_packet.extract_rejection_profile(turns)
        self.assertIn("direction", profile)
        self.assertRegex(profile, r"direction[^\n]*2")
        self.assertIn("recurring", profile.lower())

    def test_rejection_profile_empty_when_none(self):
        profile = question_packet.extract_rejection_profile("## 2026 — Q1 — sent\n")
        self.assertIn("none", profile.lower())

    def test_build_packet_hard_errors_without_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._packet_tree(root)
            with self.assertRaises(FileNotFoundError):
                question_packet.build_packet(root, "Q11")

    def test_build_packet_wide_before_narrow(self):
        from scripts import coverage_ledger

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._packet_tree(root)
            coverage_ledger.write_ledger(root)

            packet = question_packet.build_packet(root, "Q11")

        # WIDE content present and placed before the NARROW live thread.
        self.assertIn("WIDE PASS", packet)
        self.assertIn("G028", packet)  # top-starved P0 from the ledger
        self.assertIn("Health", packet)  # BLANK domain
        self.assertIn("[TBD]", packet)  # untagged-hole grep
        self.assertIn("Canonical State", packet)
        self.assertIn("Validation Checklist", packet)
        self.assertLess(packet.index("WIDE PASS"), packet.index("Canonical State"))


if __name__ == "__main__":
    unittest.main()
