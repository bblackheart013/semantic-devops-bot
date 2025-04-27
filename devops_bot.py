import asyncio
import os
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.agents import ChatCompletionAgent

# Import our services and plugins
from services.github_service import GitHubService
from plugins.github_plugin import GitHubPlugin

def read_log_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

async def main():
    # GitHub repository details - REPLACE THESE VALUES
    repo_owner = "bblackheart013"  # Replace with your GitHub username
    repo_name = "semantic-devops-bot"         # Replace with your repository name
    
    # Step 1: Build a Kernel
    kernel = Kernel()

    # Step 2: Add the OpenAI Service
    kernel.add_service(
        OpenAIChatCompletion(
            service_id="chat-gpt-service",
            ai_model_id="gpt-3.5-turbo",
            api_key="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"
        )
    )

    # Step 3: Read the log content
    log_file_path = 'logs/sample_error.log'
    log_content = read_log_file(log_file_path)

    # Step 4: Create a ChatCompletionAgent with the kernel
    agent = ChatCompletionAgent(
        kernel=kernel,
        name="DevOps_Assistant",
        instructions="You are a DevOps expert. Analyze error logs and suggest fixes. Be specific and include exact commands when applicable."
    )

    # Step 5: Get the response from the agent
    response = await agent.get_response(
        messages=f"Analyze this error log and suggest a fix:\n{log_content}"
    )

    print("\n🔎 Suggested Fix:\n", response)
    
    # Step 6: Generate a title for the GitHub issue
    issue_title_agent = ChatCompletionAgent(
        kernel=kernel,
        name="Title_Generator",
        instructions="Create a concise, descriptive title for a GitHub issue based on an error log. The title should be short (max 100 chars) but specific enough to understand the problem."
    )
    
    issue_title = await issue_title_agent.get_response(
        messages=f"Create a GitHub issue title for this error log:\n{log_content}"
    )
    
    # Step 7: Set up GitHub service and plugin
    github_service = GitHubService(repo_owner, repo_name)
    github_plugin = GitHubPlugin(github_service)
    
    # Step 8: Create the GitHub issue
    print("\n🚀 Creating GitHub issue...")
    issue = github_plugin.create_issue_from_error(
        title=str(issue_title),
        error_log=log_content,
        suggested_fix=str(response)
    )
    
    if issue:
        print(f"View the issue at: {issue['html_url']}")

if __name__ == "__main__":
    asyncio.run(main())