from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
IGNORED_PARTS = {".git", ".venv", "venv", "__pycache__", "node_modules"}
TEXT_SUFFIXES = {".py", ".md", ".txt", ".yaml", ".yml", ".json", ".toml", ".ini", ".cfg", ".example"}
PATTERNS = {
    "private key": re.compile(r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY"),
    "OpenAI-style key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "Telegram bot token": re.compile(r"\b\d{8,12}:AA[A-Za-z0-9_-]{20,}\b"),
    "hardcoded Flask secret": re.compile(r"(?i)(?:SECRET_KEY|API_WRITE_TOKEN)\s*=\s*['\"][^'\"]{16,}['\"]"),
}


def candidate_files(root: Path = ROOT):
    for path in root.rglob("*"):
        if not path.is_file() or any(part in IGNORED_PARTS for part in path.parts):
            continue
        if path.name == ".env":
            yield path
            continue
        if path.suffix.lower() in TEXT_SUFFIXES or path.name in {"Dockerfile", "Procfile"}:
            yield path


def main() -> int:
    findings: list[str] = []
    for path in candidate_files():
        relative = path.relative_to(ROOT)
        if path.name == ".env":
            findings.append(f"{relative}: populated environment file must not be committed")
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for name, pattern in PATTERNS.items():
            if pattern.search(text):
                findings.append(f"{relative}: possible {name}")

    if findings:
        print("Secret regression check failed:")
        for finding in findings:
            print(f"- {finding}")
        return 1
    print("Secret regression check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
