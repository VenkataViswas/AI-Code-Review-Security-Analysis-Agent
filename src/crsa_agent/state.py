
from enum import Enum

from pydantic import BaseModel, Field
from langgraph.graph import MessagesState


# ==================================================
# ENUMS
# ==================================================

class Severity(str, Enum):
    INFORMATIONAL = "INFORMATIONAL"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class PRReviewStatus(str, Enum):
    APPROVED = "APPROVED"
    APPROVED_WITH_SUGGESTIONS = "APPROVED_WITH_SUGGESTIONS"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"


# ==================================================
# FINDING MODELS
# ==================================================

class Finding(BaseModel):
    category: str = Field(
        description=(
            "Type of issue detected, such as Code Smell, Complexity, "
            "Design Issue, Best Practice Violation, SQL Injection, "
            "Cross-Site Scripting (XSS), Hardcoded Secret, "
            "Broken Access Control, or Input Validation."
        )
    )

    issue: str = Field(
        description="Short title describing the detected issue."
    )

    severity: Severity = Field(
        description="Severity: INFORMATIONAL, LOW, MEDIUM, HIGH, or CRITICAL."
    )

    line_number: int | None = Field(
        default=None,
        description="Affected source line, if identifiable."
    )

    description: str = Field(
        description="Explanation of the issue and its potential impact."
    )


class AgentResult(BaseModel):
    findings: list[Finding] = Field(
        default_factory=list,
        description="Findings identified by an analysis agent."
    )


# ==================================================
# REMEDIATION MODELS
# ==================================================

class RemediationItem(BaseModel):
    issue: str = Field(
        description="Issue being remediated."
    )

    severity: Severity = Field(
        description="Severity of the original finding."
    )

    line_number: int | None = Field(
        default=None,
        description="Original affected source line, if known."
    )

    fix_recommendation: str = Field(
        description="Specific steps to fix the identified issue."
    )

    corrected_code: str = Field(
        description="Corrected code example for the identified issue."
    )

    best_practice: str = Field(
        description="Explanation of the secure or maintainable coding practice."
    )


class RemediationResult(BaseModel):
    remediations: list[RemediationItem] = Field(
        default_factory=list,
        description="Remediation guidance for the supplied findings."
    )


# ==================================================
# PR SUMMARY MODELS
# ==================================================

class SeverityBreakdown(BaseModel):
    informational: int = Field(
        default=0,
        ge=0,
        description="Total number of informational-level findings."
    )

    low: int = Field(
        default=0,
        ge=0,
        description="Total number of low-severity findings."
    )

    medium: int = Field(
        default=0,
        ge=0,
        description="Total number of medium-severity findings."
    )

    high: int = Field(
        default=0,
        ge=0,
        description="Total number of high-severity findings."
    )

    critical: int = Field(
        default=0,
        ge=0,
        description="Total number of critical-severity findings."
    )


class PRSummary(BaseModel):
    overview: str = Field(
        description=(
            "Concise, human-readable summary of the overall code review. "
            "Highlight code quality, security posture, major concerns, "
            "and the overall assessment."
        )
    )

    review_status: PRReviewStatus = Field(
        description=(
            "Overall review decision based on the identified findings. "
            "Must be APPROVED, APPROVED_WITH_SUGGESTIONS, or CHANGES_REQUESTED."
        )
    )

    total_findings: int = Field(
        default=0,
        ge=0,
        description=(
            "Total number of unique findings identified by the Code Analysis "
            "and Security Analysis Agents, without double-counting duplicates."
        )
    )

    severity_breakdown: SeverityBreakdown = Field(
        default_factory=SeverityBreakdown,
        description=(
            "Count of unique findings grouped into informational, low, "
            "medium, high, and critical severity levels."
        )
    )

    prioritized_fix_list: list[str] = Field(
        default_factory=list,
        description=(
            "Ordered list of recommended fixes. Prioritize critical and "
            "high-severity security vulnerabilities, followed by medium- "
            "and low-severity issues and code quality improvements."
        )
    )

    merge_recommendation: str = Field(
        description=(
            "Final recommendation on whether the pull request should be merged. "
            "Explain whether it is safe to merge, should be merged after "
            "improvements, or requires changes before merging."
        )
    )


class PRSummaryResult(BaseModel):
    summary: PRSummary = Field(
        description="Consolidated pull request review summary."
    )


# ==================================================
# LANGGRAPH STATE
# ==================================================

class MessageState(MessagesState):
    code: str
    language: str

    code_findings: list[dict] = Field(default_factory=list)
    security_findings: list[dict] = Field(default_factory=list)

    unified_findings: list[dict] = Field(default_factory=list)

    remediation_findings: list[dict] = Field(default_factory=list)

    pr_summary: dict = Field(
        default_factory=dict,
        description=(
            "Consolidated PR summary returned by the PR Summary Agent, "
            "including overview, review status, finding counts, "
            "prioritized fixes, and merge recommendation."
        )
    )
