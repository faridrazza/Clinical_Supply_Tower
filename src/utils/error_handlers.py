"""
Error handling utilities for graceful failure management.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class SQLErrorHandler:
    """Handles SQL errors with user-friendly translations."""
    
    ERROR_TRANSLATIONS = {
        "42P01": "Table does not exist",
        "42703": "Column does not exist",
        "42601": "Syntax error in SQL query",
        "42804": "Data type mismatch",
        "23505": "Duplicate key violation",
        "23503": "Foreign key violation",
        "57014": "Query timeout exceeded",
    }
    
    @staticmethod
    def translate_error(error_code: str, error_message: str) -> str:
        """
        Translate PostgreSQL error to user-friendly message.
        
        Args:
            error_code: PostgreSQL error code
            error_message: Raw error message
            
        Returns:
            User-friendly error message
        """
        base_translation = SQLErrorHandler.ERROR_TRANSLATIONS.get(
            error_code,
            "Database error occurred"
        )
        
        # Extract relevant details from error message
        if "column" in error_message.lower():
            # Extract column name
            import re
            match = re.search(r'column "([^"]+)"', error_message)
            if match:
                column_name = match.group(1)
                return f"{base_translation}: '{column_name}'"
        
        if "table" in error_message.lower():
            # Extract table name
            import re
            match = re.search(r'table "([^"]+)"', error_message)
            if match:
                table_name = match.group(1)
                return f"{base_translation}: '{table_name}'"
        
        return base_translation
    
    @staticmethod
    def suggest_fix(error_code: str, error_message: str, query: str) -> Optional[str]:
        """
        Suggest potential fix for SQL error.
        
        Args:
            error_code: PostgreSQL error code
            error_message: Raw error message
            query: Original SQL query
            
        Returns:
            Suggested fix or None
        """
        if error_code == "42703":  # Column does not exist
            return "Check the table schema for correct column names. Column names may be case-sensitive."
        
        if error_code == "42P01":  # Table does not exist
            return "Verify the table name is correct. Use double quotes for table names with special characters."
        
        if error_code == "42601":  # Syntax error
            return "Review SQL syntax. Common issues: missing commas, unmatched parentheses, incorrect keywords."
        
        if error_code == "57014":  # Timeout
            return "Query took too long. Consider adding WHERE clauses to filter data or using LIMIT."
        
        return None


class AgentErrorHandler:
    """Handles agent-level errors and failures."""
    
    @staticmethod
    def handle_agent_failure(
        agent_name: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle agent failure with logging and user-friendly response.
        
        Args:
            agent_name: Name of the failed agent
            error: Exception that occurred
            context: Additional context information
            
        Returns:
            Error response dictionary
        """
        logger.error(f"Agent {agent_name} failed: {str(error)}", exc_info=True)
        
        return {
            "success": False,
            "agent": agent_name,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.now().isoformat(),
            "context": context or {},
            "user_message": f"I encountered an issue while processing your request. The {agent_name} experienced an error. Please try rephrasing your question or contact support if the issue persists."
        }
    
    @staticmethod
    def handle_missing_data(
        entity_type: str,
        entity_value: str,
        tables_checked: List[str]
    ) -> str:
        """
        Generate user-friendly message for missing data.
        
        Args:
            entity_type: Type of entity (batch, material, etc.)
            entity_value: Value that was not found
            tables_checked: List of tables that were checked
            
        Returns:
            User-friendly message
        """
        message = f"I couldn't find {entity_type} '{entity_value}' in the system.\n\n"
        message += "What I checked:\n"
        
        for table in tables_checked:
            message += f"- {table}: No record\n"
        
        message += "\nPossible reasons:\n"
        message += f"1. {entity_type.capitalize()} may be formatted differently\n"
        message += f"2. {entity_type.capitalize()} fully consumed and archived\n"
        message += f"3. {entity_type.capitalize()} belongs to different study not in database\n"
        
        return message
    
    @staticmethod
    def handle_conflicting_data(
        entity: str,
        conflicts: List[Dict[str, Any]]
    ) -> str:
        """
        Generate message for conflicting data scenarios.
        
        Args:
            entity: Entity with conflicting data
            conflicts: List of conflicting data sources
            
        Returns:
            User-friendly message explaining conflicts
        """
        message = f"I found conflicting data for {entity}:\n\n"
        
        for i, conflict in enumerate(conflicts, 1):
            message += f"Source {i} - {conflict['table']} "
            if 'updated' in conflict:
                message += f"(updated: {conflict['updated']})"
            message += f": {conflict['value']}\n"
        
        message += "\nNote: Data discrepancies may indicate recent updates not yet synchronized across all systems. "
        message += "Use the most recent source for critical decisions.\n"
        
        return message


def format_error_for_user(error: Dict[str, Any]) -> str:
    """
    Format error dictionary into user-friendly message.
    
    Args:
        error: Error dictionary
        
    Returns:
        Formatted error message
    """
    if error.get("user_message"):
        return error["user_message"]
    
    if error.get("error_type") == "TimeoutError":
        return "The query took too long to execute. Please try a more specific query or contact support."
    
    if error.get("error_type") == "ConnectionError":
        return "Unable to connect to the database. Please try again in a moment."
    
    return "An unexpected error occurred. Please try again or contact support if the issue persists."
