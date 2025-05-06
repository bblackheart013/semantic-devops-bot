# test_github_issue.py
import os
from dotenv import load_dotenv
load_dotenv()

# Import the function directly
from tools.github_issue_tool import create_github_issue

# Create a simple test issue
test_issue = {
    "error_summary": "Test Issue Creation",
    "root_cause": "Testing the GitHub integration",
    "severity": "LOW",
    "recommended_solution": "This is just a test",
    "prevention": "No prevention needed"
}

# Print diagnostic info
print("=== GitHub Issue Creation Test ===")
token = os.getenv("GITHUB_TOKEN")
owner = os.getenv("GITHUB_REPO_OWNER") or "bblackheart013"
repo = os.getenv("GITHUB_REPO_NAME") or "semantic-devops-bot"

print(f"Using repository: {owner}/{repo}")
print(f"Token available: {'Yes' if token else 'No'}")

# Try to create the issue
try:
    result = create_github_issue(
        issue_details=test_issue,
        repo_owner=owner,
        repo_name=repo,
        github_token=token
    )
    print(f"Result: {result}")
except Exception as e:
    print(f"Error: {str(e)}")

print("=== Test Complete ===")