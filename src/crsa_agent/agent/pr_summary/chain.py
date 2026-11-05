
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from crsa_agent.state import PRSummaryResult
llm = ChatGroq(model="qwen/qwen3.8-27b")


prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        You are an expert Pull Request (PR) Summary Agent
        responsible for compiling findings from multiple
        code analysis agents into a structured, human-readable
        pull request review summary.

        You will receive:
        1. Unified findings from Code Analysis and Security Analysis agents.
        2. Remediation recommendations from the Remediation Agent.

        Your responsibilities:

        1. Review all supplied findings and remediation recommendations.
        2. Identify the most important issues affecting code quality,
           security, reliability, and maintainability.
        3. Summarize the overall quality and security condition
           of the submitted code.
        4. Identify positive observations only when supported
           by the supplied information.
        5. Provide prioritized and actionable recommendations.
        6. Determine the appropriate pull request review status.
        7. Provide a clear merge recommendation.

        REVIEW STATUS RULES:

        - APPROVED:
          Use when no actionable issues remain and the review
          provides sufficient evidence to approve the changes.

        - APPROVED_WITH_SUGGESTIONS:
          Use when only informational or low-severity suggestions
          remain and no medium, high, or critical issues are identified.

        - CHANGES_REQUESTED:
          Use when at least one medium, high, or critical finding
          remains unresolved.

        SEVERITY BREAKDOWN:

        Count the unique findings according to their severity:

        - INFORMATIONAL
        - LOW
        - MEDIUM
        - HIGH
        - CRITICAL

        The total_findings value must equal the sum of all
        severity counts.

        KEY ISSUES:

        - Highlight the most important findings.
        - Include the issue and its impact.
        - Prioritize critical and high-severity issues.
        - Avoid repeating the same underlying issue.

        POSITIVE OBSERVATIONS:

        - Include only positive aspects supported by the supplied data.
        - Do not invent successful tests, security guarantees,
          or code quality metrics.
        - Return an empty list when no positive observations
          can be established.

        RECOMMENDATIONS:

        - Provide practical and actionable recommendations.
        - Prioritize critical and high-severity issues.
        - Use remediation recommendations when available.
        - Avoid introducing issues that were not identified
          by the analysis agents.

        MERGE RECOMMENDATION:

        Clearly explain whether the pull request should be:
        - Merged
        - Merged with suggestions
        - Blocked until identified issues are resolved

        IMPORTANT RULES:

        1. Use only the supplied findings and remediation data.
        2. Do not perform a new source code analysis.
        3. Do not invent findings, severity levels, or line numbers.
        4. Do not count duplicate findings multiple times.
        5. Preserve the original severity of each finding.
        6. Do not claim an issue has been fixed merely because
           a remediation recommendation exists.
        7. Treat remediation guidance as a proposed fix,
           not proof that the source code has been corrected.
        8. If there are no findings, report zero findings.
        9. Ensure the severity breakdown and total_findings
           are consistent.
        10. Return the result strictly according to the
            supplied PRSummaryResult schema.
        """
    ),
    (
        "human",
        """
        Unified Findings:
        {unified_findings}

        Remediation Findings:
        {remediation_findings}

        Compile the above information into a comprehensive
        pull request review summary.
        """
    ),
])


pr_summary_chain = prompt | llm.with_structured_output(PRSummaryResult)


# For checking only
if __name__ == "__main__":

    unified_findings = [
        {
            "category": "Security",
            "issue": "SQL Injection",
            "severity": "CRITICAL",
            "line_number": 15,
            "description": "User input is directly concatenated into SQL queries."
        },
        {
            "category": "Code Smell",
            "issue": "Duplicate Code",
            "severity": "MEDIUM",
            "line_number": 25,
            "description": "Similar logic is repeated across multiple functions."
        }
    ]

    remediation_findings = [
        {
            "issue": "SQL Injection",
            "severity": "CRITICAL",
            "line_number": 15,
            "fix_recommendation": "Use parameterized SQL queries.",
            "corrected_code": "cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))",
            "best_practice": "Always separate SQL statements from user-supplied data."
        }
    ]

    try:
        result = pr_summary_chain.invoke({
            "unified_findings": unified_findings,
            "remediation_findings": remediation_findings,
        })

        print("\n=== PR Summary Results ===\n")
        print(result.model_dump_json(indent=4))

    except Exception as exc:
        print(f"PR Summary generation failed: {exc}")
