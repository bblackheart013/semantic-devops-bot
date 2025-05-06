import unittest
from unittest.mock import patch, Mock
import logging
import sys
import os

# Adjust the Python path to include the project root directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now we can import our modules correctly
try:
    from agents.agent_router import AgentRouter
except ImportError:
    # Fallback direct import for when running tests directly
    from agent_router import AgentRouter


class TestAgentRouter(unittest.TestCase):
    """Test cases for the AgentRouter class."""
    
    def setUp(self):
        """Set up the test environment."""
        # Configure a test logger
        self.logger = logging.getLogger("test_logger")
        self.logger.setLevel(logging.DEBUG)
        # Use a null handler to prevent log output during tests
        self.logger.addHandler(logging.NullHandler())
        
        # Create a test router
        self.router = AgentRouter(logger=self.logger)
    
    def test_init(self):
        """Test router initialization."""
        self.assertIsNotNone(self.router.error_patterns)
        self.assertIsNotNone(self.router.routing_stats)
    
    def test_route_log_build_error(self):
        """Test routing a build error log."""
        log_content = "ModuleNotFoundError: No module named 'requests'"
        agent_type, confidence = self.router.route_log(log_content)
        self.assertEqual(agent_type, "build_error")
        self.assertGreater(confidence, 0.5)
    
    def test_route_log_deployment_error(self):
        """Test routing a deployment error log."""
        log_content = "Error response from daemon: pull access denied for myapp/image"
        agent_type, confidence = self.router.route_log(log_content)
        self.assertEqual(agent_type, "deployment_error")
        self.assertGreater(confidence, 0.5)
    
    def test_route_log_azure_error(self):
        """Test routing an Azure error log."""
        log_content = "DeploymentFailed: Resource group 'my-group' could not be found"
        agent_type, confidence = self.router.route_log(log_content)
        self.assertEqual(agent_type, "azure_error")
        self.assertGreater(confidence, 0.5)
    
    def test_route_log_general_error(self):
        """Test routing a general error log."""
        log_content = "Something went wrong with no clear error type"
        agent_type, confidence = self.router.route_log(log_content)
        self.assertEqual(agent_type, "general_error")
    
    def test_get_pattern_weight(self):
        """Test pattern weight assignment."""
        # Test a high priority pattern
        high_weight = self.router._get_pattern_weight(
            "build_error", 
            "ModuleNotFoundError: No module named '([^']+)'"
        )
        self.assertEqual(high_weight, 3.0)
        
        # Test a standard pattern
        standard_weight = self.router._get_pattern_weight(
            "build_error", 
            "build failed"
        )
        self.assertEqual(standard_weight, 1.0)
        
        # Test a general error pattern
        general_weight = self.router._get_pattern_weight(
            "general_error", 
            "error:"
        )
        self.assertEqual(general_weight, 0.5)
    
    def test_pattern_weights(self):
        """Test that pattern weights are applied correctly."""
        # Test with a high priority pattern
        high_priority_log = "ModuleNotFoundError: No module named 'requests'"
        _, high_confidence = self.router.route_log(high_priority_log)
        
        # Test with a generic pattern
        generic_log = "An error occurred"
        _, generic_confidence = self.router.route_log(generic_log)
        
        # High priority pattern should have higher confidence
        self.assertGreater(high_confidence, generic_confidence)
    
    def test_routing_stats(self):
        """Test that routing statistics are updated."""
        # Route several logs
        logs = [
            "ModuleNotFoundError: No module named 'requests'",
            "Error response from daemon: pull access denied for myapp/image",
            "DeploymentFailed: Resource group 'my-group' could not be found"
        ]
        
        for log in logs:
            self.router.route_log(log)
        
        # Check that stats were updated
        stats = self.router.get_routing_stats()
        self.assertEqual(sum(stats.values()), len(logs))
    
    def test_python_context_extraction(self):
        """Test extraction of Python context from log."""
        log_content = "ModuleNotFoundError: No module named 'requests'"
        context = self.router.analyze_log_context(log_content)
        
        self.assertEqual(context["error_type"], "python_import_error")
        self.assertEqual(context["framework"], "python")
        self.assertEqual(context["specific_module"], "requests")
        self.assertIn("pip install requests", context["potential_fixes"])
    
    def test_docker_context_extraction(self):
        """Test extraction of Docker context from log."""
        log_content = "Error response from daemon: pull access denied for myapp/image"
        context = self.router.analyze_log_context(log_content)
        
        # This test expects "docker_error" even though the original code uses "docker_auth_error"
        # We've fixed the agent_router.py to standardize on "docker_error"
        self.assertEqual(context["error_type"], "docker_error")
        self.assertEqual(context["framework"], "docker")
        self.assertEqual(context["specific_issue"], "authentication")
        self.assertIn("docker login", context["potential_fixes"][0])
    
    def test_azure_context_extraction(self):
        """Test extraction of Azure context from log."""
        log_content = "DeploymentFailed: Resource group 'my-group' could not be found"
        context = self.router.analyze_log_context(log_content)
        
        self.assertEqual(context["error_type"], "azure_resource_error")
        self.assertEqual(context["framework"], "azure")
        self.assertIn("Create the missing resource group", context["potential_fixes"])
    
    def test_environment_detection(self):
        """Test environment detection from logs."""
        # Test production environment
        prod_log = "Failed to deploy to production environment"
        context = self.router.analyze_log_context(prod_log)
        self.assertEqual(context["environment"], "production")
        
        # Test staging environment
        staging_log = "Error in staging deployment"
        context = self.router.analyze_log_context(staging_log)
        self.assertEqual(context["environment"], "staging")
        
        # Test development environment
        dev_log = "Build failed in dev environment"
        context = self.router.analyze_log_context(dev_log)
        self.assertEqual(context["environment"], "development")


if __name__ == "__main__":
    unittest.main()