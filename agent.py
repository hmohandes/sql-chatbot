from typing import List, Dict, Any, Optional
from ollama_client import ollama_client
from tools import TOOLS, sql_db_list_tables, sql_db_schema, sql_db_query, sql_db_query_checker
from config import settings
import logging
import json

logger = logging.getLogger(__name__)


class SQLAgent:
    def __init__(self):
        self.max_iterations = 5
        self.conversation_history = []

    def _build_system_prompt(self) -> str:
        """Build the system prompt for the AI agent"""
        return f"""You are an agent designed to interact with a SQL database.
Given an input question, create a syntactically correct {settings.dialect} query to run,
then look at the results of the query and return the answer. Unless the user
specifies a specific number of examples they wish to obtain, always limit your
query to at most {settings.top_k} results.

You can order the results by a relevant column to return the most interesting
examples in the database. Never query for all the columns from a specific table,
only ask for the relevant columns given the question.

You MUST double check your query before executing it. If you get an error while
executing a query, rewrite the query and try again.

DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the
database.

To start you should ALWAYS look at the tables in the database to see what you
can query. Do NOT skip this step.

Then you should query the schema of the most relevant tables.

You have access to the following tools:
- sql_db_list_tables: List all tables in the database. Input is an empty string.
- sql_db_schema: Get schema and sample rows for tables. Input is comma-separated table names.
- sql_db_query: Execute a SQL query. Input is the SQL query.
- sql_db_query_checker: Double check a SQL query for common mistakes. Input is the SQL query.

When you need to use a tool, respond with a JSON object in the following format:
{{
  "tool": "tool_name",
  "input": "tool_input"
}}

If you have enough information to answer the user's question, respond with a JSON object:
{{
  "answer": "your answer here"
}}

Always think step by step and explain your reasoning when necessary."""

    def _build_tools_schema(self) -> List[Dict]:
        """Build the tools schema for Ollama function calling"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "sql_db_list_tables",
                    "description": "List all tables in the database",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "sql_db_schema",
                    "description": "Get schema and sample rows for specified tables",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "input": {
                                "type": "string",
                                "description": "Comma-separated list of table names"
                            }
                        },
                        "required": ["input"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "sql_db_query",
                    "description": "Execute a SQL query",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "input": {
                                "type": "string",
                                "description": "The SQL query to execute"
                            }
                        },
                        "required": ["input"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "sql_db_query_checker",
                    "description": "Double check a SQL query for common mistakes",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "input": {
                                "type": "string",
                                "description": "The SQL query to check"
                            }
                        },
                        "required": ["input"]
                    }
                }
            }
        ]

    def _execute_tool(self, tool_name: str, tool_input: str) -> str:
        """Execute a tool and return the result"""
        logger.info(f"Executing tool: {tool_name} with input: {tool_input[:100] if tool_input else 'empty'}...")

        if tool_name == "sql_db_list_tables":
            return sql_db_list_tables(tool_input)
        elif tool_name == "sql_db_schema":
            return sql_db_schema(tool_input)
        elif tool_name == "sql_db_query":
            return sql_db_query(tool_input)
        elif tool_name == "sql_db_query_checker":
            return sql_db_query_checker(tool_input)
        else:
            return f"Unknown tool: {tool_name}"

    def _query_checker_prompt(self, query: str) -> str:
        """Build prompt for query checking"""
        return f"""Double check the PostgreSQL query above for common mistakes, including:
- Using NOT IN with NULL values
- Using UNION when UNION ALL should have been used
- Using BETWEEN for exclusive ranges
- Data type mismatch in predicates
- Properly quoting identifiers
- Using the correct number of arguments for functions
- Casting to the correct data type
- Using the proper columns for joins

If there are any of the above mistakes, rewrite the query. If there are no mistakes, just reproduce the original query.

Output the final SQL query only.

SQL Query: {query}"""

    def _check_query(self, query: str) -> str:
        """Use LLM to check query for common mistakes"""
        logger.info("Checking query with LLM")
        prompt = self._query_checker_prompt(query)
        checked_query = ollama_client.generate(prompt)
        logger.info(f"Query check result: {checked_query[:100]}...")
        return checked_query.strip()

    def process_question(self, question: str) -> Dict[str, Any]:
        """
        Process a user question through the agent procedure.
        Returns a dictionary with the result or error.
        """
        logger.info(f"Processing question: {question}")
        steps_log = []

        try:
            # Initialize conversation
            messages = [
                {"role": "system", "content": self._build_system_prompt()},
                {"role": "user", "content": question}
            ]

            iteration = 0
            final_answer = None

            while iteration < self.max_iterations and not final_answer:
                iteration += 1
                logger.info(f"Iteration {iteration}/{self.max_iterations}")

                # Get response from Ollama
                tools_schema = self._build_tools_schema()
                response = ollama_client.chat(messages, tools=tools_schema)

                if not response or "message" not in response:
                    return {
                        "error": "No response from AI model",
                        "steps": steps_log
                    }

                assistant_message = response["message"]
                messages.append(assistant_message)

                # Check if assistant wants to use a tool
                if "tool_calls" in assistant_message:
                    for tool_call in assistant_message["tool_calls"]:
                        tool_name = tool_call["function"]["name"]
                        tool_input_str = tool_call["function"]["arguments"]

                        # Parse tool input
                        try:
                            tool_input = json.loads(tool_input_str)
                            input_value = tool_input.get("input", "")
                        except:
                            input_value = tool_input_str

                        # Execute tool
                        tool_result = self._execute_tool(tool_name, input_value)

                        if settings.debug:
                            steps_log.append({
                                "step": iteration,
                                "tool": tool_name,
                                "input": input_value,
                                "output": tool_result
                            })

                        # Add tool result to conversation
                        messages.append({
                            "role": "tool",
                            "content": tool_result,
                            "name": tool_name
                        })

                # Check if assistant provided an answer
                elif "content" in assistant_message and assistant_message["content"]:
                    content = assistant_message["content"]

                    # Try to parse as JSON to check for answer
                    try:
                        parsed = json.loads(content)
                        if "answer" in parsed:
                            final_answer = parsed["answer"]
                        else:
                            # Not a tool call or answer, continue conversation
                            continue
                    except json.JSONDecodeError:
                        # Regular text response, treat as answer
                        final_answer = content

            if final_answer:
                logger.info("Successfully generated answer")
                return {
                    "answer": final_answer,
                    "steps": steps_log if settings.debug else None
                }
            else:
                return {
                    "error": "Max iterations reached without answer",
                    "steps": steps_log
                }

        except Exception as e:
            logger.error(f"Error processing question: {e}")
            return {
                "error": str(e),
                "steps": steps_log
            }


# Global agent instance
agent = SQLAgent()
