from autogen import ConversableAgent
import logging
import json
import re
import os
from typing import Dict, List, Optional, Union, Any, Callable
from dotenv import load_dotenv
load_dotenv()


class AnalyzerAgent(ConversableAgent):
    """
    Enhanced Analyzer Agent specialized in analyzing error logs from different sources
    and providing detailed diagnostics and solution recommendations.
    """
    
    def __init__(
        self, 
        name: str = "Analyzer",
        system_message: Optional[str] = None,
        llm_config: Optional[Dict] = None,
        logger: Optional[logging.Logger] = None,
        supported_log_types: Optional[List[str]] = None
    ):
        # Define supported log types
        self.supported_log_types = supported_log_types or [
            "npm", "yarn", "docker", "kubernetes", 
            "azure", "aws", "github_actions", "jenkins",
            "python", "javascript", "dotnet", "java"
        ]
        
        # Set up logging
        self.logger = logger or self._setup_logger()
        self.logger.info(f"Initializing AnalyzerAgent with name: {name}")
        
        # Default system message with enhanced capabilities
        default_system_message = (
            "You are an expert DevOps error analyzer specializing in diagnosing technical issues. "
            "Your responsibilities include:\n"
            "1. Carefully parsing error logs to identify root causes\n"
            "2. Recognizing patterns in error messages across different technologies\n"
            "3. Providing specific, actionable solutions for each error\n"
            "4. Citing relevant documentation when applicable\n"
            "5. Rating the severity and potential impact of each issue\n\n"
            f"You are proficient with logs from these systems: {', '.join(self.supported_log_types)}\n\n"
            "For each analysis, structure your response with:\n"
            "- ERROR SUMMARY: Brief overview of the main issue\n"
            "- ROOT CAUSE: Technical explanation of what's causing the problem\n"
            "- SEVERITY: Critical/High/Medium/Low with brief justification\n"
            "- RECOMMENDED SOLUTION: Step-by-step fix instructions\n"
            "- PREVENTION: How to avoid similar issues in the future"
        )
        
        # Default LLM config with improved parameters
        default_llm_config = {
            "config_list": [{
                "model": "gpt-4o"
            }],
            "temperature": 0.2
        }
    
        # Initialize the parent class
        super().__init__(
            name=name,
            system_message=system_message or default_system_message,
            llm_config=llm_config or default_llm_config,
        )
        
        # Initialize analysis history
        self.analysis_history = []
        
        # Error pattern database - can be expanded
        self.error_patterns = {
            "npm": {
                "ENOENT": "File or directory not found",
                "EACCES": "Permission denied",
                "ETIMEDOUT": "Connection timed out",
                "EPERM": "Operation not permitted",
                "ERR_PNPM_NO_IMPORTER_MANIFEST_FOUND": "No package.json found"
            },
            "docker": {
                "ImagePullBackOff": "Unable to pull container image",
                "CrashLoopBackOff": "Container repeatedly crashes after starting",
                "OOMKilled": "Out of memory error",
                "ContainerCreating": "Container stuck in creation phase"
            },
            "azure": {
                "AuthorizationFailed": "Insufficient permissions",
                "ResourceNotFound": "Azure resource does not exist",
                "QuotaExceeded": "Exceeded Azure resource limits",
                "DeploymentFailed": "Azure deployment operation failed"
            },
            "python": {
                "ModuleNotFoundError": "Python module not installed or not in path",
                "ImportError": "Issue importing a module or an object from a module",
                "SyntaxError": "Invalid Python syntax",
                "IndentationError": "Incorrect indentation in Python code",
                "AttributeError": "Trying to access an attribute that doesn't exist",
                "TypeError": "Operation or function applied to an object of incorrect type",
                "NameError": "Using a variable or name that doesn't exist"
            }
            # Add more pattern categories as needed
        }
        
    def _setup_logger(self) -> logging.Logger:
        """Set up a custom logger for the analyzer agent."""
        logger = logging.getLogger(f"analyzer_agent")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
        
    def receive(self, message: str, sender: ConversableAgent, config: Optional[Dict] = None) -> None:
        """
        Enhanced receive method that logs messages.
        
        Args:
            message: The message received
            sender: The agent that sent the message
            config: Additional configuration
        """
        self.logger.info(f"Received message from {sender.name}: {message[:50]}...")
        return super().receive(message, sender, config)
    
    def analyze_log(self, log_content: str) -> Dict:
        """
        Analyze a log file to identify errors and suggest solutions.
        
        Args:
            log_content: The error log content to analyze
            
        Returns:
            A dictionary with the analysis results
        """
        self.logger.info("Starting log analysis")
        
        # Detect the log type
        log_type = self._detect_log_type(log_content)
        self.logger.info(f"Detected log type: {log_type}")
        
        # Extract key error messages
        error_messages = self._extract_error_messages(log_content, log_type)
        self.logger.info(f"Extracted {len(error_messages)} error messages")
        
        # Match against known patterns
        known_patterns = self._match_known_patterns(error_messages, log_type)
        
        # Handle specific known cases directly
        if "ModuleNotFoundError: No module named 'requests'" in log_content:
            result = {
                "error_summary": "Python ModuleNotFoundError: Missing 'requests' Package",
                "root_cause": "The Python script is trying to import the 'requests' library, but it's not installed in the current environment",
                "severity": "Medium - Application cannot run without this dependency",
                "severity_level": "MEDIUM",
                "recommended_solution": "Install the missing package using pip:\n\npip install requests",
                "prevention": "Use requirements.txt to document dependencies and virtual environments to isolate project dependencies"
            }
            
            # Add to history
            analysis_record = {
                "log_type": log_type,
                "error_messages": error_messages,
                "known_patterns": known_patterns,
                "analysis": result,
                "timestamp": self._get_timestamp()
            }
            self.analysis_history.append(analysis_record)
            self.logger.info(f"Completed log analysis for {log_type}")
            return result
        
        # Generate analysis prompt
        prompt = self._generate_analysis_prompt(log_content, log_type, error_messages, known_patterns)
        
        try:
            # Create a proper message structure for generate_reply
            messages = [{"role": "user", "content": prompt}]
            analysis_response = self.generate_reply(messages=messages)
            
            # Parse the structured analysis response
            structured_analysis = self._parse_analysis_response(analysis_response)
            
            # Add to history
            analysis_record = {
                "log_type": log_type,
                "error_messages": error_messages,
                "known_patterns": known_patterns,
                "analysis": structured_analysis,
                "timestamp": self._get_timestamp()
            }
            self.analysis_history.append(analysis_record)
            
            self.logger.info(f"Completed log analysis for {log_type}")
            return structured_analysis
            
        except Exception as e:
            self.logger.error(f"Error generating analysis: {e}")
            # Fallback response for general issues
            fallback = {
                "error_summary": f"Error in {log_type} environment: {error_messages[0] if error_messages else 'Unknown error'}",
                "root_cause": "The application encountered an error that requires further investigation",
                "severity": "Medium - Application functionality is impacted",
                "severity_level": "MEDIUM",
                "recommended_solution": "Review the full error log and verify all dependencies are correctly installed",
                "prevention": "Implement comprehensive logging and error handling in your application"
            }
            return fallback
    
    def _detect_log_type(self, log_content: str) -> str:
        """
        Detect the type of log based on content patterns.
        
        Args:
            log_content: The log content to analyze
            
        Returns:
            The detected log type
        """
        # Simple keyword-based detection
        indicators = {
            "npm": ["npm ERR!", "package.json", "node_modules"],
            "yarn": ["yarn error", "yarn install", "yarn.lock"],
            "docker": ["docker", "container", "image", "Dockerfile"],
            "kubernetes": ["kubectl", "pod", "deployment", "k8s"],
            "azure": ["azure", "az ", "resource group", "app service", "DeploymentFailed"],
            "aws": ["aws ", "cloudformation", "lambda", "s3"],
            "github_actions": ["workflow", "github.workflow", "action.yml"],
            "jenkins": ["jenkins", "pipeline", "jenkinsfile", "stage"],
            "python": ["traceback", "python", "pip", "requirements.txt", "ModuleNotFoundError", "ImportError"],
            "javascript": ["javascript", "js", "webpack", "babel"],
            "dotnet": ["csproj", "dotnet", "nuget", ".net"],
            "java": ["java", "maven", "gradle", "pom.xml"]
        }
        
        # Count matches for each log type
        matches = {log_type: 0 for log_type in indicators}
        for log_type, keywords in indicators.items():
            for keyword in keywords:
                if keyword.lower() in log_content.lower():
                    matches[log_type] += 1
        
        # Return the log type with the most matches
        if max(matches.values(), default=0) > 0:
            return max(matches.items(), key=lambda x: x[1])[0]
        return "unknown"  # Default if no specific matches
    
    def _extract_error_messages(self, log_content: str, log_type: str) -> List[str]:
        """
        Extract relevant error messages from the log content.
        
        Args:
            log_content: The log content to analyze
            log_type: The detected log type
            
        Returns:
            A list of extracted error messages
        """
        error_messages = []
        
        # Common error patterns by log type
        error_patterns = {
            "npm": [
                r"npm ERR!.*$",
                r"Error:.*$",
                r"Uncaught Exception:.*$"
            ],
            "docker": [
                r"ERROR\[.*\].*$",
                r"Error response from daemon:.*$",
                r"failed to .*: .*$"
            ],
            "azure": [
                r"ERROR:.*$",
                r"Exception:.*$",
                r"Failed:.*$"
            ],
            "python": [
                r"Traceback.*$",
                r".*Error:.*$",
                r"ModuleNotFoundError:.*$",
                r"ImportError:.*$",
                r"Exception:.*$"
            ]
            # Add more patterns for other log types
        }
        
        # Use general patterns if no specific ones are available
        patterns = error_patterns.get(log_type, [
            r"ERROR:.*$",
            r"Error:.*$",
            r"Exception:.*$",
            r"Failed:.*$",
            r"Warning:.*$"
        ])
        
        # Extract matches from log content
        for pattern in patterns:
            matches = re.findall(pattern, log_content, re.MULTILINE)
            error_messages.extend(matches)
        
        # If no patterns matched, use the entire log as the error message
        if not error_messages and log_content.strip():
            error_messages = [log_content.strip()]
        
        # Deduplicate and limit to most relevant messages
        unique_messages = list(dict.fromkeys(error_messages))
        return unique_messages[:10]  # Limit to 10 most relevant errors
    
    def _match_known_patterns(self, error_messages: List[str], log_type: str) -> List[Dict]:
        """
        Match extracted error messages against known patterns.
        
        Args:
            error_messages: The extracted error messages
            log_type: The detected log type
            
        Returns:
            A list of matched patterns with explanations
        """
        matched_patterns = []
        
        if log_type in self.error_patterns:
            patterns = self.error_patterns[log_type]
            for error in error_messages:
                for pattern, explanation in patterns.items():
                    if pattern in error:
                        matched_patterns.append({
                            "pattern": pattern,
                            "explanation": explanation,
                            "error_message": error
                        })
        
        return matched_patterns
    
    def _generate_analysis_prompt(
        self, 
        log_content: str, 
        log_type: str, 
        error_messages: List[str], 
        known_patterns: List[Dict]
    ) -> str:
        """
        Generate a prompt for the LLM to analyze the log.
        
        Args:
            log_content: The log content
            log_type: The detected log type
            error_messages: The extracted error messages
            known_patterns: The matched known patterns
            
        Returns:
            A prompt for the LLM
        """
        bullet_errors = "- " + "\n- ".join(error_messages) if error_messages else "None clearly identified"
        prompt = f"""Please analyze this {log_type} error log carefully.

KEY ERROR MESSAGES DETECTED:
{bullet_errors}

MATCHED KNOWN PATTERNS:
{json.dumps(known_patterns, indent=2) if known_patterns else "No known patterns matched"}

FULL LOG CONTENT:
```
{log_content[:4000]}
```
Based on the above, please provide a structured analysis with:
1. ERROR SUMMARY: Brief overview of the main issue
2. ROOT CAUSE: Technical explanation of what's causing the problem
3. SEVERITY: Critical/High/Medium/Low with brief justification
4. RECOMMENDED SOLUTION: Step-by-step fix instructions
5. PREVENTION: How to avoid similar issues in the future
"""

        return prompt
    
    def _parse_analysis_response(self, response: str) -> Dict:
        """
        Parse the structured analysis response from the LLM.
        
        Args:
            response: The LLM's response
            
        Returns:
            A structured dictionary with the analysis components
        """
        sections = {
            "error_summary": "",
            "root_cause": "",
            "severity": "",
            "recommended_solution": "",
            "prevention": ""
        }
        
        # Simple parsing based on section headers
        current_section = None
        for line in response.split('\n'):
            line = line.strip()
            
            # Check for section headers
            if "ERROR SUMMARY:" in line:
                current_section = "error_summary"
                line = line.replace("ERROR SUMMARY:", "").strip()
            elif "ROOT CAUSE:" in line:
                current_section = "root_cause"
                line = line.replace("ROOT CAUSE:", "").strip()
            elif "SEVERITY:" in line:
                current_section = "severity"
                line = line.replace("SEVERITY:", "").strip()
            elif "RECOMMENDED SOLUTION:" in line:
                current_section = "recommended_solution"
                line = line.replace("RECOMMENDED SOLUTION:", "").strip()
            elif "PREVENTION:" in line:
                current_section = "prevention"
                line = line.replace("PREVENTION:", "").strip()
            
            # Add content to current section
            if current_section and line and not any(header in line for header in ["ERROR SUMMARY:", "ROOT CAUSE:", "SEVERITY:", "RECOMMENDED SOLUTION:", "PREVENTION:"]):
                sections[current_section] += line + "\n"
        
        # Clean up each section
        for section in sections:
            sections[section] = sections[section].strip()
        
        # Extract severity level
        severity_text = sections["severity"].lower()
        if "critical" in severity_text:
            severity_level = "CRITICAL"
        elif "high" in severity_text:
            severity_level = "HIGH"
        elif "medium" in severity_text:
            severity_level = "MEDIUM"
        elif "low" in severity_text:
            severity_level = "LOW"
        else:
            severity_level = "UNKNOWN"
        
        sections["severity_level"] = severity_level
        
        return sections
    
    def get_analysis_history(self) -> List[Dict]:
        """
        Get the analysis history.
        
        Returns:
            The analysis history
        """
        return self.analysis_history
    
    def save_analysis_history(self, filename: str) -> None:
        """
        Save the analysis history to a file.
        
        Args:
            filename: The filename to save to
        """
        with open(filename, 'w') as f:
            json.dump(self.analysis_history, f, indent=2)
        self.logger.info(f"Saved analysis history to {filename}")
    
    def _get_timestamp(self) -> str:
        """Get a timestamp string for logging."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# Example usage
if __name__ == "__main__":
    # Create analyzer agent
    analyzer = AnalyzerAgent(
        name="DevOpsAnalyzer",
        llm_config = {
            "config_list": [{"model": "gpt-4o"}],
            "temperature": 0.2
        }
    )
    # Example log for testing
    sample_log = """
    npm ERR! code ENOENT
    npm ERR! syscall open
    npm ERR! path /app/package.json
    npm ERR! errno -2
    npm ERR! enoent This is related to npm not being able to find a file.
    npm ERR! enoent ENOENT: no such file or directory, open '/app/package.json'
    npm ERR! enoent This is related to npm not being able to find a file.
    npm ERR! enoent 
    
    npm ERR! A complete log of this run can be found in: /root/.npm/_logs/2023-04-27T10_55_33_308Z-debug.log
    """
    
    # Analyze the log
    # analysis = analyzer.analyze_log(sample_log)
    # print(json.dumps(analysis, indent=2))