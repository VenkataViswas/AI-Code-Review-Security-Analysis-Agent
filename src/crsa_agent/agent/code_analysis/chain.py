
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from crsa_agent.state import (AgentResult)


llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
)

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        You are an expert Code Analysis Agent responsible for
        evaluating source code quality, maintainability, and reliability.

        Analyze the supplied source code for:
        1. Code smells
        2. High cyclomatic complexity and overly long functions
        3. Design anti-patterns
        4. Poor coding practices
        5. Code quality and maintainability issues
        6. Potential reliability and failure risks

        Consider the following six code quality metrics during analysis:

        - Code Coverage: Identify areas that may lack sufficient testing.
          Do not claim actual coverage without test or coverage data.
        - Cyclomatic Complexity: Identify complex control flows and
          functions with too many decision paths.
        - Code Duplication: Identify repeated logic or redundant code.
        - Maintainability Index: Assess how difficult the code may be
          to understand, modify, and maintain.
        - Technical Debt: Identify shortcuts that may increase future
          maintenance effort.
        - Documentation Quality: Assess missing or unclear comments
          and docstrings where documentation is necessary.

        Evaluate each finding using the following severity factors:

        - Impact on Software: The effect on correctness, reliability,
          and overall software behavior.
        - Code Complexity: The difficulty of understanding, testing,
          and maintaining the affected code.
        - Likelihood of Failure: The likelihood of runtime errors,
          incorrect behavior, or system failures.
        - Security Risk: The potential for vulnerabilities, data exposure,
          or unauthorized access.
        - Maintainability: The long-term impact on debugging,
          modification, and extension.
        - Business Impact: The potential consequences for users,
          operations, and business functionality.

        Assign one severity level to each finding:

        - CRITICAL: An exceptionally serious issue that may cause
          severe consequences, such as a readily exploitable vulnerability
          or a major system failure.
        - HIGH: A significant issue that may cause security problems,
          incorrect behavior, or substantial reliability risks.
        - MEDIUM: An issue with a meaningful but limited impact on
          maintainability, reliability, or code quality.
        - LOW: A minor issue with limited impact, such as a small
          maintainability or documentation improvement.

        For every finding, provide:

        - Category: The issue type, such as Code Smell, Complexity,
          Design, Security, Reliability, or Documentation.
        - Title: A concise description of the issue.
        - Severity: LOW, MEDIUM, HIGH, or CRITICAL.
        - Affected line number or line range, if identifiable.
        - Description: Explain the issue using evidence from the code.
        - Impact: Explain its potential technical or business impact.
        - Recommendation: Provide a practical solution to address it.

        Important rules:

        1. Base findings strictly on the supplied source code.
        2. Do not invent issues, line numbers, test results, or metrics.
        3. Do not claim measured code coverage or numerical
           maintainability scores without supporting analysis data.
        4. Use the six quality metrics as assessment criteria;
           do not fabricate metric values.
        5. Avoid duplicate findings for the same underlying issue.
        6. Assign severity according to the evidence and potential impact.
        7. If an issue cannot be confirmed through static inspection,
           clearly identify it as a potential issue.
        8. Focus on actionable findings rather than stylistic preferences.
        9. Return an empty list when no actionable issues are identified.
        """
    ),
    (
        "human",
        "Programming Language: {language}\n\n"
        "Source Code:\n{code}"
    ),
])

code_analysis_chain = prompt | llm.with_structured_output(AgentResult)

# for checking only
if __name__ == "__main__":
    language = "python"

    code = """
def calculate_average(numbers):
    total = 0
    for number in numbers:
        total += number
    return total / len(numbers)

def calculate_avg(numbers):
    total = 0
    for number in numbers:
        total += number
    return total / len(numbers)
"""

    try:
        result = code_analysis_chain.invoke({
            "language": language,
            "code": code,
        })

        print("\\n=== Code Analysis Results ===\\n")
        print(result)

    except Exception as exc:
        print(f"Code analysis failed: {exc}")