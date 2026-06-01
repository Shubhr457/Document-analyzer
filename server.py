"""
server.py — Entry point for the Document Analyzer REST API.

HOW TO RUN:
  python server.py

  Then open:
    http://localhost:8000/docs   ← Interactive Swagger UI (try routes here)
    http://localhost:8000/redoc  ← Alternative ReDoc documentation

WHAT IS UVICORN?
  FastAPI apps are ASGI applications (Asynchronous Server Gateway Interface).
  Uvicorn is the ASGI server that actually listens on a port and passes
  HTTP requests to FastAPI. Think of it like Gunicorn but async-native.
"""

import uvicorn
from fastapi import FastAPI

from app.api.routes import router

# Create the FastAPI application instance
app = FastAPI(
    title="Document Analyzer API",
    description=(
        "Upload PDF or DOCX documents and analyze them using Google Gemini. "
        "Features: text extraction, summarization, keyword extraction, "
        "sentiment analysis, named entity recognition, and RAG-based Q&A."
    ),
    version="1.0.0",
)

# Register all routes from app/api/routes.py under the root path
app.include_router(router)


if __name__ == "__main__":
    # reload=True means the server auto-restarts when you save a Python file.
    # Great for development — remove it in production.
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
