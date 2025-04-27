from typing import List, Optional

class GitHubPlugin:
    def __init__(self, github_service):
        """Initialize with a GitHub service"""
        self.github_service = github_service
        
    def format_error_for_github(self, error_log, suggested_fix):
        """Format the error and suggested fix for GitHub issue description"""
        # Create a markdown formatted issue body
        issue_body = f"""## Error Log
        
{error_log}


## AI Analysis and Suggested Fix
{suggested_fix}

---
*This issue was automatically created by the DevOps AI Bot.*
"""
        return issue_body
        
    def create_issue_from_error(
        self,
        title: str,
        error_log: str,
        suggested_fix: str,
        labels: Optional[List[str]] = None
    ) -> dict:
        """
        Create a GitHub issue from an analyzed error log.

        Args:
            title (str): Title of the GitHub issue.
            error_log (str): The raw error log text.
            suggested_fix (str): AI-generated fix suggestion.
            labels (List[str], optional): Labels for the GitHub issue.

        Returns:
            dict: GitHub issue creation response (or error message).
        """
        issue_body = self.format_error_for_github(error_log, suggested_fix)

        try:
            response = self.github_service.create_issue(
                title=title,
                body=issue_body,
                labels=labels if labels is not None else ["bug", "ai-detected"]
            )
            return response
        except Exception as e:
            return {"error": f"Failed to create issue: {str(e)}"}
