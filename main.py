from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from agent import agent
from database import db
from transformers_client import llm_client
from config import settings
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="SQL Chatbot API", version="1.0.0")


class QuestionRequest(BaseModel):
    question: str
    debug: Optional[bool] = None


class QuestionResponse(BaseModel):
    answer: Optional[str] = None
    error: Optional[str] = None
    steps: Optional[list] = None


@app.on_event("startup")
async def startup_event():
    """Initialize database connection and LLM model on startup"""
    try:
        db.connect()
        logger.info("Database connected successfully")
    except Exception as e:
        logger.error(f"Failed to connect to database on startup: {e}")
        # Don't raise here to allow the app to start even if DB is temporarily unavailable

    try:
        llm_client.initialize()
        logger.info("LLM model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load LLM model on startup: {e}")
        # Don't raise here to allow the app to start even if model loading fails

    logger.info("Application started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    db.disconnect()
    logger.info("Application shutdown")


@app.post("/query", response_model=QuestionResponse)
async def query_database(request: QuestionRequest):
    """
    Process a natural language question and return SQL query results.

    The agent will:
    1. List available tables in the database
    2. Determine which tables are relevant to the question
    3. Fetch schemas for relevant tables
    4. Generate a SQL query based on the question and schema information
    5. Double-check the query for common mistakes
    6. Execute the query and return results
    7. Correct any errors and retry if needed
    8. Formulate a natural language response based on the results
    """
    try:
        # Override debug setting if provided in request
        if request.debug is not None:
            original_debug = settings.debug
            settings.debug = request.debug

        logger.info(f"Received question: {request.question}")

        # Process the question through the agent
        result = agent.process_question(request.question)

        # Restore original debug setting
        if request.debug is not None:
            settings.debug = original_debug

        return QuestionResponse(**result)

    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Try to connect to database (or check existing connection)
        db.ensure_connection()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "SQL Chatbot API",
        "version": "1.0.0",
        "endpoints": {
            "/query": "POST - Submit a natural language question about the database",
            "/health": "GET - Check API and database health status"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
