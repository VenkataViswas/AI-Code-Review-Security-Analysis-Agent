
from crsa_agent.state import MessageState
from crsa_agent.agent.pr_summary.chain import pr_summary_chain

from log.logger import (
    log_header,
    log_info,
    log_success,
    log_error,
)


def pr_summary_node(state: MessageState) -> dict:
    log_header("PR Summary Agent")

    log_info("Compiling unified findings and remediation results...")

    try:
        result = pr_summary_chain.invoke({
            "unified_findings": state.get("unified_findings", []),
            "remediation_findings": state.get("remediation_findings", []),
        })

        summary = result.summary.model_dump(mode="json")

        log_success(
            "PR Summary generated successfully."
        )

        log_info(
            f"Review Status: {summary['review_status']}"
        )

        log_info(
            f"Total Findings: {summary['total_findings']}"
        )

        log_info(
            f"Merge Recommendation: {summary['merge_recommendation']}"
        )

        return {
            "pr_summary": summary
        }

    except Exception as exc:
        log_error(f"PR Summary generation failed: {exc}")
        raise
