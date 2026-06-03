import argparse
import re
from pathlib import Path


DEFAULT_PATTERNS = [
    r"sk-[A-Za-z0-9_-]{10,}",
    r"ghp_[A-Za-z0-9_]{20,}",
    r"github_pat_[A-Za-z0-9_]{20,}",
    r"glpat-[A-Za-z0-9_-]{20,}",
    r"AKIA[0-9A-Z]{16}",
    r"ASIA[0-9A-Z]{16}",
    r"-----BEGIN (?:RSA |DSA |EC |OPENSSH |PGP )?PRIVATE KEY-----",
    r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}",
    r"(?i)api[_-]?key\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{12,}",
    r"(?i)secret\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{12,}",
    r"(?i)password\s*[:=]\s*['\"]?.{6,}",
    r"(?i)token\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{12,}",
    r"C:\\Users\\[\w .-]{1,80}",
    r"/Users/[\w .-]{1,80}",
]

PLACEHOLDER_PATTERNS = [
    r"(?i)OPENAI_API_KEY\s*=\s*(replace|your|changeme)",
    r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*(replace|your|changeme|todo)",
]

SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".mypy_cache", ".pytest_cache"}
SKIP_SUFFIXES = {
    ".7z",
    ".bmp",
    ".dll",
    ".exe",
    ".gif",
    ".ico",
    ".jpg",
    ".jpeg",
    ".pdf",
    ".png",
    ".pyc",
    ".rar",
    ".tar",
    ".webp",
    ".zip",
}
SENSITIVE_NAMES = {
    ".env",
    ".env.development",
    ".env.local",
    ".env.production",
    ".npmrc",
    ".pypirc",
    ".venv",
    "__pycache__",
    "credentials.json",
    "id_ed25519",
    "id_rsa",
    "service-account.json",
}
SENSITIVE_SUFFIXES = {".key", ".pem", ".p12", ".pfx"}


def has_skipped_part(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def iter_files(root: Path):
    for path in root.rglob("*"):
        if has_skipped_part(path):
            continue
        if path.is_file() and path.suffix.lower() not in SKIP_SUFFIXES:
            yield path


def compile_patterns(patterns):
    regexes = []
    for pattern in patterns:
        try:
            regexes.append((pattern, re.compile(pattern)))
        except re.error as exc:
            print(f"INVALID_PATTERN\t{pattern}\t{exc}")
            return None
    return regexes


def redact_line(line: str, regex: re.Pattern) -> str:
    redacted = regex.sub("[REDACTED]", line.strip())
    return redacted[:240]


def scan(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    if not root.exists():
        print(f"ROOT_NOT_FOUND\t{root}")
        return 2

    patterns = list(DEFAULT_PATTERNS)
    if args.fail_on_placeholder:
        patterns.extend(PLACEHOLDER_PATTERNS)
    patterns.extend(args.extra_pattern or [])

    sensitive_names = {name.lower() for name in SENSITIVE_NAMES}
    sensitive_names.update(name.lower() for name in (args.extra_sensitive_name or []))

    regexes = compile_patterns(patterns)
    if regexes is None:
        return 2

    hits = []
    bad_files = []

    for path in root.rglob("*"):
        if ".git" in path.parts or has_skipped_part(path):
            continue
        name = path.name.lower()
        if name in sensitive_names or path.suffix.lower() in SENSITIVE_SUFFIXES:
            bad_files.append(path)

    for path in iter_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        rel = path.relative_to(root)
        for line_no, line in enumerate(text.splitlines(), start=1):
            for pattern, regex in regexes:
                if regex.search(line):
                    hits.append((pattern, rel, line_no, redact_line(line, regex)))

    if not hits and not bad_files:
        print("DESENSITIZE_CHECK=PASS")
        return 0

    print("DESENSITIZE_CHECK=FAIL")
    for path in bad_files:
        print(f"SENSITIVE_PATH\t{path.relative_to(root)}")
    for pattern, rel, line_no, line in hits:
        print(f"MATCH\t{rel}:{line_no}\t{pattern}\t{line}")
    return 1


def tree(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    if not root.exists():
        print(f"ROOT_NOT_FOUND\t{root}")
        return 2

    for path in sorted(root.rglob("*")):
        if ".git" in path.parts:
            continue
        rel = path.relative_to(root)
        suffix = "/" if path.is_dir() else ""
        print(f"{rel}{suffix}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Release desensitization and completeness checks.")
    sub = parser.add_subparsers(dest="command", required=True)

    scan_p = sub.add_parser("scan")
    scan_p.add_argument("--root", required=True)
    scan_p.add_argument("--extra-pattern", action="append")
    scan_p.add_argument("--extra-sensitive-name", action="append")
    scan_p.add_argument("--fail-on-placeholder", action="store_true")
    scan_p.set_defaults(func=scan)

    tree_p = sub.add_parser("tree")
    tree_p.add_argument("--root", required=True)
    tree_p.set_defaults(func=tree)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
