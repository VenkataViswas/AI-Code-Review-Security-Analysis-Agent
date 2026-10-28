
from crsa_agent.state import MessageState
from crsa_agent.agent.security_analysis.chain import security_analysis_chain

from log.logger import (
    log_header,
    log_info,
    log_success,
    log_error,
)


def security_analysis_node(state: MessageState) -> dict:
    log_header("Security Vulnerability Agent")
    log_info(f"Scanning {state['language']} source code...")

    try:
        result = security_analysis_chain.invoke({
            "code": state["code"],
            "language": state["language"],
        })

        findings = [
            finding.model_dump(mode="json")
            for finding in result.findings
        ]

        log_success(
            f"Security analysis completed: {len(findings)} finding(s)."
        )

        return {"security_findings": findings}

    except Exception as exc:
        log_error(f"Security analysis failed: {exc}")
        raise
