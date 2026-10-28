
from crsa_agent.state import MessageState
from crsa_agent.agent.code_analysis.chain import code_analysis_chain

from log.logger import (
    log_header,
    log_info,
    log_success,
    log_error,
)


def code_analysis_node(state: MessageState) -> dict:
    log_header("Code Analysis Agent")
    log_info(f"Analyzing {state['language']} source code...")

    try:
        result = code_analysis_chain.invoke({
            "code": state["code"],
            "language": state["language"],
        })

        findings = [
            finding.model_dump(mode="json")
            for finding in result.findings
        ]

        log_success(
            f"Code analysis completed: {len(findings)} finding(s)."
        )

        return {"code_findings": findings}

    except Exception as exc:
        log_error(f"Code analysis failed: {exc}")
        raise
