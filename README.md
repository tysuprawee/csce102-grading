# CSCE 102 Auto-Grading

Lightweight HTML/CSS Submission Validator

`check_format.py` is a lightweight validator for CSCE 102 HTML/CSS
homework ZIP submissions. It inspects each archive directly (no
extraction required) and produces JSON reports describing every issue it
finds.

## Requirements

-   Python 3.8+
-   Standard library modules only (no third-party dependencies)

## Usage

1.  Place all student ZIP files inside a folder, e.g. `submissions/`.

2.  Run the checker with the submissions folder and an output folder:

    ``` bash
    python check_format.py submissions/ reports/
    ```

    The `reports/` folder will be created automatically if it does not
    exist.

3.  Inspect the generated JSON reports inside the output directory.\
    Each report has the same name as the ZIP file, but with a `.json`
    extension.

## What the checker validates

### ZIP-level checks

-   The file is a valid `.zip` archive.
-   ZIP contains **no nested ZIPs**.
-   Required files exist:
    -   `index.html` at the archive root
    -   `style.css` **OR** `css/style.css`

### HTML structure checks

The validator performs strict inspections of `index.html`:

-   Required structural tags must exist *and* be properly closed:
    -   `<html>` + `</html>`
    -   `<head>` + `</head>`
    -   `<body>` + `</body>`
-   Tags must appear in the correct logical order:\
    **`<html>` → `<head>` → `<body>`**
-   Proper tag nesting and closure validation using an internal HTML
    parser:
    -   Detects unclosed tags
    -   Detects mismatched tags
    -   Detects unexpected closing tags
-   HTML must include a valid CSS reference using:\
    `<link ... href="*.css">`

### Output Format

Each JSON report contains:

``` json
{
  "student_id": null,
  "filename": "example.zip",
  "assignment": "hw1",
  "format_ok": false,
  "format_issues": [
    "example issue message"
  ]
}
```

-   `format_ok` is `true` only when **no issues** are found.
-   `student_id` remains `null` because filename pattern enforcement is
    disabled.

## Performance Tips

-   ZIP contents are streamed directly using Python's `zipfile` module
    --- no extraction required.
-   The script reads `index.html` only when present.
-   It is fast enough for grading large batches.
-   For maximum performance, keep the submissions on local storage, not
    a network drive.
