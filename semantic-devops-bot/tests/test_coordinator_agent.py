import unittest
from unittest.mock import patch, Mock
import logging
import sys
import os
import tempfile

# Adjust the Python path to include the project root directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now we can import our modules correctly
try:
    from agents.coordinator_agent import CoordinatorAgent
except ImportError:
    # Fallback direct import for when running tests directly
    from coordinator_agent import CoordinatorAgent


class TestCoordinatorAgent(unittest.TestCase):
    """Test cases for the CoordinatorAgent class."""
    
    def setUp(self):
        """Set up the test environment."""
        # Configure a test logger
        self.logger = logging.getLogger("test_logger")
        self.logger.setLevel(logging.DEBUG)
        # Use a null handler to prevent log output during tests
        self.logger.addHandler(logging.NullHandler())
        
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a test coordinator agent with dry run mode enabled
        self.coordinator = CoordinatorAgent(
            name="TestCoordinator",
            logger=self.logger,
            save_directory=self.temp_dir,
            dry_run=True
        )
        
        # Create mock specialist agents
        self.build_agent = Mock()
        self.build_agent.name = "BuildAgent"
        self.deployment_agent = Mock()
        self.deployment_agent.name = "DeploymentAgent"
        self.azure_agent = Mock()
        self.azure_agent.name = "AzureAgent"
        
        # Register the mock specialists
        self.coordinator.register_specialist("build_error", self.build_agent)
        self.coordinator.register_specialist("deployment_error", self.deployment_agent)
        self.coordinator.register_specialist("azure_error", self.azure_agent)
    
    def tearDown(self):
        """Clean up after the tests."""
        # Clean up any temporary files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init(self):
        """Test coordinator initialization."""
        self.assertEqual(self.coordinator.name, "TestCoordinator")
        self.assertTrue(self.coordinator.dry_run)
        self.assertEqual(len(self.coordinator.specialist_agents), 3)
    
    def test_register_specialist(self):
        """Test registering a specialist agent."""
        # Create a new mock agent
        new_agent = Mock()
        new_agent.name = "NewAgent"
        
        # Register the new agent
        self.coordinator.register_specialist("new_error", new_agent)
        
        # Check that the agent was registered
        self.assertIn("new_error", self.coordinator.specialist_agents)
        self.assertEqual(self.coordinator.specialist_agents["new_error"], new_agent)
    
    def test_detect_error_type(self):
        """Test error type detection."""
        # Test with a Python import error
        log_content = "ModuleNotFoundError: No module named 'requests'"
        error_type, confidence = self.coordinator.detect_error_type(log_content)
        self.assertEqual(error_type, "build_error")
        self.assertGreater(confidence, 0.5)
        
        # Test with a deployment error
        log_content = "Error response from daemon: pull access denied for myapp/image"
        error_type, confidence = self.coordinator.detect_error_type(log_content)
        self.assertEqual(error_type, "deployment_error")
        self.assertGreater(confidence, 0.5)
        
        # Test with an Azure error
        log_content = "DeploymentFailed: Resource group 'my-group' could not be found"
        error_type, confidence = self.coordinator.detect_error_type(log_content)
        self.assertEqual(error_type, "azure_error")
        self.assertGreater(confidence, 0.5)
        
        # Test with a generic error
        log_content = "Something went wrong with no clear error type"
        error_type, confidence = self.coordinator.detect_error_type(log_content)
        self.assertEqual(error_type, "general_error")
    
    def test_get_log_context(self):
        """Test extracting context from logs."""
        # Test Python import error context
        log_content = "ModuleNotFoundError: No module named 'requests'"
        context = self.coordinator.get_log_context(log_content)
        self.assertEqual(context["error_type"], "python_import_error")
        self.assertEqual(context["framework"], "python")
        self.assertEqual(context["specific_module"], "requests")
        self.assertIn("pip install requests", context["potential_fixes"])
    
    def test_route_to_specialist(self):
        """Test routing logs to specialists."""
        # Test routing a build error
        log_content = "ModuleNotFoundError: No module named 'requests'"
        response = self.coordinator.route_to_specialist("build_error", log_content)
        self.assertEqual(response["status"], "dry_run")
        self.assertEqual(response["specialist"], "BuildAgent")
        self.assertEqual(response["error_type"], "build_error")
    
    def test_analyze_log(self):
        """Test the complete log analysis process."""
        # Test analyzing a Python import error
        log_content = "ModuleNotFoundError: No module named 'requests'"
        analysis = self.coordinator.analyze_log(log_content)
        self.assertEqual(analysis["error_type"], "build_error")
        self.assertEqual(analysis["specialist"], "BuildAgent")
        self.assertEqual(analysis["status"], "dry_run")
    
    def test_unknown_error_type(self):
        """Test handling of unknown error types."""
        # Test routing an unknown error type
        with self.assertLogs(self.logger, level='WARNING') as log:
            response = self.coordinator.route_to_specialist("nonexistent_error", "Some error")
            self.assertIn("No specialist registered for nonexistent_error", log.output[0])
    
    def test_conversation_history(self):
        """Test conversation history management."""
        # Send a message to the coordinator
        sender = Mock()
        sender.name = "TestSender"
        self.coordinator.receive("Test message", sender)
        
        # Check that the message was added to the history
        history = self.coordinator.get_conversation_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["sender"], "TestSender")
        self.assertEqual(history[0]["message"], "Test message")
    
    def test_save_conversation_history(self):
        """Test saving conversation history to a file."""
        # Add a message to the history
        sender = Mock()
        sender.name = "TestSender"
        self.coordinator.receive("Test message", sender)
        
        # Save the history to a file
        filepath = self.coordinator.save_conversation_history(compress=True)
        
        # Check that the file exists
        self.assertTrue(os.path.exists(filepath))
        self.assertTrue(filepath.endswith('.json.gz'))


if __name__ == "__main__":
    unittest.main()