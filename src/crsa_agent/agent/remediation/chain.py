
from langchain_core.prompts import ChatPromptTemplate
from crsa_agent.state import RemediationResult
from langchain_groq import ChatGroq
llm = ChatGroq(model="qwen/qwen3.8-27b")

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        You are an expert Code Remediation Agent.

        Your task is to provide actionable fixes for code quality
        issues and security vulnerabilities identified by other agents.

        For every supplied finding:

        1. Identify the specific issue.
        2. Provide a concrete fix recommendation.
        3. Give a corrected code example relevant to the original code.
        4. Explain the best practice behind the fix.
        5. Preserve existing functionality wherever possible.
        6. For security issues, prioritize secure coding practices.
        7. For design and complexity issues, prioritize readability,
           maintainability, and appropriate design principles.

        Requirements:
        - Address every supplied finding.
        - Do not invent missing APIs, variables, or dependencies.
        - Use the original source code as context.
        - Correct only the relevant code where possible.
        - Make corrected examples consistent with the supplied language.
        - If a complete fix requires missing context, state the limitation
          in the recommendation rather than inventing assumptions.
        - Do not claim that the original source has been modified.
        - Preserve the severity and line number of each original finding.

        Return the results using the requested structured schema.
        """
    ),
    (
        "human",
        """
        Programming language:
        {language}

        Original source code:
        {code}

        Unified findings:
        {findings}
        """
    ),
])

remediation_chain = (
    prompt | llm.with_structured_output(RemediationResult)
)



def main():
    sample_code = """
def get_user(user_id):
    query = "SELECT * FROM users WHERE id = " + user_id
    return query
"""

    sample_findings = [
        {
            "type": "SQL Injection",
            "severity": "HIGH",
            "line": 2,
            "description": "SQL query is constructed using string concatenation.",
            "recommendation": "Use parameterized queries.",
        }
    ]

    result = remediation_chain.invoke(
        {
            "code": sample_code,
            "language": "Python",
            "findings": sample_findings,
        }
    )

    print("\n========== REMEDIATION CHAIN OUTPUT ==========\n")
    print(result)


if __name__ == "__main__":
    main()