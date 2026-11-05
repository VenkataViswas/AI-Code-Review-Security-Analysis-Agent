
from crsa_agent.state import MessageState
from crsa_agent.agent.remediation.chain import remediation_chain

from log.logger import (
    log_header,
    log_info,
    log_success,
    log_error,
)


def remediation_node(state: MessageState) -> dict:
    log_header("Remediation Agent")
    log_info(
        f"Generating fixes for "
        f"{len(state['unified_findings'])} finding(s)..."
    )

    if not state["unified_findings"]:
        log_success("No findings to remediate.")

        return {"remediation_findings": []}

    try:
        result = remediation_chain.invoke({
            "code": state["code"],
            "language": state["language"],
            "findings": str(state["unified_findings"]),
        })

        remediations = [
            item.model_dump(mode="json")
            for item in result.remediations
        ]

        log_success(
            f"Generated {len(remediations)} remediation item(s)."
        )

        return {"remediation_findings": remediations}

    except Exception as exc:
        log_error(f"Remediation generation failed: {exc}")
        raise
