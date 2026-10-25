
from enum import Enum

from pydantic import BaseModel, Field
from langgraph.graph import MessagesState


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Finding(BaseModel):
    category: str = Field(
        description="Category of the finding."
    )
    issue: str = Field(
        description="Short title describing the issue."
    )
    severity: Severity = Field(
        description="Severity: LOW, MEDIUM, HIGH, or CRITICAL."
    )
    line_number: int | None = Field(
        default=None,
        description="Affected source line, if identifiable."
    )
    description: str = Field(
        description="Explanation of the issue and its impact."
    )
    recommendation: str = Field(
        description="Initial recommendation to address the issue."
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
