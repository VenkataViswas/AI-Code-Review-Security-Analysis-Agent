import ast
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

def detect_language(code_content: str, filename: str = "") -> str:
    if filename.lower().endswith(".java"):
        return "Java"
    if filename.lower().endswith(".py"):
        return "Python"

    java_markers = (r"\bpublic\s+class\b", r"\bSystem\.out\.", r"\bpublic\s+static\s+void\s+main\b",
                    r"\bimport\s+java\.")
    if any(re.search(pattern, code_content) for pattern in java_markers):
        return "Java"
    return "Python"


def check_python(source: str):
    try:
        ast.parse(source)
        return {"ok": True, "title": "No syntax errors found", "details": "Python parsed successfully.", "items": []}
    except SyntaxError as e:
        item = f"Line {e.lineno or '?'}: {e.msg}"
        if e.text:
            item += f"\n    {e.text.rstrip()}"
            if e.offset:
                item += "\n    " + " " * (e.offset - 1) + "^"
        return {"ok": False, "title": "Syntax error found", "details": str(e), "items": [item]}


def check_java(source: str):
    javac = shutil.which("javac")
    if not source.strip():
        return {"ok": False, "title": "Empty input", "details": "Please paste Java code or upload a .java file.",
                "items": []}

    if not javac:
        issues = []
        if source.count("{") != source.count("}"):
            issues.append(f"Brace count mismatch: {source.count('{')} opening vs {source.count('}')} closing braces.")
        if source.count("(") != source.count(")"):
            issues.append(
                f"Parenthesis count mismatch: {source.count('(')} opening vs {source.count(')')} closing parentheses.")
        return {
            "ok": not issues,
            "title": "Basic checks passed" if not issues else "Potential syntax issue found",
            "details": "Java compiler (javac) is not installed. Performing basic delimiter check only.",
            "items": issues
        }

    with tempfile.TemporaryDirectory() as tmp:
        match = re.search(r"\bpublic\s+(?:final\s+|abstract\s+)?class\s+(\w+)", source)
        filename = (match.group(1) if match else "Main") + ".java"
        filepath = Path(tmp) / filename
        filepath.write_text(source, encoding="utf-8")

        try:
            proc = subprocess.run([javac, "-Xlint:all", str(filepath)], capture_output=True, text=True, timeout=20)
            output = (proc.stderr or proc.stdout).strip()
            if proc.returncode == 0:
                return {"ok": True, "title": "No compilation errors found",
                        "details": "javac compiled the source successfully.", "items": [output] if output else []}
            return {"ok": False, "title": "Compilation error found",
                    "details": "javac reported an error. Review the compiler output below.",
                    "items": [output or "Compilation failed without diagnostic output."]}
        except subprocess.TimeoutExpired:
            return {"ok": False, "title": "Check timed out", "details": "Compilation took too long and was stopped.",
                    "items": []}
