# SQL Chatbot

A Python web application that acts as an AI-powered gateway to interact with PostgreSQL databases using natural language queries. The application uses Transformers (with customizable models like google/gemma-4-e2b) to understand questions, generate SQL queries, and return results in a natural language format.

## Features

- Natural language to SQL query generation
- Automatic table and schema discovery
- Query validation and error correction
- FastAPI-based REST API
- Debug mode for step-by-step procedure logging
- PostgreSQL database support

## Architecture

The application follows a multi-step procedure to answer user questions:

1. **List Tables**: Fetches available tables from the database
2. **Identify Relevant Tables**: Decides which tables are relevant to the question
3. **Fetch Schemas**: Retrieves schema information for relevant tables
4. **Generate Query**: Creates a SQL query based on the question and schema
5. **Validate Query**: Double-checks the query for common mistakes using LLM
6. **Execute Query**: Runs the query against the database
7. **Error Correction**: Retries with corrected queries if errors occur
8. **Formulate Response**: Generates a natural language answer based on results

## Prerequisites

- Python 3.8 or higher
- PostgreSQL database
- PyTorch and Transformers libraries
- Sufficient GPU memory (recommended) or CPU for model inference

## Installation

1. Clone the repository:
```bash
cd C:\Users\Hossein\Desktop\Projects\sql-chatbot
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
# Copy the example environment file
copy .env.example .env

# Edit .env with your database and LLM configuration
```

## Configuration

Edit the `.env` file with your settings:

```env
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database
DB_USER=your_username
DB_PASSWORD=your_password

# LLM Configuration (Transformers)
LLM_MODEL=google/gemma-4-e2b
LLM_DEVICE=auto  # auto, cpu, cuda
LLM_MAX_LENGTH=2048
LLM_TEMPERATURE=0.7

# Application Configuration
DEBUG=false
TOP_K=5
DIALECT=postgresql
```

### LLM Model Options

The `LLM_MODEL` setting can be set to any compatible Hugging Face model. Default is `google/gemma-2-2b-it`. Other options include:
- `google/gemma-2-9b-it`
- `microsoft/phi-3-mini-4k-instruct`
- `TinyLlama/TinyLlama-1.1B-Chat-v1.0`
- Or any other causal language model from Hugging Face

### Device Configuration

The `LLM_DEVICE` setting controls where the model runs:
- `auto`: Automatically select available GPU (CUDA) or CPU
- `cuda`: Force GPU usage (requires CUDA-compatible GPU)
- `cpu`: Force CPU usage (slower but no GPU required)

## Running the Application

Start the FastAPI server:

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

## API Endpoints

### POST /query

Submit a natural language question about the database.

**Request Body:**
```json
{
  "question": "What are the top 5 products by sales?",
  "debug": false
}
```

**Response:**
```json
{
  "answer": "The top 5 products by sales are: Product A ($10,000), Product B ($8,500), ...",
  "error": null,
  "steps": null
}
```

If `debug` is set to `true`, the response will include detailed steps:
```json
{
  "answer": "The top 5 products by sales are: ...",
  "error": null,
  "steps": [
    {
      "step": 1,
      "tool": "sql_db_list_tables",
      "input": "",
      "output": "products, sales, customers"
    },
    {
      "step": 2,
      "tool": "sql_db_schema",
      "input": "products, sales",
      "output": "Table: products\nColumns: ..."
    }
  ]
}
```

### GET /health

Check API and database health status.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

### GET /

Root endpoint with API information.

## Available Tools

The AI agent has access to the following tools:

### sql_db_list_tables
- **Input**: Empty string
- **Output**: Comma-separated list of tables in the database

### sql_db_schema
- **Input**: Comma-separated list of table names (e.g., "table1, table2, table3")
- **Output**: Schema and sample rows for the specified tables

### sql_db_query
- **Input**: Detailed and correct SQL query
- **Output**: Result from the database or error message
- **Note**: If an error is returned, the agent will rewrite the query and try again

### sql_db_query_checker
- **Input**: SQL query
- **Output**: Validated or corrected SQL query
- **Purpose**: Double-checks queries for common mistakes before execution

## Query Checking

The `sql_db_query_checker` tool validates queries for common mistakes including:
- Using NOT IN with NULL values
- Using UNION when UNION ALL should have been used
- Using BETWEEN for exclusive ranges
- Data type mismatch in predicates
- Properly quoting identifiers
- Using the correct number of arguments for functions
- Casting to the correct data type
- Using the proper columns for joins

## Example Usage

### Using cURL:

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"How many users are in the database?\"}"
```

### Using Python:

```python
import requests

response = requests.post(
    "http://localhost:8000/query",
    json={"question": "What are the top 5 products by sales?"}
)

result = response.json()
print(result["answer"])
```

### Using JavaScript:

```javascript
fetch('http://localhost:8000/query', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    question: 'Show me all customers from the USA'
  })
})
  .then(response => response.json())
  .then(data => console.log(data.answer));
```

## Debug Mode

Set `DEBUG=true` in the `.env` file or pass `"debug": true` in the request to enable detailed logging of each step in the procedure. This is useful for understanding how the agent arrives at its answer and for troubleshooting.

## Security Considerations

- The application is designed for read-only queries (SELECT statements)
- DML statements (INSERT, UPDATE, DELETE, DROP) are blocked by the system prompt
- Keep your database credentials secure and never commit `.env` files to version control
- Consider adding authentication/authorization for production use

## Troubleshooting

### Database Connection Issues
- Verify PostgreSQL is running
- Check database credentials in `.env`
- Ensure the database exists and user has necessary permissions

### LLM Model Issues
- Ensure you have sufficient memory (GPU recommended for faster inference)
- If using CPU, set `LLM_DEVICE=cpu` in `.env`
- Verify the model name is correct and available on Hugging Face
- First startup may take longer as the model downloads
- Check torch installation matches your CUDA version if using GPU

### Query Errors
- Enable debug mode to see step-by-step execution
- Check database logs for detailed error messages
- Verify table names and column names match your schema

## Project Structure

```
sql-chatbot/
├── main.py              # FastAPI application and endpoints
├── config.py            # Configuration management
├── database.py          # Database connection and operations
├── tools.py             # SQL tool implementations
├── transformers_client.py  # Transformers LLM client
├── agent.py             # Main agent logic and procedure
├── requirements.txt     # Python dependencies
├── .env.example         # Example environment configuration
└── README.md            # This file
```

## License

This project is provided as-is for educational and development purposes.
