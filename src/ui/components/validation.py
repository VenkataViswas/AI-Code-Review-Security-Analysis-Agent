
import streamlit as st

from crsa_agent.initial_code_check_utils import (
    check_python,
    check_java,
)

from ui.components.analysis_service import invoke_analysis_graph


def _interpret_validation_result(result):
    """Normalize common validation utility return formats."""

    if isinstance(result, bool):
        return result, None if result else "Code validation failed."

    if isinstance(result, tuple):
        if result and isinstance(result[0], bool):
            message = result[1] if len(result) > 1 else None
            return result[0], str(message) if message else None

        if result:
            return _interpret_validation_result(result[0])

    if isinstance(result, dict):
        for key in ("ok", "valid", "success"):
            if key in result:
                valid = bool(result[key])
                message = (
                    result.get("error")
                    or result.get("message")
                    or result.get("details")
                )
                return valid, str(message) if message else None

    if isinstance(result, list):
        return (
            not result,
            "; ".join(map(str, result)) if result else None,
        )

    if result is None:
        return True, None

    return result is not False, None


def validate_code(code: str, language: str):
    """Validate Python or Java source code."""

    if not code or not code.strip():
        return False, "Please provide code for analysis."

    if not language:
        return False, "Unable to detect the programming language."

    language = language.lower().strip()

    try:
        if language == "python":
            result = check_python(code)

        elif language == "java":
            result = check_java(code)

        else:
            return False, "Only Python and Java are supported."

        return _interpret_validation_result(result)

    except Exception as exc:
        return False, str(exc)


def validate_and_analyze(code, language):

    # Clear previous results before starting a new analysis.
    st.session_state.pop("analysis_result", None)
    st.session_state.pop("result", None)

    is_valid, error_message = validate_code(code, language)

    if not is_valid:
        st.error(error_message or "Code validation failed.")
        return

    try:
        with st.spinner("Validating code and running AI analysis..."):

            # Run the LangGraph workflow.
            analysis = invoke_analysis_graph(code, language)

            if analysis is None:
                st.error("The analysis graph returned no result.")
                return

            # Save all required data.
            st.session_state["analysis_result"] = analysis
            st.session_state["submitted_code"] = code
            st.session_state["submitted_language"] = language

            st.session_state["validation_status"] = {
                "ok": True,
                "title": "Validation passed",
                "details": "Code syntax or compilation validation completed successfully.",
                "items": [],
            }

            # Navigate after successful analysis.
            st.switch_page("pages/result_page.py")

    except Exception as exc:
        st.error("Code analysis failed.")
        st.exception(exc)
