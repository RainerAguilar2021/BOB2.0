"""Evidence discovery and presentation helpers for the BobGuard web demo."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


INCIDENT_IDS = ("INC-001", "INC-002")
TEXT_SUFFIXES = {
    ".csv",
    ".json",
    ".log",
    ".md",
    ".ps1",
    ".py",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}
IGNORED_DIRECTORIES = {
    ".git",
    ".pytest_cache",
    ".streamlit",
    ".venv",
    "__pycache__",
    "node_modules",
    "venv",
}
DEMO_FILES = {
    ".gitignore",
    "app.py",
    "bobguard_demo.py",
    "requirements.txt",
    "tests/test_bobguard_demo.py",
}
REFERENCE_DOCUMENTS = {"README.md"}

_CREDENTIAL_ASSIGNMENT = re.compile(
    r"""(?ix)
    ((?:^|[^a-z0-9])(?:[a-z0-9]+[_-])*
    (?:password|passwd|token|secret|api[_-]?key|client[_-]?secret|credential)
    ["']?\s*[:=]\s*["']?)
    (?:"[^"\r\n]*"|'[^'\r\n]*'|[^\s,;}]+)
    """
)
_BEARER_TOKEN = re.compile(
    r"(?i)(\bAuthorization\s*:\s*Bearer\s+)[A-Za-z0-9._~+/=-]+"
)
_KNOWN_TOKEN_SHAPES = re.compile(
    r"\b(?:AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{20,})\b"
)


@dataclass(frozen=True)
class ReleaseEvidence:
    policy_files: tuple[str, ...]
    checker_files: tuple[str, ...]
    checker_output_files: tuple[str, ...]
    audit_output_files: tuple[str, ...]

    @property
    def checker_status(self) -> str:
        if self.checker_output_files:
            return "An output file exists; its verdict is not interpreted automatically."
        if self.checker_files:
            return "A checker was found, but no saved result was found."
        return "No checker evidence was found."

    @property
    def audit_status(self) -> str:
        if self.audit_output_files:
            return "An audit-related file exists; its result requires review."
        return "Dependency audit not verified."


def list_repository_files(root: Path) -> tuple[str, ...]:
    """Return repository-relative files while excluding VCS and local caches."""
    resolved_root = root.resolve()
    files: list[str] = []
    for path in resolved_root.rglob("*"):
        relative = path.relative_to(resolved_root)
        if any(part.lower() in IGNORED_DIRECTORIES for part in relative.parts):
            continue
        if path.is_file() and not path.is_symlink():
            files.append(relative.as_posix())
    return tuple(sorted(files))


def incident_evidence_paths(root: Path, incident_id: str) -> tuple[str, ...]:
    """Find text artifacts that refer to an incident, without treating this app as evidence."""
    if incident_id not in INCIDENT_IDS:
        raise ValueError(f"Unsupported incident ID: {incident_id}")

    resolved_root = root.resolve()
    matches: list[str] = []
    for relative_path in list_repository_files(resolved_root):
        if relative_path in DEMO_FILES or relative_path in REFERENCE_DOCUMENTS:
            continue
        path = resolved_root / Path(relative_path)
        if incident_id in relative_path.upper():
            matches.append(relative_path)
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        content = path.read_text(encoding="utf-8", errors="replace")
        if incident_id in content.upper():
            matches.append(relative_path)
    return tuple(matches)


def incident_artifact_label(relative_path: str) -> str:
    """Distinguish synthetic incident/log material from source and test files."""
    path = Path(relative_path)
    parts = {part.lower() for part in path.parts}
    filename = path.name.lower()
    output_file = path.suffix.lower() in {".csv", ".json", ".log", ".md", ".txt"}
    if (
        "incidents" in parts
        or "incident" in filename
        or "log" in filename
        or (
            output_file
            and any(marker in filename for marker in ("result", "output", "transcript"))
        )
    ):
        return "synthetic incident/run artifact"
    return "repository source or test file"


def incident_test_output_paths(root: Path, incident_id: str) -> tuple[str, ...]:
    """Find clearly named run outputs; source tests alone are not execution results."""
    output_markers = ("result", "output", "transcript", "test-run", "test_run")
    return tuple(
        relative_path
        for relative_path in incident_evidence_paths(root, incident_id)
        if Path(relative_path).suffix.lower() in {".csv", ".json", ".log", ".md", ".txt"}
        and any(
            marker in Path(relative_path).name.lower()
            for marker in output_markers
        )
    )


def mask_sensitive_text(text: str) -> str:
    """Mask common credential-shaped text for display; this is not a security boundary."""
    masked = _CREDENTIAL_ASSIGNMENT.sub(r"\1[REDACTED]", text)
    masked = _BEARER_TOKEN.sub(r"\1[REDACTED]", masked)
    return _KNOWN_TOKEN_SHAPES.sub("[REDACTED]", masked)


def read_safe_excerpt(root: Path, relative_path: str, max_chars: int = 4000) -> str:
    """Read a bounded, masked excerpt from a repository-relative path."""
    resolved_root = root.resolve()
    candidate = (resolved_root / relative_path).resolve()
    try:
        candidate.relative_to(resolved_root)
    except ValueError as error:
        raise ValueError("Evidence path must stay inside the repository.") from error
    if not candidate.is_file():
        raise FileNotFoundError(relative_path)
    if max_chars < 1:
        raise ValueError("max_chars must be positive.")
    with candidate.open(encoding="utf-8", errors="replace") as source:
        content = source.read(max_chars + 1)
    excerpt = mask_sensitive_text(content[:max_chars])
    if len(content) > max_chars:
        excerpt += "\n… excerpt truncated …"
    return excerpt


def inspect_release_evidence(root: Path) -> ReleaseEvidence:
    """Report which release artifacts exist without inferring that any gate passed."""
    files = tuple(
        path
        for path in list_repository_files(root)
        if path not in DEMO_FILES
    )
    policy_files = tuple(
        path
        for path in files
        if "policy" in Path(path).name.lower()
        and "report" in Path(path).name.lower()
    )
    checker_files = tuple(
        path
        for path in files
        if "release" in Path(path).name.lower()
        and any(word in Path(path).name.lower() for word in ("check", "gate"))
    )
    output_markers = ("output", "result", "transcript", "report")
    checker_output_files = tuple(
        path
        for path in checker_files
        if Path(path).suffix.lower() in {".csv", ".json", ".log", ".md", ".txt"}
        or any(marker in Path(path).name.lower() for marker in output_markers)
    )
    audit_output_files = tuple(
        path
        for path in files
        if any(word in Path(path).name.lower() for word in ("audit", "dependency"))
        and (
            Path(path).suffix.lower() in {".csv", ".json", ".log", ".md", ".txt"}
            or any(marker in Path(path).name.lower() for marker in output_markers)
        )
    )
    return ReleaseEvidence(
        policy_files=policy_files,
        checker_files=checker_files,
        checker_output_files=checker_output_files,
        audit_output_files=audit_output_files,
    )
