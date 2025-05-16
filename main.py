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

print("🔎 ENV DEBUG:")
print("GITHUB_TOKEN:", os.getenv("GITHUB_TOKEN"))
print("GITHUB_REPO_OWNER:", os.getenv("GITHUB_REPO_OWNER"))
print("GITHUB_REPO_NAME:", os.getenv("GITHUB_REPO_NAME"))

print("\n🔍 Starting program execution...")


from tools.github_issue_tool import create_github_issue

# AutoGen imports
from autogen import GroupChat, GroupChatManager, ConversableAgent

# Import custom agents
from agents.coordinator_agent import CoordinatorAgent
from agents.analyzer_agent import AnalyzerAgent

# Import GitHub integration (to be implemented)
# from tools.github_tool import GitHubIssueTool

def validate_github_config():
    """Validate GitHub configuration from environment variables."""
    print("\n🔍 Validating GitHub configuration:")
    
    token = os.getenv("GITHUB_TOKEN")
    owner = os.getenv("GITHUB_REPO_OWNER")
    repo = os.getenv("GITHUB_REPO_NAME")
    
    if token:
        # Hide most of the token for security
        masked_token = token[:4] + "*" * (len(token) - 8) + token[-4:] if len(token) > 8 else "****"
        print(f"✅ GITHUB_TOKEN: {masked_token}")
    else:
        print("❌ GITHUB_TOKEN: Not found")
        
    if owner:
        print(f"✅ GITHUB_REPO_OWNER: {owner}")
    else:
        print("❌ GITHUB_REPO_OWNER: Not found")
        
    if repo:
        print(f"✅ GITHUB_REPO_NAME: {repo}")
    else:
        print("❌ GITHUB_REPO_NAME: Not found")
        
    if token and owner and repo:
        print("✅ GitHub configuration is complete")
    else:
        print("⚠️ GitHub configuration is incomplete")

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
        print("\n🔍 Starting log analysis...")
        self.logger.info("Starting log analysis")
        # Use the coordinator to detect error type
        error_type, confidence = self.coordinator.detect_error_type(log_content)
        print(f"🔍 Detected error type: {error_type} (confidence: {confidence:.2f})")

        # Get context and route to specialist
        context = self.coordinator.get_log_context(log_content)
        specialist_response = self.coordinator.route_to_specialist(error_type, log_content, context)

        # Get the analysis from the response
        if specialist_response and "response" in specialist_response:
            analysis_result = specialist_response["response"]
            # Add confidence score
            analysis_result["detection_confidence"] = confidence
        else:
            # Fallback if no response
            analysis_result = {
                "error_summary": f"Analysis failed for {error_type}",
                "root_cause": "Unable to get specialist analysis",
                "severity": "UNKNOWN",
                "recommended_solution": "Check logs for errors",
                "prevention": "Ensure all specialist agents are registered"
            }
=======
    """
Enhanced analyze_log method for DevOpsBot class - 
Replace the existing method in main.py with this implementation.
"""

