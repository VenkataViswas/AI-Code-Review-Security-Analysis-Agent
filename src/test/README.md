# AI Code Review & Security Analysis Agent — Test Dataset

## Contents
- `test/files/`: 20 Python (`.py`) files and 20 Java (`.java`) files.
- `test/manifest.csv`: a list of files, languages, categories, and intended test purpose.

## Test coverage per language
- 2 clean baseline files
- 4 syntax/compilation-error files
- 4 code-quality-only files
- 4 security-only files
- 6 mixed code-quality + security files

## Important notes
- Files named `*_syntax_*` intentionally contain syntax or compilation errors. They are designed to test whether the application detects and reports invalid source code gracefully.
- Other files include intentionally insecure patterns or maintainability issues for defensive code-review testing.
- The credentials and keys in examples are dummy placeholders, not real secrets.
- Do not run vulnerable samples in production or against real systems. Treat them as static-analysis fixtures.
- Java examples use common language syntax; the `java_syntax_*` files intentionally include compile-time errors.
- Static-analysis LLM results can vary. The manifest describes intended issues, not a guarantee that an LLM will report every issue correctly.
