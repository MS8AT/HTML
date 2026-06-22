#!/usr/bin/env python3
"""Check local site links, images, CSS urls, and JSON asset references."""

from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


PROJECT_ROOT = Path(__file__).resolve().parents[2]
IGNORE_DIRS = {".git", ".claude", "_project", "__pycache__"}
SKIP_PREFIXES = (
    "http://",
    "https://",
    "mailto:",
    "tel:",
    "javascript:",
    "data:",
    "#",
    "//",
)
ASSET_EXTENSIONS = {
    ".html",
    ".css",
    ".js",
    ".json",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
    ".svg",
    ".pdf",
    ".mp4",
    ".webm",
    ".ico",
}


class RefParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.refs: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if not value:
                continue
            attr = name.lower()
            if attr in {"href", "src", "poster", "data-src"}:
                self.refs.append((attr, value))
            elif attr == "srcset":
                for part in value.split(","):
                    url = part.strip().split(" ")[0]
                    if url:
                        self.refs.append(("srcset", url))


def is_ignored(path: Path) -> bool:
    try:
        rel_parts = path.relative_to(PROJECT_ROOT).parts
    except ValueError:
        return True
    return any(part in IGNORE_DIRS for part in rel_parts)


def iter_files(pattern: str) -> list[Path]:
    return sorted(path for path in PROJECT_ROOT.rglob(pattern) if path.is_file() and not is_ignored(path))


def should_skip(url: str) -> bool:
    value = url.strip()
    return not value or value.startswith(SKIP_PREFIXES)


def resolve_url(base_file: Path, url: str) -> Path | None:
    value = url.strip()
    if should_skip(value):
        return None

    parsed = urlsplit(value)
    path = unquote(parsed.path)
    if not path:
        return None

    if path.startswith("/"):
        return (PROJECT_ROOT / path.lstrip("/")).resolve()
    return (base_file.parent / path).resolve()


def add_ref(
    source: Path,
    kind: str,
    url: str,
    broken: list[tuple[str, str, str]],
    referenced: set[Path],
) -> None:
    target = resolve_url(source, url)
    if target is None:
        return

    referenced.add(target)
    if not target.exists():
        broken.append((source.relative_to(PROJECT_ROOT).as_posix(), kind, url))


def check_html(broken: list[tuple[str, str, str]], referenced: set[Path]) -> None:
    for html_file in iter_files("*.html"):
        text = html_file.read_text(encoding="utf-8", errors="replace")
        parser = RefParser()
        parser.feed(text)
        for kind, url in parser.refs:
            add_ref(html_file, kind, url, broken, referenced)
        check_css_urls(html_file, text, broken, referenced)


def check_css_urls(
    source_file: Path,
    text: str,
    broken: list[tuple[str, str, str]],
    referenced: set[Path],
) -> None:
    for match in re.finditer(r"url\(([^)]+)\)", text):
        url = match.group(1).strip("\"' ")
        add_ref(source_file, "css-url", url, broken, referenced)


def check_css(broken: list[tuple[str, str, str]], referenced: set[Path]) -> None:
    for css_file in iter_files("*.css"):
        text = css_file.read_text(encoding="utf-8", errors="replace")
        check_css_urls(css_file, text, broken, referenced)


def collect_json_strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        strings: list[str] = []
        for item in value:
            strings.extend(collect_json_strings(item))
        return strings
    if isinstance(value, dict):
        strings = []
        for item in value.values():
            strings.extend(collect_json_strings(item))
        return strings
    return []


def looks_like_local_asset(value: str) -> bool:
    if should_skip(value):
        return False
    path = urlsplit(value).path
    return Path(path).suffix.lower() in ASSET_EXTENSIONS


def check_json(broken: list[tuple[str, str, str]], referenced: set[Path]) -> None:
    for json_file in iter_files("*.json"):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as exc:
            broken.append((json_file.relative_to(PROJECT_ROOT).as_posix(), "json-parse", str(exc)))
            continue
        for value in collect_json_strings(data):
            if looks_like_local_asset(value):
                add_ref(json_file, "json-ref", value, broken, referenced)


def report_candidate_root_files() -> None:
    allowed_root_files = {
        ".gitattributes",
        ".gitignore",
        "index.html",
        "light-theme.css",
        "logo-future.jpg",
    }
    candidates = []
    for path in sorted(PROJECT_ROOT.iterdir()):
        if path.is_file() and path.name not in allowed_root_files and path.name != "Thumbs.db":
            candidates.append(path.name)

    if candidates:
        print("\nCandidate non-site files in root:")
        for name in candidates:
            print(f"  - {name}")


def main() -> int:
    broken: list[tuple[str, str, str]] = []
    referenced: set[Path] = set()

    check_html(broken, referenced)
    check_css(broken, referenced)
    check_json(broken, referenced)

    html_count = len(iter_files("*.html"))
    css_count = len(iter_files("*.css"))
    json_count = len(iter_files("*.json"))

    print("Site link check")
    print(f"Root: {PROJECT_ROOT}")
    print(f"HTML files: {html_count}")
    print(f"CSS files: {css_count}")
    print(f"JSON files: {json_count}")
    print(f"Local references checked: {len(referenced)}")

    if broken:
        print("\nBroken local references:")
        for source, kind, url in broken:
            print(f"  - {source} | {kind} | {url}")
        report_candidate_root_files()
        return 1

    print("\nOK: no broken local references found.")
    report_candidate_root_files()
    return 0


if __name__ == "__main__":
    sys.exit(main())