def analyze_log(self, log_content):
    """
    Analyze a log file using the analyzer agent directly.
    
    Args:
        log_content: The error log content to analyze
>>>>>>> b89151a7fe5ec1b19534aed89d66958077045cbb
        
    Returns:
        A dictionary with the analysis results
    """
    self.logger.info("Starting log analysis")
    
    try:
        # If we have a valid analyzer, use it
        if hasattr(self, 'analyzer') and self.analyzer:
            # Detect the log type for better analysis
            log_type = "unknown"
            if "ModuleNotFoundError" in log_content or "ImportError" in log_content:
                log_type = "python"
            elif "docker" in log_content.lower() or "container" in log_content.lower():
                log_type = "docker" 
            elif "azure" in log_content.lower() or "resource group" in log_content.lower():
                log_type = "azure"
                
            self.logger.info(f"Detected log type: {log_type}")
            
            # Use the analyzer agent
            try:
                # Try to use the actual analyzer
                analysis_result = self.analyzer.analyze_log(log_content)
                self.logger.info("Analyzer agent returned analysis")
                
                # Return the analysis result with metadata
                return {
                    "status": "success",
                    "error_type": analysis_result.get("error_summary", "Unknown error").split(":")[0],
                    "analysis": analysis_result,
                    "source": "analyzer_agent"
                }
                
            except Exception as e:
                self.logger.error(f"Error using analyzer agent: {e}")
                # Fall back to coordinator based routing
                pass
                
        # Use coordinator-based routing if available
        if hasattr(self, 'coordinator') and self.coordinator:
            try:
                coord_result = self.coordinator.analyze_log(log_content)
                self.logger.info("Coordinator completed analysis")
                return coord_result
            except Exception as e:
                self.logger.error(f"Error using coordinator: {e}")
                # Fall back to fallback option
        
        # Fallback to a simple pattern-based analysis
        self.logger.warning("Using fallback pattern-based analysis")
        
        # Check for common error patterns
        error_type = "unknown"
        root_cause = "Could not determine root cause"
        recommended_solution = "Please review the log for more details"
        
        if "ModuleNotFoundError: No module named 'requests'" in log_content:
            error_type = "python_import_error"
            error_summary = "ModuleNotFoundError: No module named 'requests'"
            root_cause = "The Python script is trying to import the 'requests' library, but it's not installed in the current environment"
            recommended_solution = "Install the missing package using pip:\n\npip install requests"
            prevention = "Use requirements.txt to document dependencies and virtual environments to isolate project dependencies"
            severity = "Medium - Application cannot run without this dependency"
            severity_level = "MEDIUM"
            
        elif "pull access denied" in log_content and "repository does not exist" in log_content:
            error_type = "docker_auth_error"
            error_summary = "Docker pull access denied: repository does not exist or requires authentication"
            root_cause = "Docker is unable to pull the specified image because it either does not exist or you don't have permission to access it"
            recommended_solution = "1. Verify the image name is correct\n2. Use 'docker login' to authenticate with the registry\n3. Check that you have access to the repository"
            prevention = "Use a CI/CD system with proper credential management for automated deployments"
            severity = "High - Deployment is blocked until resolved"
            severity_level = "HIGH"
            
        elif "DeploymentFailed" in log_content and "Resource group" in log_content and "could not be found" in log_content:
            error_type = "azure_resource_error"
            error_summary = "Azure Deployment Failed: Resource group not found"
            root_cause = "The specified Azure resource group does not exist in the current subscription"
            recommended_solution = "1. Verify the resource group name\n2. Check that you're using the correct Azure subscription\n3. Create the resource group if needed using 'az group create'"
            prevention = "Use infrastructure as code tools like ARM templates or Terraform to manage resource groups"
            severity = "Medium - Deployment cannot proceed"
            severity_level = "MEDIUM"
            
        else:
            # Generic error case
            error_type = "unknown_error"
            error_summary = log_content[:100] + ("..." if len(log_content) > 100 else "")
            root_cause = "Could not determine the specific cause of this error"
            recommended_solution = "Review the complete log for more context and details"
            prevention = "Implement comprehensive logging and monitoring"
            severity = "Medium - Unknown impact"
            severity_level = "MEDIUM"
            
        analysis_result = {
            "error_summary": error_summary,
            "root_cause": root_cause,
            "severity": severity,
            "severity_level": severity_level,
            "recommended_solution": recommended_solution,
            "prevention": prevention
        }
            
        return {
            "status": "success",
            "error_type": error_type,
            "analysis": analysis_result,
            "source": "fallback_analysis"
        }
        
    except Exception as e:
        self.logger.error(f"Error in analyze_log: {e}")
        return {
            "status": "error",
            "error": str(e),
            "analysis": {
                "error_summary": "Analysis failed",
                "root_cause": f"Internal error: {str(e)}",
                "severity": "Unknown",
                "severity_level": "UNKNOWN",
                "recommended_solution": "Please try again or check server logs",
                "prevention": "Report this issue to the development team"
            }
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
    
    # Add the missing arguments
    parser.add_argument("--github-token", help="GitHub API token")
    parser.add_argument("--repo-owner", help="GitHub repository owner")
    parser.add_argument("--repo-name", help="GitHub repository name")
    
    return parser.parse_args()

def main():
    """Main entry point for the application."""
    print("🚀 Main function started")


    # Parse command-line arguments
    args = parse_arguments()
    
    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logging(log_level)
    logger.info("Starting Semantic DevOps Bot")

    validate_github_config()
    
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
        
        # Add GitHub token and repo info if provided via command line
        if args.github_token:
            config["github"]["token"] = args.github_token
            print(f"GitHub token provided via command line: {'*' * 30}")
        if args.repo_owner:
            config["github"]["repo_owner"] = args.repo_owner
            print(f"Repo owner from command line: {args.repo_owner}")
        if args.repo_name:
            config["github"]["repo_name"] = args.repo_name
            print(f"Repo name from command line: {args.repo_name}")
            
        # Check for environment variables if not provided via command line
        if "token" not in config["github"] or not config["github"]["token"]:
            env_token = os.getenv("GITHUB_TOKEN")
            if env_token:
                config["github"]["token"] = env_token
                print(f"GitHub token loaded from environment: {'*' * 30}")
                
        if "repo_owner" not in config["github"] or not config["github"]["repo_owner"]:
            env_owner = os.getenv("GITHUB_REPO_OWNER")
            if env_owner:
                config["github"]["repo_owner"] = env_owner
                print(f"Repo owner loaded from environment: {env_owner}")
                
        if "repo_name" not in config["github"] or not config["github"]["repo_name"]:
            env_name = os.getenv("GITHUB_REPO_NAME")
            if env_name:
                config["github"]["repo_name"] = env_name
                print(f"Repo name loaded from environment: {env_name}")
        
        # Log GitHub issue configuration
        logger.info(f"GitHub issue creation enabled")
        if "repo_owner" in config["github"] and "repo_name" in config["github"]:
            logger.info(f"Target repository: {config['github']['repo_owner']}/{config['github']['repo_name']}")
        else:
            logger.warning("GitHub repository information incomplete. Issues may not be created correctly.")
    
    print(f"Config for GitHub: {config.get('github', {})}")
    
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

if __name__ == "__main__":
    sys.exit(main())

       