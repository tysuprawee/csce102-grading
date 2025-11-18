"""Command-line tool for validating HTML+CSS assignment submissions."""

import json
import re
import sys
from pathlib import Path
from zipfile import BadZipFile, ZipFile

ASSIGNMENT_NAME = "hw1"
FILENAME_PATTERN = re.compile(r"^(\d{8})_" + ASSIGNMENT_NAME + r"\.zip$")


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


def _has_required_html_tags(content):
    """Return True if the HTML content includes <html>, <head>, and <body> tags."""
    lowered = content.lower()
    return all(tag in lowered for tag in ("<html", "<head", "<body"))


def _has_css_link(content):
    """Return True if the HTML content includes a <link> tag referencing a CSS file."""
    link_pattern = re.compile(r"<link[^>]+href=\"[^\"]+\.css\"", re.IGNORECASE)
    return bool(link_pattern.search(content))


def check_zip_file(zip_path):
    """Inspect a single ZIP file and return its report dictionary."""
    filename = zip_path.name
    issues = []
    student_id = None

    match = FILENAME_PATTERN.match(filename)
    if match:
        student_id = match.group(1)
    else:
        issues.append("Filename does not match expected pattern <studentID>_hw1.zip.")

    index_content = None

    try:
        with ZipFile(zip_path, "r") as archive:
            names = archive.namelist()
            index_present = "index.html" in names
            style_present = "style.css" in names
            css_style_present = "css/style.css" in names

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
        if not _has_required_html_tags(index_content):
            issues.append(
                "index.html does not appear to contain <html>, <head>, and <body> tags."
            )
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
