import tempfile
import unittest
from pathlib import Path

from bobguard_demo import (
    incident_artifact_label,
    incident_evidence_paths,
    incident_test_output_paths,
    inspect_release_evidence,
    list_repository_files,
    mask_sensitive_text,
    read_safe_excerpt,
)


class EvidenceDiscoveryTests(unittest.TestCase):
    def test_empty_checkout_does_not_invent_incident_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.assertEqual(incident_evidence_paths(root, "INC-001"), ())
            self.assertEqual(incident_evidence_paths(root, "INC-002"), ())

    def test_incident_artifacts_are_discovered_by_path_or_content(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "incidents" / "INC-001").mkdir(parents=True)
            (root / "incidents" / "INC-001" / "logs.md").write_text(
                "synthetic incident record", encoding="utf-8"
            )
            (root / "tests").mkdir()
            (root / "tests" / "checks.ps1").write_text(
                "# checks for INC-002", encoding="utf-8"
            )

            self.assertEqual(
                incident_evidence_paths(root, "INC-001"),
                ("incidents/INC-001/logs.md",),
            )
            self.assertEqual(
                incident_evidence_paths(root, "INC-002"),
                ("tests/checks.ps1",),
            )

    def test_demo_code_is_not_reported_as_incident_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "app.py").write_text("INC-001", encoding="utf-8")
            (root / "bobguard_demo.py").write_text("INC-002", encoding="utf-8")
            (root / "README.md").write_text(
                "Documented run: INC-001 and INC-002", encoding="utf-8"
            )
            self.assertEqual(incident_evidence_paths(root, "INC-001"), ())
            self.assertEqual(incident_evidence_paths(root, "INC-002"), ())

    def test_unsupported_incident_id_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(ValueError):
                incident_evidence_paths(Path(temp_dir), "INC-999")

    def test_only_incident_and_log_artifacts_are_labeled_synthetic(self) -> None:
        self.assertIn(
            "synthetic",
            incident_artifact_label("incidents/INC-001/logs.md"),
        )
        self.assertIn(
            "source or test",
            incident_artifact_label("app/Invoke-Calculator.ps1"),
        )

    def test_run_output_is_distinguished_from_test_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "tests").mkdir()
            (root / "tests" / "Invoke-Tests.ps1").write_text(
                "# INC-001 assertions", encoding="utf-8"
            )
            (root / "test-results-INC-001.txt").write_text(
                "PASS 4/4", encoding="utf-8"
            )
            self.assertEqual(
                incident_test_output_paths(root, "INC-001"),
                ("test-results-INC-001.txt",),
            )


class DisplaySafetyTests(unittest.TestCase):
    def test_common_credential_shapes_are_masked(self) -> None:
        text = (
            'SYNTHETIC_API_TOKEN = "demo-credential-value"\n'
            "Authorization: Bearer bearer-secret-value\n"
            "AWS key: AKIA1234567890ABCDEF"
        )

        masked = mask_sensitive_text(text)

        self.assertNotIn("demo-credential-value", masked)
        self.assertNotIn("bearer-secret-value", masked)
        self.assertNotIn("AKIA1234567890ABCDEF", masked)
        self.assertEqual(masked.count("[REDACTED]"), 3)

    def test_excerpt_is_bounded_and_rejects_paths_outside_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "evidence.md").write_text("x" * 30, encoding="utf-8")
            excerpt = read_safe_excerpt(root, "evidence.md", max_chars=10)
            self.assertEqual(excerpt, "x" * 10 + "\n… excerpt truncated …")
            with self.assertRaises(ValueError):
                read_safe_excerpt(root, "..\\outside.md")

    def test_excerpt_masks_values_before_display(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "logs.md").write_text(
                'SYNTHETIC_TOKEN = "never-display-this-value"',
                encoding="utf-8",
            )
            excerpt = read_safe_excerpt(root, "logs.md")
            self.assertNotIn("never-display-this-value", excerpt)
            self.assertIn("[REDACTED]", excerpt)


class ReleaseStatusTests(unittest.TestCase):
    def test_checker_result_and_dependency_audit_are_separate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "release-check.ps1").write_text("checker", encoding="utf-8")
            evidence = inspect_release_evidence(root)

            self.assertIn("checker", evidence.checker_status.lower())
            self.assertIn("no saved result", evidence.checker_status.lower())
            self.assertEqual(evidence.audit_status, "Dependency audit not verified.")

    def test_output_presence_never_becomes_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "release-check-result.txt").write_text(
                "checker output", encoding="utf-8"
            )
            (root / "dependency-audit-report.json").write_text(
                '{"status": "unknown"}', encoding="utf-8"
            )
            evidence = inspect_release_evidence(root)

            self.assertIn("not interpreted", evidence.checker_status.lower())
            self.assertIn("requires review", evidence.audit_status.lower())
            self.assertNotIn("approv", evidence.checker_status.lower())
            self.assertNotIn("approv", evidence.audit_status.lower())

    def test_inventory_ignores_local_caches(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".venv" / "Lib").mkdir(parents=True)
            (root / ".venv" / "Lib" / "secret.txt").write_text("x", encoding="utf-8")
            (root / "README.md").write_text("readme", encoding="utf-8")
            self.assertEqual(list_repository_files(root), ("README.md",))


if __name__ == "__main__":
    unittest.main()
