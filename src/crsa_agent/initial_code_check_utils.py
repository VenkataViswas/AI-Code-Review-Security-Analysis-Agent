
import ast
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


def detect_language(code_content: str, filename: str = "") -> str:
    code = code_content.strip()

    if not code:
        return "Not detected"

    # Filename-based detection
    filename = filename.lower()

    if filename.endswith(".java"):
        return "Java"

    if filename.endswith(".py"):
        return "Python"

    # Strong Java indicators
    java_patterns = [
        r"^\s*package\s+[\w.]+\s*;",
        r"^\s*import\s+(?:static\s+)?(?:java|javax|org|com)\.[\w.*]+\s*;",
        r"\bpublic\s+(?:(?:abstract|final)\s+)?(?:class|interface|enum|record)\s+\w+",
        r"\bclass\s+\w+\s*\{",
        r"\bSystem\s*\.\s*out\s*\.\s*(?:print|println)",
        r"\bpublic\s+static\s+void\s+main\s*\(",
        r"\b(?:extends|implements)\s+\w+",
        r"\bnew\s+\w+\s*\(",
    ]

    if any(re.search(p, code, re.MULTILINE) for p in java_patterns):
        return "Java"

    # Strong Python indicators
    python_patterns = [
        r"^\s*def\s+\w+\s*\(",
        r"^\s*async\s+def\s+\w+\s*\(",
        r"^\s*class\s+\w+\s*:",
        r"^\s*(?:if|elif|else|for|while|try|except|finally|with)\b.*:",
        r"\bprint\s*\(",
        r"\bNone\b",
        r"\b(?:True|False)\b",
        r"\bself\b",
        r"^\s*from\s+\w+\s+import\b",
        r"^\s*import\s+\w+",
    ]

    if any(re.search(p, code, re.MULTILINE) for p in python_patterns):
        return "Python"

    return "Not detected"


def check_python(source: str):
    if not source.strip():
        return {
            "ok": False,
            "title": "Empty input",
            "details": "Please enter Python code.",
            "items": [],
        }

    try:
        ast.parse(source)

        return {
            "ok": True,
            "title": "No syntax errors found",
            "details": "Python syntax validation completed successfully.",
            "items": [],
        }

    except SyntaxError as e:
        item = f"Line {e.lineno or '?'}: {e.msg}"

        if e.text:
            item += f"\n    {e.text.rstrip()}"

            if e.offset:
                item += "\n    " + " " * (e.offset - 1) + "^"

        return {
            "ok": False,
            "title": "Python Syntax Error",
            "details": e.msg,
            "items": [item],
            "line_number": e.lineno,
            "snippet": e.text.strip() if e.text else "",
        }


def check_java(source: str):
    if not source.strip():
        return {
            "ok": False,
            "title": "Empty input",
            "details": "Please enter Java code.",
            "items": [],
        }

    javac = shutil.which("javac")

    # javac is required for complete Java syntax validation.
    if not javac:
        issues = []

        if source.count("{") != source.count("}"):
            issues.append("Opening and closing braces do not match.")

        if source.count("(") != source.count(")"):
            issues.append("Opening and closing parentheses do not match.")

        return {
            "ok": not issues,
            "title": (
                "Basic checks passed"
                if not issues
                else "Potential Java syntax issue"
            ),
            "details": (
                "javac is unavailable. Only basic delimiter checks "
                "were performed; Java syntax is not fully verified."
            ),
            "items": issues,
        }

    with tempfile.TemporaryDirectory() as tmp:
        # Match public top-level class/interface/enum/record name.
        match = re.search(
            r"\bpublic\s+(?:(?:abstract|final)\s+)?"
            r"(?:class|interface|enum|record)\s+(\w+)",
            source,
        )

        filename = (match.group(1) if match else "Main") + ".java"
        filepath = Path(tmp) / filename

        filepath.write_text(source, encoding="utf-8")

        try:
            proc = subprocess.run(
                [
                    javac,
                    "-proc:none",
                    "-Xlint:none",
                    "-d",
                    tmp,
                    str(filepath),
                ],
                capture_output=True,
                text=True,
                timeout=20,
            )

            output = (proc.stderr or proc.stdout).strip()

            if proc.returncode == 0:
                return {
                    "ok": True,
                    "title": "Java validation successful",
                    "details": "Java source compiled successfully.",
                    "items": [],
                }

            return {
                "ok": False,
                "title": "Java Compilation/Validation Error",
                "details": "javac reported an error. This may be a syntax, type, or dependency error.",
                "items": [output or "Compilation failed."],
            }

        except subprocess.TimeoutExpired:
            return {
                "ok": False,
                "title": "Java validation timed out",
                "details": "The compiler exceeded the 20-second limit.",
                "items": [],
            }

        except OSError as e:
            return {
                "ok": False,
                "title": "Java validation failed",
                "details": str(e),
                "items": [],
            }
