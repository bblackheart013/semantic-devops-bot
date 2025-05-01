from autogen import ConversableAgent
import logging
import json
from typing import Dict, List, Optional, Union, Any, Callable


class CoordinatorAgent(ConversableAgent):
    """
    Enhanced Coordinator Agent that routes tasks to appropriate specialist agents
    based on error type detection and maintains conversation history.
    """
    
    def __init__(
        self, 
        name: str = "Coordinator",
        system_message: Optional[str] = None,
        llm_config: Optional[Dict] = None,
        logger: Optional[logging.Logger] = None,
        error_types: Optional[List[str]] = None
    ):
        # Default error types if none provided
        self.error_types = error_types or [
            "build_error", 
            "deployment_error", 
            "azure_error", 
            "general_error"
        ]
        
        # Set up logging
        self.logger = logger or self._setup_logger()
        self.logger.info(f"Initializing CoordinatorAgent with name: {name}")
        
        # Default system message if none provided
        default_system_message = (
            "You are the central coordinator for a DevOps automation system. "
            "Your responsibilities include:\n"
            "1. Analyzing incoming error logs to determine the error type\n"
            "2. Routing tasks to the appropriate specialist agents\n"
            "3. Synthesizing responses from specialist agents\n"
            "4. Managing the overall conversation flow\n"
            "5. Ensuring all GitHub issues created contain actionable information\n\n"
            f"You work with specialist agents for these error types: {', '.join(self.error_types)}"
        )
        
        # Configure the coordinator
        coordinator_config = {
            "name": name,
            "system_message": system_message or default_system_message,
        }
        
        # Default LLM config if none provided
        default_llm_config = {
            "config_list": [{"model": "gpt-4o"}],
            "timeout": 120,
            "cache_seed": 42
        }

        
        # Initialize the GroupChatManager parent
        super().__init__(
            **coordinator_config,
            llm_config=llm_config or default_llm_config,
        )
        
        # Store conversation history
        self.conversation_history = []
        
        # Track registered specialist agents
        self.specialist_agents = {}
        
    def _setup_logger(self) -> logging.Logger:
        """Set up a custom logger for the coordinator agent."""
        logger = logging.getLogger(f"coordinator_agent")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
        
    def receive(self, message: str, sender: ConversableAgent, config: Optional[Dict] = None) -> None:
        """
        Enhanced receive method that logs messages and updates conversation history.
        
        Args:
            message: The message received
            sender: The agent that sent the message
            config: Additional configuration
        """
        self.logger.info(f"Received message from {sender.name}: {message[:50]}...")
        
        # Add to conversation history
        self.conversation_history.append({
            "sender": sender.name,
            "message": message,
            "timestamp": self._get_timestamp()
        })
        
        # Call the parent class receive method
        return super().receive(message, sender, config)
    
    def register_specialist(self, agent_type: str, agent: ConversableAgent) -> None:
        """
        Register a specialist agent with the coordinator.
        
        Args:
            agent_type: The type of agent (should match one of self.error_types)
            agent: The agent to register
        """
        if agent_type not in self.error_types:
            self.logger.warning(f"Registering unknown agent type: {agent_type}")
            self.error_types.append(agent_type)
            
        self.specialist_agents[agent_type] = agent
        self.logger.info(f"Registered {agent_type} specialist: {agent.name}")
    
    def detect_error_type(self, log_content: str) -> str:
        """
        Analyze log content to determine the most likely error type.
        This method can be enhanced with more sophisticated error detection.
        
        Args:
            log_content: The error log content to analyze
            
        Returns:
            The detected error type
        """
        # Simple keyword-based detection - could be replaced with ML model
        error_indicators = {
            "build_error": ["build failed", "compile error", "npm error", "yarn error", "package error"],
            "deployment_error": ["deployment failed", "release error", "container error", "kubernetes", "docker"],
            "azure_error": ["azure", "resource group", "app service", "function app", "cosmos db"]
        }
        
        # Count matches for each error type
        matches = {error_type: 0 for error_type in error_indicators}
        for error_type, keywords in error_indicators.items():
            for keyword in keywords:
                if keyword.lower() in log_content.lower():
                    matches[error_type] += 1
        
        # Get the error type with the most matches
        if max(matches.values(), default=0) > 0:
            return max(matches.items(), key=lambda x: x[1])[0]
        return "general_error"  # Default if no specific matches
    
    def route_to_specialist(self, error_type: str, log_content: str) -> Dict:
        """
        Route the log content to the appropriate specialist agent.
        
        Args:
            error_type: The detected error type
            log_content: The error log content
            
        Returns:
            The response from the specialist agent
        """
        if error_type not in self.specialist_agents:
            self.logger.warning(f"No specialist registered for {error_type}, using general handling")
            # Fall back to the coordinator's own analysis
            return {"status": "unrouted", "message": "No specialist available for this error type"}
        
        specialist = self.specialist_agents[error_type]
        self.logger.info(f"Routing {error_type} to specialist: {specialist.name}")
        
        # Initialize a chat with the specialist
        response = specialist.generate_reply(sender=self, message=log_content)
        
        return {
            "status": "routed",
            "specialist": specialist.name,
            "error_type": error_type,
            "response": response
        }
    
    def analyze_log(self, log_content: str) -> Dict:
        """
        High-level method to analyze a log file:
        1. Detect the error type
        2. Route to the appropriate specialist
        3. Return the analysis results
        
        Args:
            log_content: The error log content to analyze
            
        Returns:
            A dictionary with the analysis results
        """
        self.logger.info("Starting log analysis")
        
        # Detect the error type
        error_type = self.detect_error_type(log_content)
        self.logger.info(f"Detected error type: {error_type}")
        
        # Route to the specialist
        specialist_response = self.route_to_specialist(error_type, log_content)
        
        # Compile the full analysis
        analysis = {
            "error_type": error_type,
            "specialist": specialist_response.get("specialist", "none"),
            "analysis": specialist_response.get("response", "No specialist analysis available"),
            "timestamp": self._get_timestamp()
        }
        
        self.logger.info(f"Completed log analysis for {error_type}")
        return analysis
    
    def _get_timestamp(self) -> str:
        """Get a timestamp string for logging."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def get_conversation_history(self) -> List[Dict]:
        """
        Get the conversation history.
        
        Returns:
            The conversation history
        """
        return self.conversation_history
    
    def save_conversation_history(self, filename: str) -> None:
        """
        Save the conversation history to a file.
        
        Args:
            filename: The filename to save to
        """
        with open(filename, 'w') as f:
            json.dump(self.conversation_history, f, indent=2)
        self.logger.info(f"Saved conversation history to {filename}")


# Example usage:
if __name__ == "__main__":
    # Create the coordinator
    coordinator = CoordinatorAgent(
        name="DevOpsCoordinator",
        llm_config={"config_list": [{"model": "gpt-4o"}]}
    )
    
    # Register some specialist agents (these would be imported in a real scenario)
    # from build_error_agent import BuildErrorAgent
    # build_specialist = BuildErrorAgent()
    # coordinator.register_specialist("build_error", build_specialist)
    
    # Example log analysis
    # sample_log = "Error: Build failed: npm ERR! code ENOENT\nnpm ERR! syscall open\nnpm ERR! path /path/to/package.json"
    # analysis = coordinator.analyze_log(sample_log)
    # print(json.dumps(analysis, indent=2))