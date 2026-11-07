from database import db
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def sql_db_list_tables(input_data: str = "") -> str:
    """
    Tool to list all tables in the database.
    Input: empty string
    Output: comma-separated list of tables
    """
    logger.info("Tool: sql_db_list_tables called")
    try:
        result = db.list_tables()
        result_str = str(result)[:200] if result is not None else 'empty'
        logger.info(f"Tool: sql_db_list_tables result: {result_str}")
        return result
    except Exception as e:
        error_msg = f"Error listing tables: {str(e)}"
        logger.error(error_msg)
        return error_msg


def sql_db_schema(input_data: str) -> str:
    """
    Tool to get schema and sample rows for specified tables.
    Input: comma-separated list of table names (e.g., "table1, table2, table3")
    Output: schema information with sample data
    """
    # Handle if input_data is a dict
    if isinstance(input_data, dict):
        input_data = input_data.get("input", "")

    input_str = str(input_data)[:100] if input_data is not None else 'empty'
    logger.info(f"Tool: sql_db_schema called with input: {input_str}")
    try:
        if not input_data or not str(input_data).strip():
            return "Error: No table names provided. Please provide a comma-separated list of table names."

        result = db.get_schema(str(input_data))
        logger.info(f"Tool: sql_db_schema result retrieved")
        return result
    except Exception as e:
        error_msg = f"Error getting schema: {str(e)}"
        logger.error(error_msg)
        return error_msg


def sql_db_query(input_data: str) -> str:
    """
    Tool to execute a SQL query.
    Input: detailed and correct SQL query
    Output: result from the database or error message
    """
    # Handle if input_data is a dict
    if isinstance(input_data, dict):
        input_data = input_data.get("input", "")

    input_str = str(input_data)[:100] if input_data is not None else 'empty'
    logger.info(f"Tool: sql_db_query called with query: {input_str}...")
    try:
        if not input_data or not str(input_data).strip():
            return "Error: No query provided."

        result = db.execute_query(str(input_data))
        result_str = str(result)[:200] if result is not None else 'empty'
        logger.info(f"Tool: sql_db_query result: {result_str}...")
        return result
    except Exception as e:
        error_msg = f"Error executing query: {str(e)}"
        logger.error(error_msg)
        return error_msg


def sql_db_query_checker(input_data: str) -> str:
    """
    Tool to double check SQL query for common mistakes before execution.
    Input: SQL query
    Output: validated or corrected SQL query
    """
    # Handle if input_data is a dict
    if isinstance(input_data, dict):
        input_data = input_data.get("input", "")

    input_str = str(input_data)[:100] if input_data is not None else 'empty'
    logger.info(f"Tool: sql_db_query_checker called with query: {input_str}...")

    # Note: This tool will be used by the AI agent through Ollama
    # The actual checking logic will be performed by the LLM
    # This function just passes through the query for the LLM to analyze
    return str(input_data) if input_data is not None else ""


# Tool registry for the AI agent
TOOLS = {
    "sql_db_list_tables": {
        "function": sql_db_list_tables,
        "description": "List all tables in the database. Input is an empty string, output is a comma-separated list of tables.",
    },
    "sql_db_schema": {
        "function": sql_db_schema,
        "description": "Get schema and sample rows for specified tables. Input is a comma-separated list of table names, output is the schema and sample rows.",
    },
    "sql_db_query": {
        "function": sql_db_query,
        "description": "Execute a SQL query. Input is a detailed and correct SQL query, output is a result from the database. If the query is not correct, an error message will be returned.",
    },
    "sql_db_query_checker": {
        "function": sql_db_query_checker,
        "description": "Double check a SQL query for common mistakes before executing it. Input is a SQL query, output is the validated or corrected query.",
    },
}
