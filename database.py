import psycopg2
from psycopg2 import sql
from typing import List, Dict, Any, Optional
from config import settings
import logging

logger = logging.getLogger(__name__)


class DatabaseConnection:
    def __init__(self):
        self.connection = None

    def connect(self):
        """Establish connection to PostgreSQL database"""
        try:
            self.connection = psycopg2.connect(settings.database_url)
            self.connection.autocommit = True
            logger.info("Successfully connected to database")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")

    def list_tables(self) -> str:
        """
        List all tables in the database.
        Returns comma-separated list of table names.
        """
        if not self.connection:
            self.connect()

        query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                tables = [row[0] for row in cursor.fetchall()]
                logger.info(f"Retrieved {len(tables)} tables")
                return ",".join(tables)
        except Exception as e:
            logger.error(f"Error listing tables: {e}")
            raise

    def get_schema(self, table_names: str) -> str:
        """
        Get schema and sample rows for specified tables.
        Input: comma-separated list of table names
        Output: schema information with sample data
        """
        if not self.connection:
            self.connect()

        tables = [t.strip() for t in table_names.split(",") if t.strip()]
        schema_info = []

        for table in tables:
            # Get column information
            columns_query = """
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = %s AND table_schema = 'public'
                ORDER BY ordinal_position;
            """

            # Get sample rows
            sample_query = sql.SQL("SELECT * FROM {} LIMIT 3").format(
                sql.Identifier(table)
            )

            try:
                with self.connection.cursor() as cursor:
                    # Get columns
                    cursor.execute(columns_query, (table,))
                    columns = cursor.fetchall()

                    # Get sample data
                    cursor.execute(sample_query)
                    samples = cursor.fetchall()
                    column_names = [desc[0] for desc in cursor.description]

                    # Build schema string
                    schema_str = f"\nTable: {table}\n"
                    schema_str += "Columns:\n"
                    for col in columns:
                        schema_str += f"  - {col[0]} ({col[1]}, nullable: {col[2]}, default: {col[3]})\n"

                    schema_str += "Sample rows:\n"
                    for sample in samples:
                        schema_str += f"  {dict(zip(column_names, sample))}\n"

                    schema_info.append(schema_str)
                    logger.info(f"Retrieved schema for table: {table}")

            except Exception as e:
                logger.error(f"Error getting schema for table {table}: {e}")
                schema_info.append(f"\nTable: {table}\nError: {str(e)}")

        return "\n".join(schema_info)

    def execute_query(self, query: str) -> str:
        """
        Execute a SQL query and return results.
        Input: SQL query string
        Output: formatted results or error message
        """
        if not self.connection:
            self.connect()

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                results = cursor.fetchall()
                column_names = [desc[0] for desc in cursor.description]

                # Format results
                if not results:
                    return "Query executed successfully but returned no results."

                formatted_results = []
                for row in results:
                    formatted_results.append(dict(zip(column_names, row)))

                output = f"Query executed successfully. Results:\n"
                for result in formatted_results:
                    output += f"  {result}\n"

                logger.info(f"Query executed successfully, returned {len(results)} rows")
                return output

        except Exception as e:
            error_msg = f"Query execution error: {str(e)}"
            logger.error(error_msg)
            return error_msg


# Global database instance
db = DatabaseConnection()
