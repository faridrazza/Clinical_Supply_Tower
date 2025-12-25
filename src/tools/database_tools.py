"""
Database tools for executing SQL queries and managing connections.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from src.config.settings import settings

logger = logging.getLogger(__name__)


class DatabaseTools:
    """Tools for database operations."""
    
    def __init__(self, database_url: Optional[str] = None):
        """Initialize database connection."""
        self.database_url = database_url or settings.database_url
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = psycopg2.connect(self.database_url)
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def execute_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute SQL query and return results.
        
        Args:
            query: SQL query string
            params: Query parameters for parameterized queries
            timeout: Query timeout in seconds
            
        Returns:
            Dictionary with results or error information
        """
        timeout = timeout or settings.query_timeout
        
        try:
            with self.get_connection() as conn:
                # Set statement timeout
                with conn.cursor() as cur:
                    cur.execute(f"SET statement_timeout = {timeout * 1000}")
                
                # Execute query
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    if params:
                        cur.execute(query, params)
                    else:
                        cur.execute(query)
                    
                    # Fetch results
                    if cur.description:  # SELECT query
                        results = cur.fetchall()
                        columns = [desc[0] for desc in cur.description]
                        
                        return {
                            "success": True,
                            "data": [dict(row) for row in results],
                            "columns": columns,
                            "row_count": len(results),
                            "query": query,
                            "executed_at": datetime.now().isoformat()
                        }
                    else:  # INSERT/UPDATE/DELETE
                        return {
                            "success": True,
                            "rows_affected": cur.rowcount,
                            "query": query,
                            "executed_at": datetime.now().isoformat()
                        }
        
        except psycopg2.Error as e:
            logger.error(f"Database error: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_code": e.pgcode,
                "error_type": type(e).__name__,
                "query": query,
                "executed_at": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "query": query,
                "executed_at": datetime.now().isoformat()
            }
    
    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """
        Get schema information for a specific table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dictionary with schema information
        """
        query = """
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default,
            character_maximum_length
        FROM information_schema.columns
        WHERE table_name = %s
        ORDER BY ordinal_position;
        """
        
        result = self.execute_query(query, (table_name,))
        
        if result["success"]:
            return {
                "table_name": table_name,
                "columns": result["data"],
                "column_count": result["row_count"]
            }
        else:
            return {"error": result["error"]}
    
    def get_all_tables(self) -> List[str]:
        """Get list of all tables in the database."""
        query = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_type = 'BASE TABLE'
        ORDER BY table_name;
        """
        
        result = self.execute_query(query)
        
        if result["success"]:
            return [row["table_name"] for row in result["data"]]
        else:
            return []
    
    def get_sample_data(self, table_name: str, limit: int = 5) -> Dict[str, Any]:
        """
        Get sample data from a table.
        
        Args:
            table_name: Name of the table
            limit: Number of rows to return
            
        Returns:
            Dictionary with sample data
        """
        query = f'SELECT * FROM "{table_name}" LIMIT {limit};'
        return self.execute_query(query)
    
    def validate_query_syntax(self, query: str) -> Dict[str, Any]:
        """
        Validate SQL query syntax without executing it.
        
        Args:
            query: SQL query to validate
            
        Returns:
            Dictionary with validation result
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Use EXPLAIN to validate without executing
                    cur.execute(f"EXPLAIN {query}")
                    return {
                        "valid": True,
                        "message": "Query syntax is valid"
                    }
        except psycopg2.Error as e:
            return {
                "valid": False,
                "error": str(e),
                "error_code": e.pgcode
            }
    
    def get_table_row_count(self, table_name: str) -> int:
        """Get approximate row count for a table."""
        query = f'SELECT COUNT(*) as count FROM "{table_name}";'
        result = self.execute_query(query)
        
        if result["success"] and result["data"]:
            return result["data"][0]["count"]
        return 0


# Global database tools instance
db_tools = DatabaseTools()


def run_sql_query(
    query: str,
    params: Optional[Dict[str, Any]] = None,
    timeout: Optional[int] = None
) -> Dict[str, Any]:
    """
    Convenience function to execute SQL queries.
    
    This is the primary tool used by agents to query the database.
    
    Args:
        query: SQL query string
        params: Query parameters
        timeout: Query timeout in seconds
        
    Returns:
        Dictionary with query results or error information
    """
    return db_tools.execute_query(query, params, timeout)


def get_schema_info(table_name: str) -> Dict[str, Any]:
    """
    Get schema information for a table.
    
    Args:
        table_name: Name of the table
        
    Returns:
        Dictionary with schema information
    """
    return db_tools.get_table_schema(table_name)


def list_all_tables() -> List[str]:
    """Get list of all tables in the database."""
    return db_tools.get_all_tables()


def fuzzy_match_table_name(partial_name: str) -> Optional[str]:
    """
    Find best matching table name using PostgreSQL similarity.
    
    Handles edge cases like "Trial ABC" vs "Trial_ABC_v2"
    """
    query = """
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND similarity(table_name, %s) > 0.3
    ORDER BY similarity(table_name, %s) DESC
    LIMIT 1;
    """
    
    result = db_tools.execute_query(query, (partial_name, partial_name))
    
    if result["success"] and result["data"]:
        return result["data"][0]["table_name"]
    return None


def search_tables_by_keyword(keyword: str) -> List[str]:
    """Search for tables matching a keyword."""
    query = """
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name ILIKE %s
    ORDER BY table_name;
    """
    
    search_pattern = f"%{keyword}%"
    result = db_tools.execute_query(query, (search_pattern,))
    
    if result["success"]:
        return [row["table_name"] for row in result["data"]]
    return []
