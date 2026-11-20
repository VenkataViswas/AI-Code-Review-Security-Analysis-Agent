import ast
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import streamlit as st

from ui.components.analysis_service import invoke_analysis_graph


def analyze_python_syntax(code: str):
    """Analyze Python syntax with exact line number, column pointer, and suggestion."""
    try:
        ast.parse(code)
        return True, None
    except SyntaxError as e:
        line_no = e.lineno or 1
        offset = e.offset or 1
        raw_text = (e.text or "").rstrip()
        msg = e.msg or "Invalid syntax"

        # Construct caret line
        caret_pos = max(0, offset - 1)
        caret_line = " " * caret_pos + "^"

        if raw_text:
            snippet = f"Line {line_no}: {raw_text}\n{' ' * (len(f'Line {line_no}: '))}{caret_line}\nSyntaxError: {msg}"
        else:
            snippet = f"Line {line_no}: SyntaxError: {msg}"

        # Tailored suggestion
        if "expected ':'" in msg:
            suggestion = f"Add a colon ':' at the end of the statement on line {line_no}."
        elif "unclosed" in msg or "parenthesis" in msg:
            suggestion = f"Check for an unclosed parenthesis ')' or bracket on or before line {line_no}."
        elif "indent" in msg:
            suggestion = f"Fix indentation alignment on line {line_no} (use consistent 4 spaces)."
        elif "EOL" in msg or "unterminated string" in msg:
            suggestion = f"Check for an unclosed string quote on line {line_no}."
        else:
            suggestion = f"Review the syntax structure around line {line_no}."

        return False, {
            "language": "Python",
            "title": f"Python Syntax Error (Line {line_no})",
            "line_number": line_no,
            "message": f"SyntaxError: {msg}",
            "code_line": raw_text,
            "snippet": snippet,
            "suggestion": suggestion,
        }


def analyze_java_syntax(code: str):
    """Validate Java syntax using javac, avoiding unreliable line-based checks."""

    if not code.strip():
        return False, {
            "language": "Java",
            "title": "Empty Input",
            "line_number": 1,
            "message": "No Java code provided.",
            "code_line": "",
            "snippet": "Empty source code.",
            "suggestion": "Paste or upload Java source code.",
        }

    javac = shutil.which("javac")

    # Compiler unavailable: do not falsely report syntax errors.
    # Allow CRSA analysis to continue.
    if not javac:
        return True, None

    lines = code.splitlines()

    # Detect public class/interface/enum/record for correct filename.
    match = re.search(
        r"\bpublic\s+(?:(?:abstract|final|sealed|non-sealed)\s+)*"
        r"(?:class|interface|enum|record)\s+(\w+)",
        code
    )

    class_name = match.group(1) if match else "Main"

    with tempfile.TemporaryDirectory() as tmp:
        file_path = Path(tmp) / f"{class_name}.java"
        file_path.write_text(code, encoding="utf-8")

        try:
            proc = subprocess.run(
                [javac, "-Xlint:all", "-d", tmp, str(file_path)],
                capture_output=True,
                text=True,
                timeout=20
            )

            output = (proc.stderr or proc.stdout).strip()

            # Valid Java source
            if proc.returncode == 0:
                return True, None

            # javac invocation/environment failure is NOT a source syntax error
            if not output or "Usage: javac" in output:
                return True, None

            # Parse actual compiler diagnostic
            error_match = re.search(
                r"\.java:(\d+):\s*error:\s*(.+)",
                output
            )

            if error_match:
                line_no = int(error_match.group(1))
                error_message = error_match.group(2).strip()

                code_line = (
                    lines[line_no - 1]
                    if 1 <= line_no <= len(lines)
                    else ""
                )

                return False, {
                    "language": "Java",
                    "title": f"Java Syntax Error (Line {line_no})",
                    "line_number": line_no,
                    "message": error_message,
                    "code_line": code_line,
                    "snippet": output[:1000],
                    "suggestion": (
                        f"Review the Java compiler error on line {line_no}: "
                        f"{error_message}"
                    ),
                }

            # Unknown compiler failure: don't mislabel it as a syntax error
            return True, None

        except subprocess.TimeoutExpired:
            # Do not block analysis due to compiler timeout
            return True, None

        except Exception:
            # Compiler execution failure should not create false syntax errors
            return True, None

def validate_code(code: str, language: str):
    """Validate source code with high-precision syntax checking."""
    if not code or not code.strip():
        return False, {
            "language": language or "Code",
            "title": "Empty Code Submission",
            "line_number": 1,
            "message": "Please enter or upload source code before initiating analysis.",
            "code_line": "",
            "snippet": "No source code provided.",
            "suggestion": "Paste source code in the editor or select a benchmark preset above.",
        }

    lang = (language or "python").lower().strip()

    if lang == "python":
        return analyze_python_syntax(code)
    elif lang == "java":
        return analyze_java_syntax(code)
    else:
        return False, {
            "language": language,
            "title": "Unsupported Language",
            "line_number": 1,
            "message": f"Language '{language}' is not supported. Supported: Python and Java.",
            "code_line": "",
            "snippet": f"Detected language: {language}",
            "suggestion": "Please submit Python (.py) or Java (.java) source code.",
        }


def validate_and_analyze(code, language):
    """Validate syntax and run the multi-agent pipeline."""
    # Clear previous run results
    st.session_state.pop("analysis_result", None)
    st.session_state.pop("result", None)

    is_valid, error_info = validate_code(code, language)

    if not is_valid:
        # Save structured syntax error so input_panel can render it right at the editor!
        st.session_state["syntax_error"] = error_info
        st.rerun()
        return

    # Clear any previous syntax error
    st.session_state.pop("syntax_error", None)

    try:
        with st.spinner("🤖 Orchestrating Multi-Agent Pipeline: Code Analysis + OWASP Security Scan..."):
            analysis = invoke_analysis_graph(code, language)

            if analysis is None:
                st.session_state["syntax_error"] = {
                    "language": language,
                    "title": "Analysis Workflow Error",
                    "line_number": 1,
                    "message": "The multi-agent graph returned an empty result.",
                    "code_line": "",
                    "snippet": "No output from agent pipeline.",
                    "suggestion": "Check API keys or try a benchmark preset.",
                }
                st.rerun()
                return

            st.session_state["analysis_result"] = analysis
            st.session_state["submitted_code"] = code
            st.session_state["submitted_language"] = language

            st.switch_page("pages/result_page.py")

    except Exception as exc:
        st.session_state["syntax_error"] = {
            "language": language,
            "title": "Pipeline Execution Error",
            "line_number": 1,
            "message": str(exc),
            "code_line": "",
            "snippet": f"Exception: {exc}",
            "suggestion": "Review error log and verify input source code.",
        }
        st.rerun()
