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
    """Analyze Java syntax including delimiter balance, semicolons, and javac diagnostics."""
    lines = code.splitlines()

    # 1. Delimiter balance check
    open_braces = code.count("{")
    close_braces = code.count("}")
    if open_braces != close_braces:
        diff = abs(open_braces - close_braces)
        missing_type = "closing '}'" if open_braces > close_braces else "opening '{'"
        return False, {
            "language": "Java",
            "title": "Java Syntax Error: Unbalanced Braces",
            "line_number": len(lines),
            "message": f"Brace count mismatch: {open_braces} opening '{{' vs {close_braces} closing '}}' (Missing {diff} {missing_type}).",
            "code_line": "Ensure all class and method bodies are properly closed.",
            "snippet": f"Total '{{': {open_braces} | Total '}}': {close_braces}",
            "suggestion": f"Check class and method declarations for missing {missing_type}.",
        }

    open_parens = code.count("(")
    close_parens = code.count(")")
    if open_parens != close_parens:
        diff = abs(open_parens - close_parens)
        missing_type = "closing ')'" if open_parens > close_parens else "opening '('"
        return False, {
            "language": "Java",
            "title": "Java Syntax Error: Unbalanced Parentheses",
            "line_number": len(lines),
            "message": f"Parenthesis mismatch: {open_parens} opening '(' vs {close_parens} closing ')' (Missing {diff} {missing_type}).",
            "code_line": "Ensure all method signatures, conditions, and calls have matching parentheses.",
            "snippet": f"Total '(': {open_parens} | Total ')': {close_parens}",
            "suggestion": f"Check expressions and parameter lists for missing {missing_type}.",
        }

    # 2. Missing semicolon checks on common statements
    for idx, raw_line in enumerate(lines, 1):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
            continue
        if stripped.endswith("{") or stripped.endswith("}") or stripped.endswith(":"):
            continue

        if stripped.startswith("package ") or stripped.startswith("import "):
            if not stripped.endswith(";"):
                return False, {
                    "language": "Java",
                    "title": f"Java Syntax Error (Line {idx})",
                    "line_number": idx,
                    "message": "Missing semicolon ';' at end of import/package declaration.",
                    "code_line": raw_line,
                    "snippet": f"Line {idx}: {raw_line}\n{' ' * len(f'Line {idx}: {raw_line}')}^\nSyntaxError: missing ';'",
                    "suggestion": f"Add a semicolon ';' to terminate line {idx}.",
                }

        # Statement patterns that strictly require semicolon
        stmt_keywords = ("return ", "System.out.println", "System.out.print", "throw ", "break", "continue")
        if any(stripped.startswith(k) for k in stmt_keywords):
            if not stripped.endswith(";"):
                return False, {
                    "language": "Java",
                    "title": f"Java Syntax Error (Line {idx})",
                    "line_number": idx,
                    "message": "Missing semicolon ';' at end of statement.",
                    "code_line": raw_line,
                    "snippet": f"Line {idx}: {raw_line}\n{' ' * len(f'Line {idx}: {raw_line}')}^\nSyntaxError: missing ';'",
                    "suggestion": f"Add a semicolon ';' to terminate statement on line {idx}.",
                }

    # 3. If javac is installed and operational, check compiler diagnostics
    javac = shutil.which("javac")
    if javac:
        try:
            with tempfile.TemporaryDirectory() as tmp:
                match = re.search(r"\bpublic\s+(?:final\s+|abstract\s+)?class\s+(\w+)", code)
                class_name = match.group(1) if match else "Main"
                file_path = Path(tmp) / f"{class_name}.java"
                file_path.write_text(code, encoding="utf-8")

                proc = subprocess.run(
                    [javac, "-Xlint:all", str(file_path)],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                output = (proc.stderr or proc.stdout).strip()

                # If javac succeeded, it is valid
                if proc.returncode == 0:
                    return True, None

                # If javac failed with diagnostic output, parse line number & error message
                if output and "without diagnostic output" not in output:
                    line_match = re.search(rf"{class_name}\.java:(\d+):\s*error:\s*(.+)", output)
                    line_no = int(line_match.group(1)) if line_match else 1
                    err_msg = line_match.group(2) if line_match else "Java compilation error"

                    return False, {
                        "language": "Java",
                        "title": f"Java Compilation Error (Line {line_no})",
                        "line_number": line_no,
                        "message": err_msg,
                        "code_line": lines[line_no - 1] if line_no <= len(lines) else "",
                        "snippet": output[:400],
                        "suggestion": f"Review javac compiler diagnostics on line {line_no}.",
                    }
        except Exception:
            # Fall back to delimiter verification if sandbox restricts javac execution
            pass

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
