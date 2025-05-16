# agents/__init__.py
# This makes the agents directory a proper Python package
# Allows imports like: from agents.coordinator_agent import CoordinatorAgent

# Import key components to make them available at the package level
from agents.coordinator_agent import CoordinatorAgent
from agents.analyzer_agent import AnalyzerAgent

# agents/tests/__init__.py (For tests directory)
# This makes the tests directory a proper Python package

# tools/__init__.py
# This makes the tools directory a proper Python package
from tools.github_issue_tool import GitHubIssueTool, create_github_issue

# services/__init__.py
# This makes the services directory a proper Python package
from services.github_service import GitHubService

# plugins/__init__.py
# This makes the plugins directory a proper Python package
from plugins.github_plugin import GitHubPlugin