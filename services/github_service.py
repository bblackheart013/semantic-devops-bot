import os
import requests

class GitHubService:
    def __init__(self, repo_owner, repo_name, token=None):
        """Initialize GitHub service with repository information"""
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        # Use token from parameter or environment variable
        self.token = token or os.environ.get("GITHUB_TOKEN")
        
        if not self.token:
            print("⚠️ GitHub token not found. Please set the GITHUB_TOKEN environment variable.")
    
    def create_issue(self, title, body, labels=None):
        """Create a GitHub issue using the REST API"""
        if not self.token:
            print("❌ GitHub token is required to create issues.")
            return None
            
        # GitHub API endpoint for creating issues
        url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/issues"
        print(f"Attempting to create issue at: {url}")
        
        # Headers for authentication
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Prepare the issue data
        issue_data = {
            "title": title,
            "body": body
        }
        
        # Add labels if provided
        if labels:
            issue_data["labels"] = labels
        
        # Make the API request
        response = requests.post(url, headers=headers, json=issue_data)
        
        if response.status_code == 201:
            # Issue created successfully
            issue = response.json()
            print(f"✅ Issue created successfully: {issue['html_url']}")
            return issue
        else:
            # Something went wrong
            print(f"❌ Failed to create issue. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None