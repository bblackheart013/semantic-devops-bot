import os
from dotenv import load_dotenv
load_dotenv()

# Import the GitHub issue creation function
from tools.github_issue_tool import create_github_issue

# Sample error analysis
sample_analysis = {
    "error_summary": "ModuleNotFoundError: No module named 'requests'",
    "root_cause": "Missing 'requests' package in Python environment",
    "severity": "MEDIUM",
    "recommended_solution": "Install the package using pip install requests",
    "prevention": "Include 'requests' in your requirements.txt"
}

# Get GitHub info from environment variables
github_token = os.getenv("GITHUB_TOKEN")
repo_owner = os.getenv("GITHUB_REPO_OWNER")
repo_name = os.getenv("GITHUB_REPO_NAME")

print(f"GitHub Configuration:")
print(f"Token available: {'Yes' if github_token else 'No'}")
print(f"Repository Owner: {repo_owner}")
print(f"Repository Name: {repo_name}")

# Try to create a GitHub issue
try:
    result = create_github_issue(
        issue_details=sample_analysis,
        repo_owner=repo_owner,
        repo_name=repo_name,
        github_token=github_token
    )
    print(f"\nResult: {result}")
except Exception as e:
    print(f"Error: {str(e)}")