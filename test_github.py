from tools.github_issue_tool import create_github_issue
import os

# Create a simple test issue
result = create_github_issue(
    issue_details={
        "error_summary": "Test Issue",
        "root_cause": "Testing GitHub integration",
        "severity": "LOW",
        "recommended_solution": "None needed",
        "prevention": "Regular testing"
    },
    repo_owner=os.getenv("GITHUB_REPO_OWNER"),
    repo_name=os.getenv("GITHUB_REPO_NAME"),
    github_token=os.getenv("GITHUB_TOKEN")
)

print(f"Result: {result}")