"""
Semantic DevOps Bot - Main Application
-------------------------------------
This module sets up and runs the multi-agent system for analyzing DevOps errors
and creating GitHub issues with solutions.
"""

import os
import sys
import logging
import json
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Union, Any
from dotenv import load_dotenv
load_dotenv()
from tools.github_issue_tool import create_github_issue

# AutoGen imports
from autogen import GroupChat, GroupChatManager, ConversableAgent

# Import custom agents
from agents.coordinator_agent import CoordinatorAgent
from agents.analyzer_agent import AnalyzerAgent

# Import GitHub integration (to be implemented)
# from tools.github_tool import GitHubIssueTool

def create_llm_config(temperature=0.1):
    """Create a properly formatted LLM configuration."""
    return {
        "config_list": [{"model": "gpt-4o"}], 
        "temperature": temperature
    }
# Configure logging
def setup_logging(log_level=logging.INFO):
    """Set up logging configuration."""
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(f"logs/devops_bot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        ]
    )
    return logging.getLogger("main")


# Create specialized agents
def create_build_error_agent() -> ConversableAgent:
    """Create a specialized agent for build errors."""
    system_message = """You are a Build Error Specialist. You excel at:
    1. Interpreting build logs from CI/CD systems
    2. Identifying dependency conflicts and version issues
    3. Understanding compilation and packaging errors
    4. Solving problems with build configuration files
    5. Providing actionable solutions for npm, yarn, maven, gradle, etc.
    
    Focus on the specific build tool in question and consider common pitfalls.
    """
    return ConversableAgent(
        name="BuildErrorAgent",
        system_message=system_message,
        llm_config=create_llm_config(temperature=0.1)
    )



def create_deployment_error_agent() -> ConversableAgent:
    """Create a specialized agent for deployment errors."""
    system_message = """You are a Deployment Error Specialist. You excel at:
    1. Debugging container deployment issues (Docker, Kubernetes)
    2. Resolving cloud platform deployment failures (Azure, AWS, GCP)
    3. Analyzing network configuration and connectivity problems
    4. Identifying permission and security constraints
    5. Diagnosing resource allocation issues
    
    When analyzing errors, consider infrastructure constraints and environment differences.
    """
    return ConversableAgent(
        name="DeploymentErrorAgent",
        system_message=system_message,
        llm_config=create_llm_config(temperature=0.1)
    )

def create_azure_optimization_agent() -> ConversableAgent:
    """Create a specialized agent for Azure optimizations."""
    system_message = """You are an Azure Optimization Specialist. You excel at:
    1. Identifying cost optimization opportunities in Azure services
    2. Suggesting performance improvements for Azure resources
    3. Recognizing security best practices and potential vulnerabilities
    4. Recommending scaling strategies for Azure deployments
    5. Providing guidance on Azure resource governance
    
    Look for patterns that indicate waste, inefficiency, or unnecessary complexity.
    """
    return ConversableAgent(
        name="AzureOptimizationAgent",
        system_message=system_message,
        llm_config=create_llm_config(temperature=0.1)
    )

def read_log_file(file_path):
    """Read a log file and return its contents."""
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except Exception as e:
        logging.error(f"Error reading log file: {e}")
        return None


def create_github_issue(analysis_result, repo_owner, repo_name, github_token=None):
    """Create a GitHub issue based on analysis results."""
    # This function would be implemented to use the GitHub API
    # For now, we'll just print what would be created
    
    # Extract key information from analysis
    error_summary = analysis_result.get("error_summary", "Unknown error")
    recommended_solution = analysis_result.get("recommended_solution", "No solution provided")
    severity = analysis_result.get("severity", "Unknown severity")
    
    # Create an issue title
    title = f"[{severity}] {error_summary[:50]}..."
    
    # Create issue body
    body = f"""## Error Analysis

### Summary
{error_summary}

### Root Cause
{analysis_result.get('root_cause', 'Unknown')}

### Severity
{severity}

### Recommended Solution
{recommended_solution}

### Prevention
{analysis_result.get('prevention', 'No prevention steps provided')}

---
*This issue was automatically generated by the Semantic DevOps Bot*
"""
    
    print("\n=== GitHub Issue that would be created ===")
    print(f"Repository: {repo_owner}/{repo_name}")
    print(f"Title: {title}")
    print(f"Body:\n{body}")
    print("==========================================\n")
    
    # In a real implementation, this would call the GitHub API
    # return github_tool.create_issue(repo_owner, repo_name, title, body, github_token)


