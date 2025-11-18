"""Command-line tool for validating HTML+CSS assignment submissions."""

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from zipfile import BadZipFile, ZipFile

ASSIGNMENT_NAME = "hw1"
CSS_LINK_PATTERN = re.compile(r"<link[^>]+href=\"[^\"]+\.css\"", re.IGNORECASE)


def parse_args():
    """Parse and validate command-line arguments."""
    if len(sys.argv) != 3:
        script = Path(sys.argv[0]).name
        sys.stderr.write(
            f"Usage: python {script} <submissions_dir> <reports_dir>\n"
        )
        sys.exit(1)

    submissions_dir = Path(sys.argv[1]).expanduser().resolve()
    reports_dir = Path(sys.argv[2]).expanduser().resolve()

    if not submissions_dir.exists() or not submissions_dir.is_dir():
        sys.stderr.write(
            f"Submissions directory does not exist or is not a directory: {submissions_dir}\n"
        )
        sys.exit(1)

    reports_dir.mkdir(parents=True, exist_ok=True)
    return submissions_dir, reports_dir


def _has_css_link(content):
    """Return True if the HTML content includes a <link> tag referencing a CSS file."""
    return bool(CSS_LINK_PATTERN.search(content))


def _check_basic_html_structure(content):
    """
    Perform basic checks on HTML structure:
    - <html>, </html>, <head>, </head>, <body>, </body> are present
    - They appear in a reasonable order: html > head > body
    Returns a list of issues (strings).
    """
    issues = []
    lowered = content.lower()

    # Check presence of open/close tags
    for tag in ("html", "head", "body"):
        if f"<{tag}" not in lowered:
            issues.append(f"index.html is missing <{tag}> tag.")
        if f"</{tag}>" not in lowered:
            issues.append(f"index.html is missing </{tag}> closing tag.")

    # If any are missing, skip order check
    def find_tag_pos(name, closing=False):
        if closing:
            return lowered.find(f"</{name}>")
        return lowered.find(f"<{name}")

    positions = {
        "html_open": find_tag_pos("html"),
        "html_close": find_tag_pos("html", closing=True),
        "head_open": find_tag_pos("head"),
        "head_close": find_tag_pos("head", closing=True),
        "body_open": find_tag_pos("body"),
        "body_close": find_tag_pos("body", closing=True),
    }

    if all(pos != -1 for pos in positions.values()):
        if not (
            positions["html_open"]
            < positions["head_open"]
            < positions["head_close"]
            < positions["body_open"]
            < positions["body_close"]
            < positions["html_close"]
        ):
            issues.append(
                "index.html has an unexpected order of <html>, <head>, and <body> tags."
            )

    return issues


class HTMLStructureValidator(HTMLParser):
    """
    Simple HTML tag-balance checker.
    - Ensures non-void tags are properly opened/closed.
    - Collects mismatches and unclosed tags as issues.
    """

    VOID_TAGS = {
        "area", "base", "br", "col", "embed", "hr", "img",
        "input", "link", "meta", "param", "source", "track", "wbr"
    }

    def __init__(self):
        super().__init__()
        self.stack = []
        self.issues = []

    def handle_starttag(self, tag, attrs):
        if tag not in self.VOID_TAGS:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        # Self-closing tag, nothing to push
        pass

    def handle_endtag(self, tag):
        if tag in self.VOID_TAGS:
            # Void tags should not have end tags, but HTMLParser is permissive.
            # We'll just ignore this rather than complain.
            return

        if not self.stack:
            self.issues.append(f"Unexpected closing tag </{tag}>.")
            return

        expected = self.stack.pop()
        if expected != tag:
            self.issues.append(
                f"Mismatched closing tag </{tag}> (expected </{expected}>)."
            )

    def finalize(self):
        # Any tags left on the stack are unclosed
        for tag in self.stack:
            self.issues.append(f"Unclosed tag <{tag}>.")


def _check_tag_balance(content):
    """
    Use HTMLStructureValidator to detect unclosed/mismatched tags.
    Returns a list of issues.
    """
    parser = HTMLStructureValidator()
    try:
        parser.feed(content)
        parser.close()
    except Exception:
        # If parsing itself fails, note that
        parser.issues.append("HTML parsing error (possibly malformed tags).")
    parser.finalize()
    return parser.issues


def check_zip_file(zip_path):
    """Inspect a single ZIP file and return its report dictionary."""
    filename = zip_path.name
    issues = []

    # We now ignore filename pattern; student_id is unknown
    student_id = None

    index_content = None

    try:
        with ZipFile(zip_path, "r") as archive:
            names = archive.namelist()
            name_set = set(names)
            index_present = "index.html" in name_set
            style_present = "style.css" in name_set
            css_style_present = "css/style.css" in name_set

            for name in names:
                if name.lower().endswith(".zip"):
                    issues.append(f"Nested zip found: {name}")

            if not index_present:
                issues.append("No index.html found at zip root.")
            else:
                try:
                    with archive.open("index.html") as html_file:
                        index_content = html_file.read().decode("utf-8", errors="ignore")
                except KeyError:
                    issues.append("Could not read index.html from the zip archive.")
                    index_content = None

            if not (style_present or css_style_present):
                issues.append(
                    "No style.css found. Expected style.css at root or css/style.css."
                )
    except (FileNotFoundError, BadZipFile, OSError):
        issues.append("Could not open zip file (corrupted or invalid).")

    if index_content is not None:
        # Basic structure and tag closure checks
        issues.extend(_check_basic_html_structure(index_content))
        issues.extend(_check_tag_balance(index_content))

        # Check for CSS link
        if not _has_css_link(index_content):
            issues.append("index.html does not link to a CSS file.")

    report = {
        "student_id": student_id,
        "filename": filename,
        "assignment": ASSIGNMENT_NAME,
        "format_ok": len(issues) == 0,
        "format_issues": issues,
    }
    return report


def main():
    """Entry point for the script."""
    submissions_dir, reports_dir = parse_args()

    for zip_path in sorted(submissions_dir.iterdir()):
        if not zip_path.is_file() or zip_path.suffix.lower() != ".zip":
            continue
        report = check_zip_file(zip_path)
        output_path = reports_dir / f"{zip_path.stem}.json"
        with output_path.open("w", encoding="utf-8") as report_file:
            json.dump(report, report_file, indent=2)
            report_file.write("\n")


if __name__ == "__main__":
    main()
