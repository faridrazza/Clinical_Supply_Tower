"""
Base agent class with common functionality.
"""
import logging
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for all agents."""
    
    def __init__(self, name: str, llm=None):
        """
        Initialize base agent.
        
        Args:
            name: Agent name
            llm: Language model instance (optional)
        """
        self.name = name
        self.llm = llm
        self.logger = logging.getLogger(f"agent.{name}")
    
    @abstractmethod
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agent logic.
        
        Args:
            input_data: Input data dictionary
            
        Returns:
            Output data dictionary
        """
        pass
    
    def log_execution(self, input_data: Dict[str, Any], output_data: Dict[str, Any]):
        """Log agent execution."""
        self.logger.info(f"{self.name} executed")
        self.logger.debug(f"Input: {input_data}")
        self.logger.debug(f"Output: {output_data}")
    
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle agent errors.
        
        Args:
            error: Exception that occurred
            context: Additional context
            
        Returns:
            Error response dictionary
        """
        from src.utils.error_handlers import AgentErrorHandler
        
        return AgentErrorHandler.handle_agent_failure(
            agent_name=self.name,
            error=error,
            context=context
        )
