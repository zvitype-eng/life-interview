import tempfile
import unittest
from pathlib import Path

from scripts import coverage_ledger, memoir_doctor


def _ledger_tree(tmp):
    root = Path(tmp)
    interview = root / "interview"
    interview.mkdir()
    (interview / "gaps.md").write_text(
        "| ID | Type | Priority | Source | Owner | Repair | Status |\n"
        "|---|---|---|---|---|---|---|\n"
        "| G001 | story | P0 | Q1 | a | the box | open |\n",
        encoding="utf-8",
    )
    (interview / "validations.md").write_text("# cards\n", encoding="utf-8")
    (interview / "coverage.md").write_text(
        "## World Inventory\n\n| Domain | Status | Notes |\n|---|---|---|\n"
        "| Health | BLANK | x |\n",
        encoding="utf-8",
    )
    (interview / "log.md").write_text("## Q1 — 2026-01-01\n", encoding="utf-8")
    return root


class MemoirDoctorTests(unittest.TestCase):
    def test_parse_log_questions_returns_numbers_in_order(self):
        text = "## Q1 — 2026-01-01\n**Q:** A\n**A:** B\n\n## Q2 — 2026-01-02\n"

        self.assertEqual(memoir_doctor.parse_log_questions(text), [1, 2])

    def test_check_log_sequence_flags_duplicate_question(self):
        text = "## Q1 — 2026-01-01\n\n## Q1 — 2026-01-02\n"

        issues = memoir_doctor.check_log_sequence(text)

        self.assertTrue(any("Duplicate question number: Q1" in issue for issue in issues))

    def test_check_state_matches_log_flags_mismatch(self):
        state = """| Field | Value |
|---|---|
| Last answered question | Q66 |
| Questions answered | 66 |
| Next question | Q67 |
"""
        log = "## Q66 — 2026-01-01\n\n## Q67 — 2026-01-02\n"

        issues = memoir_doctor.check_state_matches_log(state, log)

        self.assertTrue(any("Last answered question" in issue for issue in issues))
        self.assertTrue(any("Questions answered" in issue for issue in issues))
        self.assertTrue(any("Next question" in issue for issue in issues))

    def test_check_stale_phrases_flags_pending_claim_in_current_state_file(self):
        # A2: a pending-claim about an already-answered Q, in a canonical
        # current-state ledger (state.md / _resume.md), is stale drift.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            interview = root / "interview"
            interview.mkdir()
            (interview / "log.md").write_text(
                "".join(f"## Q{n} — 2026-01-01\n\n" for n in range(1, 87)),
                encoding="utf-8",
            )
            (interview / "state.md").write_text("Q66 in flight\n", encoding="utf-8")

            issues = memoir_doctor.check_stale_phrases(root)

        self.assertTrue(any("Q66" in issue for issue in issues))

    def test_check_stale_phrase_regex_flags_new(self):
        # A2: the generalized regex catches a pending-phrase the old 2-entry
        # hardcoded dict never listed (e.g. "unanswered").
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            interview = root / "interview"
            interview.mkdir()
            (interview / "log.md").write_text(
                "## Q1 — d\n\n## Q2 — d\n\n## Q3 — d\n", encoding="utf-8"
            )
            (interview / "_resume.md").write_text(
                "Status: Q2 unanswered\n", encoding="utf-8"
            )

            issues = memoir_doctor.check_stale_phrases(root)

        self.assertTrue(any("Q2" in issue for issue in issues))

    def test_check_log_operational_markers_flags_notes(self):
        log = "## Q1 — 2026-01-01\n**Q:** X\n**A:** Y\n**Disposition:** bad\n"

        issues = memoir_doctor.check_log_operational_markers(log)

        self.assertTrue(any("Operational marker" in issue for issue in issues))

    def test_check_log_operational_markers_flags_ops_patterns_case_insensitive(self):
        log = "## Q1 — 2026-01-01\n**Q:** X\n**A:** Y\nNote: clarified after withdrawn pivoting soft-close.\n"

        issues = memoir_doctor.check_log_operational_markers(log)

        self.assertGreaterEqual(len(issues), 5)

    def test_check_required_files_flags_missing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            issues = memoir_doctor.check_required_files(Path(tmp))

        self.assertTrue(any("AGENTS.md" in issue for issue in issues))

    def test_check_resume_matches_log_flags_mismatch(self):
        resume = "| Questions answered | 99 |\n| Last answered | Q42 |\n"
        log = "## Q1 — d\n\n## Q2 — d\n\n## Q3 — d\n"

        issues = memoir_doctor.check_resume_matches_log(resume, log)

        self.assertTrue(any("Questions answered" in issue for issue in issues))
        self.assertTrue(any("Last answered" in issue for issue in issues))

    def test_check_citations_flags_dangling_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            interview = root / "interview"
            interview.mkdir()
            (interview / "cast.md").write_text(
                "A real fact [F-Q2] and a dangling one [I-Q999].\n", encoding="utf-8"
            )
            log = "## Q1 — d\n\n## Q2 — d\n\n## Q3 — d\n"

            issues = memoir_doctor.check_citations(root, log)

        self.assertTrue(any("Q999" in issue for issue in issues))
        self.assertFalse(any("Q2 " in issue for issue in issues))

    def test_check_resume_missing_field_fails(self):
        # A1: absent/unparseable status fields must FAIL, not silently pass.
        resume = "a resume with no recognizable status table at all\n"
        log = "## Q1 — d\n\n## Q2 — d\n"

        issues = memoir_doctor.check_resume_matches_log(resume, log)

        self.assertTrue(any("Questions answered" in issue for issue in issues))
        self.assertTrue(any("Last answered" in issue for issue in issues))

    def test_read_error_reported_as_fail(self):
        # A3: a non-UTF-8 / unreadable file is reported as an issue, not a crash.
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.md"
            bad.write_bytes(b"\xff\xfe\x00 not valid utf-8")
            issues = []

            result = memoir_doctor.safe_read(bad, issues)

        self.assertIsNone(result)
        self.assertTrue(any("Cannot read" in issue for issue in issues))

    def test_fvol_citation_validated(self):
        # A4: bare F-vol-DATE tags are visible and a future date is flagged.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            interview = root / "interview"
            interview.mkdir()
            (interview / "facts.md").write_text(
                "fine F-vol-2026-01-01 and future F-vol-2099-12-31\n",
                encoding="utf-8",
            )
            log = "## Q1 — 2026-01-01\n\n## Q2 — 2026-01-02\n"

            issues = memoir_doctor.check_citations(root, log)

        self.assertTrue(any("2099-12-31" in issue for issue in issues))
        self.assertFalse(any("2026-01-01" in issue for issue in issues))

    def test_fvol_date_after_last_q_but_in_volunteer_log_is_ok(self):
        # Volunteer material is given between numbered questions, so its date can
        # legitimately be later than the last logged Q — as long as it's homed in
        # volunteer-log.md. It must NOT be flagged as a future date.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            interview = root / "interview"
            interview.mkdir()
            (interview / "facts.md").write_text(
                "later volunteer fact F-vol-2026-01-05\n", encoding="utf-8"
            )
            (interview / "volunteer-log.md").write_text(
                "## V-2026-01-05-1 — a thing\nverbatim\n", encoding="utf-8"
            )
            log = "## Q1 — 2026-01-01\n\n## Q2 — 2026-01-02\n"
            issues = memoir_doctor.check_citations(root, log)
        self.assertFalse(any("2026-01-05" in issue for issue in issues))

    def test_check_citations_scans_added_files(self):
        # A6: budget.md is now in scope for citation resolution.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            interview = root / "interview"
            interview.mkdir()
            (interview / "budget.md").write_text(
                "a dangling tag [F-Q999]\n", encoding="utf-8"
            )
            log = "## Q1 — d\n\n## Q2 — d\n"

            issues = memoir_doctor.check_citations(root, log)

        self.assertTrue(any("Q999" in issue and "budget.md" in issue for issue in issues))

    def test_marker_not_flagged_in_answer_body(self):
        # A5: marker words inside a verbatim answer body are not flagged.
        log = (
            "## Q1 — 2026-01-01\n"
            "**Q:** X\n"
            "**A:** I clarified my feelings to her; we kept pivoting between "
            "cities, and it felt like a soft-close on that chapter.\n"
        )

        issues = memoir_doctor.check_log_operational_markers(log)

        self.assertEqual(issues, [])

    def test_volunteer_provenance_missing_home_fails(self):
        # C1: an F-vol date present in topical files but with no `## V-<date>-N`
        # entry in volunteer-log.md is a FAIL (date-keyed, exact).
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "interview").mkdir()
            (root / "interview" / "facts.md").write_text(
                "a fact F-vol-2026-06-10 tagged\n", encoding="utf-8"
            )
            issues = memoir_doctor.check_volunteer_provenance(root)
        self.assertTrue(any("2026-06-10" in issue for issue in issues))

    def test_volunteer_provenance_satisfied(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "interview").mkdir()
            (root / "interview" / "facts.md").write_text(
                "a fact F-vol-2026-06-10 tagged\n", encoding="utf-8"
            )
            (root / "interview" / "volunteer-log.md").write_text(
                "## V-2026-06-10-1 — staircase\nverbatim line\n", encoding="utf-8"
            )
            issues = memoir_doctor.check_volunteer_provenance(root)
        self.assertEqual(issues, [])

    def test_log_topical_completeness_warns_uncited(self):
        # C2: an answered Q with no [F/I-Qn] citation in any topical file is a
        # non-blocking WARNING (not a FAIL).
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            interview = root / "interview"
            interview.mkdir()
            log = "## Q1 — d\n\n## Q2 — d\n\n## Q3 — d\n"
            (interview / "log.md").write_text(log, encoding="utf-8")
            (interview / "cast.md").write_text(
                "rendered [F-Q1] and [I-Q2]\n", encoding="utf-8"
            )
            warnings = memoir_doctor.check_log_topical_completeness(root, log)
        self.assertTrue(any("Q3" in w for w in warnings))
        self.assertFalse(any("Q1" in w for w in warnings))

    def test_completeness_is_not_a_fail(self):
        # C2 must never push a FAIL: it is surfaced via run_warnings, not run_checks.
        self.assertTrue(hasattr(memoir_doctor, "run_warnings"))

    def test_ledger_absent_fails(self):
        # B2: a missing derived ledger is a FAIL.
        with tempfile.TemporaryDirectory() as tmp:
            root = _ledger_tree(tmp)
            issues = memoir_doctor.check_ledger(root)
        self.assertTrue(any("missing" in issue.lower() for issue in issues))

    def test_ledger_drift_fails(self):
        # B2: an on-disk ledger that differs from a fresh computation is a FAIL.
        with tempfile.TemporaryDirectory() as tmp:
            root = _ledger_tree(tmp)
            derived = root / "interview" / "derived"
            derived.mkdir()
            (derived / "coverage-ledger.md").write_text(
                "stale wrong content\n", encoding="utf-8"
            )
            issues = memoir_doctor.check_ledger(root)
        self.assertTrue(any("stale" in issue.lower() for issue in issues))

    def test_widepass_required_on_latest_sent_card(self):
        # B4: the most-recent sent card must carry a Wide-pass line.
        text = (
            "# cards\n\n## Q1 — 2026-01-01 — sent\n"
            "Job tag: x\nCoverage debt served: G001.\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "interview").mkdir()
            (root / "interview" / "validations.md").write_text(text, encoding="utf-8")
            issues = memoir_doctor.check_validation_cards(root)
        self.assertTrue(any("Wide-pass" in issue for issue in issues))

    def test_validation_cards_pass_when_complete(self):
        text = (
            "# cards\n\n## Q1 — 2026-01-01 — sent\n"
            "Wide-pass: top-starved=G001; BLANK=Health\n"
            "Coverage debt served: G001.\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "interview").mkdir()
            (root / "interview" / "validations.md").write_text(text, encoding="utf-8")
            issues = memoir_doctor.check_validation_cards(root)
        self.assertEqual(issues, [])

    def test_rejected_card_requires_class(self):
        # E1: a card marked rejected must carry a Rejection class.
        text = "# cards\n\n## Q2 — 2026-01-02 — rejected\nReason: meh\n"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "interview").mkdir()
            (root / "interview" / "validations.md").write_text(text, encoding="utf-8")
            issues = memoir_doctor.check_validation_cards(root)
        self.assertTrue(any("Rejection class" in issue for issue in issues))

    def test_ledger_fresh_passes(self):
        # B2: a freshly written ledger drifts on nothing.
        with tempfile.TemporaryDirectory() as tmp:
            root = _ledger_tree(tmp)
            derived = root / "interview" / "derived"
            derived.mkdir()
            (derived / "coverage-ledger.md").write_text(
                coverage_ledger.build_ledger(root) + "\n", encoding="utf-8"
            )
            issues = memoir_doctor.check_ledger(root)
        self.assertEqual(issues, [])


def _book_tree(tmp, files):
    """Minimal repo with a book/ dir. `files` maps relative book path -> text."""
    root = Path(tmp)
    for rel, text in files.items():
        path = root / "book" / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return root


GOOD_DRAFT = """# Draft — test scene

Card: DC-9

Some prose about a brook [F-Q2].

## Fidelity ledger

### Sourced
- The brook [F-Q2].

### Invented
- Weather texture.

### Relationships asserted
- [no kinship asserted]
"""

LOG_TWO_QS = "## Q1 — 2026-01-01\n**Q:** a\n**A:** b\n\n## Q2 — 2026-01-02\n**Q:** c\n**A:** d\n"


class DraftFidelityGateTests(unittest.TestCase):
    # Audit 2026-07-03 C3/H3: the drafting gate had zero coverage; the gate is
    # now mandatory (uncarded book prose FAILs) and these tests pin each
    # enforced behavior so a refactor cannot silently disable it.

    def test_uncarded_book_prose_fails(self):
        # C3 regression: mode-samples.md sat ungated while the doctor said OK.
        with tempfile.TemporaryDirectory() as tmp:
            root = _book_tree(tmp, {"dry-run/sample.md": "# A sample\n\nProse.\n"})
            issues = memoir_doctor.check_uncarded_book_prose(root)
        self.assertTrue(any("neither a 'Card: DC-<n>' line" in i for i in issues))

    def test_exemption_tokens_skip_uncarded_check(self):
        files = {
            "a.md": "# ⚠ RETRACTED — dead\n\nGone.\n",
            "b.md": "# SCENE TEMPLATE — copy me\n",
            "c.md": "# Notes [NOTES — planning, not prose]\n",
            "d.md": "# Experiment (NON-CANONICAL)\n",
            "e.md": "# ⚠ SUPERSEDED — do not lift\n",
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = _book_tree(tmp, files)
            issues = memoir_doctor.check_uncarded_book_prose(root)
        self.assertEqual(issues, [])

    def test_carded_draft_passes_uncarded_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _book_tree(tmp, {"scene.md": GOOD_DRAFT})
            issues = memoir_doctor.check_uncarded_book_prose(root)
        self.assertEqual(issues, [])

    def test_bold_card_variant_is_recognized(self):
        # C3: `**Card:** DC-1` used to evade the strict regex and skip the gate.
        text = GOOD_DRAFT.replace("Card: DC-9", "**Card:** DC-9")
        with tempfile.TemporaryDirectory() as tmp:
            root = _book_tree(tmp, {"scene.md": text})
            self.assertEqual(memoir_doctor.check_uncarded_book_prose(root), [])
            # and it is actually inspected, not just excused:
            bad = text.replace("## Fidelity ledger", "## Something else")
            (root / "book" / "scene.md").write_text(bad, encoding="utf-8")
            issues = memoir_doctor.check_draft_fidelity(root, LOG_TWO_QS)
        self.assertTrue(any("missing a '## Fidelity ledger'" in i for i in issues))

    def test_carded_draft_without_ledger_fails(self):
        text = "# Draft\n\nCard: DC-9\n\nProse.\n"
        with tempfile.TemporaryDirectory() as tmp:
            root = _book_tree(tmp, {"scene.md": text})
            issues = memoir_doctor.check_draft_fidelity(root, LOG_TWO_QS)
        self.assertTrue(any("missing a '## Fidelity ledger'" in i for i in issues))

    def test_missing_subblock_fails(self):
        text = GOOD_DRAFT.replace("### Invented\n- Weather texture.\n\n", "")
        with tempfile.TemporaryDirectory() as tmp:
            root = _book_tree(tmp, {"scene.md": text})
            issues = memoir_doctor.check_draft_fidelity(root, LOG_TWO_QS)
        self.assertTrue(any("missing '### Invented'" in i for i in issues))

    def test_dangling_citation_in_draft_fails(self):
        text = GOOD_DRAFT.replace("[F-Q2]", "[F-Q99]")
        with tempfile.TemporaryDirectory() as tmp:
            root = _book_tree(tmp, {"scene.md": text})
            issues = memoir_doctor.check_draft_fidelity(root, LOG_TWO_QS)
        self.assertTrue(any("Q99" in i for i in issues))

    def test_forbidden_derived_source_fails(self):
        # The "four boys → four brothers" laundering path: scenes.md as source.
        text = GOOD_DRAFT.replace("- The brook [F-Q2].", "- The brook (scenes.md).")
        with tempfile.TemporaryDirectory() as tmp:
            root = _book_tree(tmp, {"scene.md": text})
            issues = memoir_doctor.check_draft_fidelity(root, LOG_TWO_QS)
        self.assertTrue(any("scenes.md" in i for i in issues))

    def test_kinship_degree_without_cast_cite_fails(self):
        text = GOOD_DRAFT.replace(
            "- [no kinship asserted]", "- the four are brothers [F-Q2]"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = _book_tree(tmp, {"scene.md": text})
            issues = memoir_doctor.check_draft_fidelity(root, LOG_TWO_QS)
        self.assertTrue(any("kinship degree without a cast.md citation" in i for i in issues))

    def test_kinship_degree_with_cast_cite_passes(self):
        text = GOOD_DRAFT.replace(
            "- [no kinship asserted]",
            "- Jordan is his full brother (cast.md roster) [F-Q2]",
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = _book_tree(tmp, {"scene.md": text})
            issues = memoir_doctor.check_draft_fidelity(root, LOG_TWO_QS)
        self.assertEqual(issues, [])

    def test_good_draft_passes_everything(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _book_tree(tmp, {"scene.md": GOOD_DRAFT})
            issues = memoir_doctor.check_draft_fidelity(root, LOG_TWO_QS)
            issues += memoir_doctor.check_uncarded_book_prose(root)
        self.assertEqual(issues, [])


class PhaseGateTests(unittest.TestCase):
    # Audit 2026-07-03 H8: post-close, interview-turn machinery is retired —
    # the doctor reads the CLOSED flag from state.md's own Interview-status row.

    CLOSED_STATE = """| Field | Value |
|---|---|
| Last answered question | Q2 |
| Questions answered | 2 |
| Next question | — |
| ⚠ Interview status | **CLOSED 2026-06-26** — no question is pending. |
"""

    def test_closed_marker_next_question_accepted_when_closed(self):
        issues = memoir_doctor.check_state_matches_log(self.CLOSED_STATE, LOG_TWO_QS)
        self.assertEqual(issues, [])

    def test_numeric_next_question_still_accepted_when_closed(self):
        state = self.CLOSED_STATE.replace("| Next question | — |", "| Next question | Q3 |")
        issues = memoir_doctor.check_state_matches_log(state, LOG_TWO_QS)
        self.assertEqual(issues, [])

    def test_wrong_next_question_still_fails_when_closed(self):
        state = self.CLOSED_STATE.replace("| Next question | — |", "| Next question | Q9 |")
        issues = memoir_doctor.check_state_matches_log(state, LOG_TWO_QS)
        self.assertTrue(any("Next question" in i for i in issues))

    def test_open_interview_still_requires_numeric_next_question(self):
        state = self.CLOSED_STATE.replace(
            "| ⚠ Interview status | **CLOSED 2026-06-26** — no question is pending. |", ""
        ).replace("| Next question | — |", "| Next question | — |")
        issues = memoir_doctor.check_state_matches_log(state, LOG_TWO_QS)
        self.assertTrue(any("Next question" in i for i in issues))

    def test_widepass_gate_skipped_when_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "interview").mkdir()
            (root / "interview" / "validations.md").write_text(
                "## Q2 — 2026-01-02 — sent\nno wide-pass line here\n",
                encoding="utf-8",
            )
            open_issues = memoir_doctor.check_validation_cards(root, closed=False)
            closed_issues = memoir_doctor.check_validation_cards(root, closed=True)
        self.assertTrue(any("Wide-pass" in i for i in open_issues))
        self.assertEqual(closed_issues, [])

    def test_rejection_class_still_enforced_when_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "interview").mkdir()
            (root / "interview" / "validations.md").write_text(
                "## Q2 — 2026-01-02 — rejected\nno class line\n",
                encoding="utf-8",
            )
            issues = memoir_doctor.check_validation_cards(root, closed=True)
        self.assertTrue(any("Rejection class" in i for i in issues))

    def test_rejected_matcher_catches_ascii_hyphen_and_parens(self):
        # Audit 2026-07-03 M5: '- rejected' / '(rejected)' evaded the em-dash matcher.
        for heading in ("## Q2 — 2026-01-02 - rejected", "## Q2 — 2026-01-02 (rejected)"):
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                (root / "interview").mkdir()
                (root / "interview" / "validations.md").write_text(
                    heading + "\nno class line\n", encoding="utf-8"
                )
                issues = memoir_doctor.check_validation_cards(root)
            self.assertTrue(
                any("Rejection class" in i for i in issues), msg=heading
            )

    def test_widepass_gate_checks_last_sent_card_by_position(self):
        # Audit 2026-07-03 M5: a re-derived card for a LOWER Q number, appended
        # later, is the most recent sent card — max-Q selection let it ship ungated.
        text = (
            "## Q9 — 2026-01-09 — sent\nWide-pass: done\nCoverage debt served: G001\n\n"
            "## Q4 — 2026-02-01 — sent\nno wide-pass here\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "interview").mkdir()
            (root / "interview" / "validations.md").write_text(text, encoding="utf-8")
            issues = memoir_doctor.check_validation_cards(root)
        self.assertTrue(any("Wide-pass" in i and "Q4" in i for i in issues))


class CleanFTableCellTests(unittest.TestCase):
    # Audit 2026-07-03 H4: the whole-row table exemption left the clean-[F]
    # invariant open in facts.md's dominant format; now enforced per cell.

    def _facts_tree(self, tmp, facts_text):
        root = Path(tmp)
        (root / "interview").mkdir()
        (root / "interview" / "facts.md").write_text(facts_text, encoding="utf-8")
        return root

    def test_same_cell_f_and_i_mix_fails(self):
        row = "| item | a fact [F-Q1] plus a guess [I, near-certain] | F-Q1 |\n"
        with tempfile.TemporaryDirectory() as tmp:
            root = self._facts_tree(tmp, row)
            issues = memoir_doctor.check_no_inference_on_fact_lines(root)
        self.assertTrue(any("table cell mixes" in i for i in issues))

    def test_cross_column_row_passes(self):
        # A fact column and a separate source/inference column stay legal.
        row = "| item | a fact [F-Q1] | I-Q17, F-Q1 |\n"
        with tempfile.TemporaryDirectory() as tmp:
            root = self._facts_tree(tmp, row)
            issues = memoir_doctor.check_no_inference_on_fact_lines(root)
        self.assertEqual(issues, [])

    def test_non_table_line_mix_still_fails(self):
        line = "- a fact [F-Q1] and an inference [I] on one line\n"
        with tempfile.TemporaryDirectory() as tmp:
            root = self._facts_tree(tmp, line)
            issues = memoir_doctor.check_no_inference_on_fact_lines(root)
        self.assertTrue(any("clean-[F] invariant" in i for i in issues))


if __name__ == "__main__":
    unittest.main()


class FreshStartTests(unittest.TestCase):
    """A template clone before Q1 must be doctor-green; a claimed count with
    no verbatim must not be."""

    STATE_ZERO = (
        "| Field | Value |\n|---|---|\n"
        "| Last answered question | — |\n"
        "| Questions answered | 0 |\n"
        "| Next question | Q1 |\n"
        "| Interview status | OPEN |\n"
    )
    STATE_THREE = STATE_ZERO.replace("| 0 |", "| 3 |").replace("| — |", "| Q3 |").replace("| Q1 |", "| Q4 |")

    def _fresh_tree(self, tmp, state_text):
        root = Path(tmp)
        for rel in memoir_doctor.REQUIRED_FILES:
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"# {path.name}\n", encoding="utf-8")
        (root / "interview/state.md").write_text(state_text, encoding="utf-8")
        (root / "interview/_resume.md").write_text(
            "| Questions answered | 0 |\n| Last answered | — |\n", encoding="utf-8"
        )
        (root / "interview/gaps.md").write_text(
            "| ID | Type | Priority | Source | Owner | Repair | Status |\n|---|---|---|---|---|---|---|\n",
            encoding="utf-8",
        )
        coverage_ledger.write_ledger(root)
        return root

    def test_interview_not_started_requires_zero_and_empty_log(self):
        self.assertTrue(memoir_doctor.interview_not_started(self.STATE_ZERO, "# log\n"))
        self.assertFalse(memoir_doctor.interview_not_started(self.STATE_THREE, "# log\n"))
        self.assertFalse(memoir_doctor.interview_not_started(self.STATE_ZERO, "## Q1 — 2026-01-01\n"))

    def test_fresh_clone_before_q1_is_green(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._fresh_tree(tmp, self.STATE_ZERO)
            self.assertEqual(memoir_doctor.run_checks(root), [])

    def test_claimed_answers_with_empty_log_still_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._fresh_tree(tmp, self.STATE_THREE)
            issues = memoir_doctor.run_checks(root)
            self.assertTrue(any("No answered Q headings" in i for i in issues), issues)
