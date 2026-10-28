
from langgraph.graph import StateGraph, START, END

from crsa_agent.state import MessageState
from crsa_agent.agent.code_analysis.node import code_analysis_node
from crsa_agent.agent.security_analysis.node import security_analysis_node


builder = StateGraph(MessageState)

# Register agent nodes
builder.add_node("code_analysis", code_analysis_node)
builder.add_node("security_analysis", security_analysis_node)

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
                "INFORMATIONAL" : 4
            }.get(item["severity"], 5),
        )
    },
)

# Run both agents in parallel
builder.add_edge(START, "code_analysis")
builder.add_edge(START, "security_analysis")

# Merge after both agents complete
builder.add_edge("code_analysis", "merge_findings")
builder.add_edge("security_analysis", "merge_findings")

builder.add_edge("merge_findings", END)

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


    def process_users(users):
        results = []

        for user in users:
            if user is not None:
                if user["active"] == True:
                    if user["role"] == "admin":
                        results.append(user["name"])
        return results
    '''

    initial_state = {
        "code": sample_code,
        "language": "python",
    }

    result = graph.invoke(initial_state)
    print(result)