class DevOpsBot:
    """Main DevOps Bot class that orchestrates the multi-agent system."""
    
    def __init__(self, config=None):
        """Initialize the DevOps Bot with configuration."""
        self.logger = logging.getLogger("DevOpsBot")
        self.logger.info("Initializing DevOps Bot")
        
        # Load configuration
        self.config = config or self._load_default_config()
        
        # Create the agents
        self.coordinator = self._create_coordinator()
        self.analyzer = self._create_analyzer()
        self.build_agent = create_build_error_agent()
        self.deployment_agent = create_deployment_error_agent()
        self.azure_agent = create_azure_optimization_agent()
        
        # Register specialist agents with coordinator
        self.coordinator.register_specialist("build_error", self.build_agent)
        self.coordinator.register_specialist("deployment_error", self.deployment_agent)
        self.coordinator.register_specialist("azure_error", self.azure_agent)
        
        # Set up group chat
        self.agents = [
            self.coordinator,
            self.analyzer,
            self.build_agent, 
            self.deployment_agent,
            self.azure_agent
        ]
        
        # Create group chat with all agents
        self.groupchat = GroupChat(
            agents=self.agents,
            messages=[],
            max_round=self.config.get("max_rounds", 10)
        )
        
        self.logger.info(f"DevOps Bot initialized with {len(self.agents)} agents")
    
    def _create_coordinator(self):
        """Create the coordinator agent."""
        return CoordinatorAgent(
            name=self.config.get("coordinator_name", "Coordinator"),
            llm_config=self.config.get("llm_config")
        )
    
    def _create_analyzer(self):
        """Create the analyzer agent."""
        return AnalyzerAgent(
            name=self.config.get("analyzer_name", "Analyzer"),
            llm_config=self.config.get("llm_config")
        )
    
    def _load_default_config(self):
        """Load default configuration."""
        # Try to load from config.json if it exists
        if os.path.exists("config.json"):
            try:
                with open("config.json", "r") as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load config.json: {e}")
        
        # Default configuration
        return {
        "coordinator_name": "DevOpsCoordinator",
        "analyzer_name": "DevOpsAnalyzer",
        "llm_config": create_llm_config(temperature=0.2),
        "max_rounds": 10,
        "github": {
            "repo_owner": "your-username",
            "repo_name": "your-repo"
        }
    }
    
    def analyze_log(self, log_content):
        """Analyze a log file using the analyzer agent directly."""
        self.logger.info("Starting log analysis")
        
        # Use the analyzer agent directly
        analysis_result = self.analyzer.analyze_log(log_content)
        
        # Print the final analysis response
        print("\n📌 Final Analysis Response:")
        print(f"ERROR SUMMARY: {analysis_result['error_summary']}")
        print(f"ROOT CAUSE: {analysis_result['root_cause']}")
        print(f"SEVERITY: {analysis_result['severity']}")
        print(f"RECOMMENDED SOLUTION: {analysis_result['recommended_solution']}")
        print(f"PREVENTION: {analysis_result['prevention']}")
        
        # If GitHub issue creation is enabled, create an issue
        if self.config.get("github", {}).get("create_issues", False):
            repo_owner = self.config["github"].get("repo_owner")
            repo_name = self.config["github"].get("repo_name")
            github_token = self.config["github"].get("token")
            
            # Using the GitHub Issue Tool
            from tools.github_issue_tool import create_github_issue
            create_github_issue(
                issue_details=analysis_result,
                repo_owner=repo_owner,
                repo_name=repo_name,
                github_token=github_token
            )
        
        # Add a simple conversation record for saving
        self.groupchat.messages = [{
            "content": f"Analysis of error: {log_content}",
            "role": "user"
        }, {
            "content": str(analysis_result),
            "role": "assistant"
        }]
        
        return {
            "analysis": analysis_result,
            "messages": self.groupchat.messages
        }


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Semantic DevOps Bot")
    parser.add_argument("--log", "-l", help="Path to log file to analyze")
    parser.add_argument("--log-text", "-t", help="Log text to analyze")
    parser.add_argument("--config", "-c", help="Path to configuration file")
    parser.add_argument("--github-issue", "-g", action="store_true", 
                        help="Create GitHub issue with analysis results")
    parser.add_argument("--verbose", "-v", action="store_true", 
                        help="Enable verbose logging")
    parser.add_argument("--create-issue", "-i", action="store_true", 
                        help="Create GitHub issue with analysis results")
    return parser.parse_args()

def main():
    """Main entry point for the application."""
    # Parse command-line arguments
    args = parse_arguments()
    
    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logging(log_level)
    logger.info("Starting Semantic DevOps Bot")
    
    # Load custom configuration if provided
    config = None
    if args.config:
        try:
            with open(args.config, "r") as f:
                config = json.load(f)
            logger.info(f"Loaded configuration from {args.config}")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return 1
    
    # Add GitHub issue creation flag if specified
    if args.create_issue:
        if config is None:
            config = {}
        if "github" not in config:
            config["github"] = {}
        config["github"]["create_issues"] = True
    
    try:
        # Initialize the DevOps Bot
        bot = DevOpsBot(config)
        
        # Get log content from file or command-line
        log_content = None
        if args.log:
            log_content = read_log_file(args.log)
            if not log_content:
                logger.error(f"Failed to read log file: {args.log}")
                return 1
        elif args.log_text:
            log_content = args.log_text
        else:
            # Use a demo log if none provided
            log_content = """
            ModuleNotFoundError: No module named 'requests'
            Traceback (most recent call last):
              File "app.py", line 3, in <module>
                import requests
            ModuleNotFoundError: No module named 'requests'
            """
            logger.info("No log provided, using demo log")
        
        # Analyze the log
        result = bot.analyze_log(log_content)
        
        # Save the conversation
        if hasattr(bot, 'save_conversation'):
            bot.save_conversation()
        
        logger.info("Analysis completed successfully")
        return 0
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        return 1


# For simple testing
# For simple testing
if __name__ == "__main__":
    # # Create analyzer agent
    # analyzer = AnalyzerAgent(name="Analyzer")
    # # Create coordinator agent
    # coordinator = CoordinatorAgent(name="Coordinator")
    # # Create the group chat
    # groupchat = GroupChat(agents=[coordinator, analyzer], messages=[], max_round=5)

    # # Start the conversation
    # print("🚀 starting conversation...\n")
    # manager = GroupChatManager(groupchat=groupchat, llm_config=coordinator.llm_config)
    # manager.run(
    #     message="here is an error log: ModuleNotFoundError: No module named 'requests'",
    #     sender=coordinator
    # )

    # Uncomment this to use the full DevOpsBot implementation
    sys.exit(main())