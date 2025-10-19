import json
from datetime import datetime
from typing import Any, Dict, Optional
from abc import ABC, abstractmethod


class BaseAgent(ABC):
    """
    Parent class for all agents in the workflow.
    Provides common functionality for logging, initialization, and execution.
    """
    
    def __init__(self, agent_id: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the base agent.
        
        Args:
            agent_id (str): Unique identifier for the agent
            config (dict, optional): Configuration dictionary containing tools, credentials, etc.
        """
        self.agent_id = agent_id
        self.config = config or {}
        self.tools = self.config.get('tools', [])
        self.instructions = self.config.get('instructions', '')
        self.logs = []
        
        self.log(f"Initializing {self.__class__.__name__} with ID: {agent_id}")
    
    def log(self, message: str, level: str = "INFO", data: Optional[Dict[str, Any]] = None):
        """
        Log messages with timestamp for debugging and tracking.
        
        Args:
            message (str): Log message
            level (str): Log level (INFO, WARNING, ERROR, SUCCESS)
            data (dict, optional): Additional data to log
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "agent_id": self.agent_id,
            "level": level,
            "message": message
        }
        
        if data:
            log_entry["data"] = data
        
        self.logs.append(log_entry)
        
        # Color coding for console output
        color_codes = {
            "INFO": "\033[94m",      # Blue
            "SUCCESS": "\033[92m",   # Green
            "WARNING": "\033[93m",   # Yellow
            "ERROR": "\033[91m",     # Red
            "RESET": "\033[0m"       # Reset
        }
        
        color = color_codes.get(level, color_codes["INFO"])
        reset = color_codes["RESET"]
        
        # Print formatted log
        print(f"{color}[{timestamp}] [{level}] [{self.agent_id}]{reset} {message}")
        
        # Print additional data if provided
        if data:
            print(f"  └─ Data: {json.dumps(data, indent=2)}")
    
    @abstractmethod
    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's main logic.
        This method must be overridden by all sub-agents.
        
        Args:
            inputs (dict): Input data for the agent
            
        Returns:
            dict: Output data from the agent
            
        Raises:
            NotImplementedError: If not implemented by sub-agent
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement the run() method"
        )
    
    def validate_inputs(self, inputs: Dict[str, Any], required_fields: list) -> bool:
        """
        Helper method to validate required input fields.
        
        Args:
            inputs (dict): Input data to validate
            required_fields (list): List of required field names
            
        Returns:
            bool: True if valid, False otherwise
        """
        missing_fields = [field for field in required_fields if field not in inputs]
        
        if missing_fields:
            self.log(
                f"Missing required input fields: {missing_fields}",
                level="ERROR",
                data={"missing": missing_fields, "received": list(inputs.keys())}
            )
            return False
        
        self.log("Input validation passed", level="SUCCESS")
        return True
    
    def get_tool_config(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve configuration for a specific tool.
        
        Args:
            tool_name (str): Name of the tool
            
        Returns:
            dict: Tool configuration or None if not found
        """
        for tool in self.tools:
            if tool.get('name') == tool_name:
                self.log(f"Retrieved config for tool: {tool_name}")
                return tool.get('config', {})
        
        self.log(f"Tool not found: {tool_name}", level="WARNING")
        return None
    
    def export_logs(self) -> list:
        """
        Export all logs for this agent.
        
        Returns:
            list: List of log entries
        """
        return self.logs
    
    def __repr__(self) -> str:
        """String representation of the agent."""
        return f"{self.__class__.__name__}(id={self.agent_id})"