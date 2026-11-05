from langgraph.graph import StateGraph, START, END
from langgraph.types import RetryPolicy

from crsa_agent.state import MessageState
from crsa_agent.agent.code_analysis.node import code_analysis_node
from crsa_agent.agent.security_analysis.node import security_analysis_node
from crsa_agent.agent.remediation.node import remediation_node
from crsa_agent.agent.pr_summary.node import pr_summary_node

builder = StateGraph(MessageState)

# Retry policy: maximum 10 attempts per node
retry_policy = RetryPolicy(max_attempts=10)

# Register agent nodes with retry policy
builder.add_node(
    "code_analysis",
    code_analysis_node,
    retry_policy=retry_policy,
)

builder.add_node(
    "security_analysis",
    security_analysis_node,
    retry_policy=retry_policy,
)

builder.add_node(
    "remediation",
    remediation_node,
    retry_policy=retry_policy,
)

builder.add_node(
    "pr_summary",
    pr_summary_node,
    retry_policy=retry_policy,
)

# Merge and sort findings by severity
builder.add_node(
    "merge_findings",
    lambda state: {
        "unified_findings": sorted(
            state["code_findings"] + state["security_findings"],
            key=lambda item: {
                "CRITICAL": 0,
                "HIGH": 1,
                "MEDIUM": 2,
                "LOW": 3,
                "INFORMATIONAL": 4,
            }.get(item["severity"], 5),
        )
    },
    retry_policy=retry_policy,
)

# Run both agents in parallel
builder.add_edge(START, "code_analysis")
builder.add_edge(START, "security_analysis")

# Merge after both agents complete
builder.add_edge("code_analysis", "merge_findings")
builder.add_edge("security_analysis", "merge_findings")

# Remediation
builder.add_edge("merge_findings", "remediation")
builder.add_edge("remediation", "pr_summary")
builder.add_edge("pr_summary", END)

# Compile the graph
graph = builder.compile()

if __name__ == "__main__":
    graph.get_graph().draw_mermaid_png(output_file_path="graph.png")

    sample_code = '''
    import sqlite3

    API_KEY = "sk_test_123456789"

    def get_user(username):
        conn = sqlite3.connect("users.db")
        query = "SELECT * FROM users WHERE username = '" + username + "'"
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    '''

    initial_state = {
        "code": sample_code,
        "language": "python",
    }

    result = graph.invoke(initial_state)
    print(result)