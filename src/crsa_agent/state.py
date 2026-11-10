
from enum import Enum

from pydantic import BaseModel, Field
from langgraph.graph import MessagesState


class Severity(str, Enum):
    INFORMATIONAL = "INFORMATIONAL" # Suggestion no immediate action required
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


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
        description="Short title describing the issue."
    )
    severity: Severity = Field(
    description="Severity: INFORMATIONAL, LOW, MEDIUM, HIGH, or CRITICAL."
    )
    line_number: int | None = Field(
        default=None,
        description="Affected source line, if identifiable."
    )
    description: str = Field(
        description="Explanation of the issue and its impact."
    )

class AgentResult(BaseModel):
    findings: list[Finding] = Field(
        default_factory=list,
        description="Findings identified by an analysis agent."
    )


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
        description="Specific steps to fix the issue."
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


class MessageState(MessagesState):
    code: str
    language: str
    code_findings: list[dict]
    security_findings: list[dict]
    unified_findings: list[dict]
    remediation_findings: list[dict]
    pr_summary: list[dict]

class PRReviewStatus(str, Enum):
    APPROVED = "APPROVED"
    APPROVED_WITH_SUGGESTIONS = "APPROVED_WITH_SUGGESTIONS"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"


class SeveritySummary(BaseModel):
    informational: int = Field(default=0)
    low: int = Field(default=0)
    medium: int = Field(default=0)
    high: int = Field(default=0)
    critical: int = Field(default=0)


class PRSummary(BaseModel):
    title: str = Field(
        description="Short, meaningful title for the pull request review."
    )

    overview: str = Field(
        description="Human-readable summary of the overall code review."
    )

    review_status: PRReviewStatus = Field(
        description=(
            "Overall review decision: APPROVED, "
            "APPROVED_WITH_SUGGESTIONS, or CHANGES_REQUESTED."
        )
    )

    total_findings: int = Field(
        default=0,
        description="Total number of unique findings across all agents."
    )

    severity_breakdown: SeveritySummary = Field(
        default_factory=SeveritySummary,
        description="Count of findings grouped by severity."
    )

    key_issues: list[str] = Field(
        default_factory=list,
        description="Most important issues identified during the review."
    )

    positive_observations: list[str] = Field(
        default_factory=list,
        description="Positive aspects of the code identified during review."
    )

    recommendations: list[str] = Field(
        default_factory=list,
        description="Prioritized recommendations for improving the code."
    )

    merge_recommendation: str = Field(
        description=(
            "Final recommendation explaining whether the PR should be merged, "
            "merged with suggestions, or blocked until issues are resolved."
        )
    )


class PRSummaryResult(BaseModel):
    summary: PRSummary = Field(
        description="Consolidated pull request review summary."
    )