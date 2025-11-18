CSCE 102 auto-grading
======================

`check_format.py` is a lightweight validator for CSCE 102 HTML/CSS homework ZIP
submissions. It inspects each archive directly (no extraction required) and
produces JSON reports describing every issue it finds.

## Requirements

* Python 3.8+
* Standard library modules only (no third-party dependencies)

## Usage

1. Place all student ZIPs inside a folder, e.g. `submissions/`.
2. Run the checker with the submissions folder and an output folder:

   ```bash
   python check_format.py submissions/ reports/
   ```

   The reports folder will be created automatically if it does not exist.
3. Inspect the generated JSON files (one per submission) inside the reports
   directory. Each file mirrors the ZIP name but uses a `.json` extension.

## What the checker validates

* Filename pattern: `########_hw1.zip` (8-digit student ID)
* Required files at the archive root:
  * `index.html`
  * Either `style.css` or `css/style.css`
* No nested ZIPs
* `index.html` contains `<html>`, `<head>`, and `<body>` tags
* `index.html` links to a CSS file via a `<link ... href="*.css">` tag

All violations are reported in the `format_issues` list, and `format_ok` is set
to `false` when at least one issue is present.

## Performance tips

The script streams each ZIP file once using `zipfile.ZipFile`, caches filename
membership lookups, and only reads `index.html` when it exists. This keeps the
checker fast even when processing large batches of submissions. To maximize
throughput, run it from local storage rather than a network drive.
