"""
app/api/routes.py — FastAPI REST API routes for the Document Analyzer.

WHAT is FastAPI?
  A modern Python web framework for building APIs. It's built on top of
  Starlette (ASGI framework) and Pydantic (data validation). Key features:
    - Automatic /docs page with interactive API explorer (Swagger UI)
    - Automatic request/response validation via Python type hints
    - Async support for high-performance concurrent handling

ROUTE OVERVIEW:
  GET  /                          Health check
  POST /extract      {file}       Extract text & metadata
  POST /summarize    {file}       Summarize document
  POST /keywords     {file}       Keywords & topics
  POST /sentiment    {file}       Sentiment analysis
  POST /ner          {file}       Named entity recognition
  POST /analyze/all  {file}       Run all analysis at once
  POST /chat/index   {file}       Index a document for Q&A
  POST /chat/ask     {question}   Ask a question

All file-upload endpoints accept multipart/form-data with a `file` field.
"""

import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.analysis.keywords import extract_keywords
from app.analysis.ner import extract_entities
from app.analysis.qa import answer_question
from app.analysis.sentiment import analyze_sentiment
from app.analysis.summarizer import summarize
from app.parsers.docx_parser import extract_from_docx
from app.parsers.pdf_parser import extract_from_pdf
from app.rag.retriever import DocumentRetriever

router = APIRouter()

# Global retriever — holds the currently indexed document in memory.
# In a real multi-user app, you'd store this per session/user.
_retriever = DocumentRetriever()


# ── Helper ─────────────────────────────────────────────────────────────────────


async def save_and_parse(file: UploadFile) -> dict:
    """
    Save an uploaded file to a temp directory, parse it, then delete it.
    Returns the parsed document dict.

    We use a temp file because our parsers work with file paths (not bytes).
    The file is deleted immediately after parsing to keep the server clean.
    """
    suffix = Path(file.filename).suffix.lower()
    if suffix not in (".pdf", ".docx"):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Use .pdf or .docx",
        )

    # Write upload to a temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        if suffix == ".pdf":
            doc = extract_from_pdf(tmp_path)
        else:
            doc = extract_from_docx(tmp_path)
    finally:
        os.unlink(tmp_path)  # always delete the temp file

    if not doc["text"].strip():
        raise HTTPException(
            status_code=422, detail="No text could be extracted from the file."
        )

    return doc


# ── Routes ─────────────────────────────────────────────────────────────────────


@router.get("/", tags=["Health"])
def health_check():
    """Confirm the API is running."""
    return {"status": "ok", "message": "Document Analyzer API is live."}


@router.post("/extract", tags=["Parsing"])
async def extract(file: UploadFile = File(...)):
    """
    Upload a PDF or DOCX and get back the extracted text and metadata.
    No AI calls are made — this is pure document parsing.
    """
    doc = await save_and_parse(file)
    return {
        "metadata": doc["metadata"],
        "text": doc["text"],
        "word_count": len(doc["text"].split()),
    }


@router.post("/summarize", tags=["Analysis"])
async def summarize_document(
    file: UploadFile = File(...),
    max_words: int = Form(200),
):
    """Upload a document and receive a Gemini-generated summary."""
    doc = await save_and_parse(file)
    summary = summarize(doc["text"], max_words=max_words)
    return {"summary": summary, "metadata": doc["metadata"]}


@router.post("/keywords", tags=["Analysis"])
async def keywords_and_topics(
    file: UploadFile = File(...),
    num_keywords: int = Form(10),
):
    """Extract keywords and high-level topics from the document."""
    doc = await save_and_parse(file)
    result = extract_keywords(doc["text"], num_keywords=num_keywords)
    return {**result, "metadata": doc["metadata"]}


@router.post("/sentiment", tags=["Analysis"])
async def sentiment(file: UploadFile = File(...)):
    """Analyse the overall sentiment of the document."""
    doc = await save_and_parse(file)
    result = analyze_sentiment(doc["text"])
    return {**result, "metadata": doc["metadata"]}


@router.post("/ner", tags=["Analysis"])
async def named_entities(file: UploadFile = File(...)):
    """Extract named entities (people, orgs, locations, etc.) from the document."""
    doc = await save_and_parse(file)
    entities = extract_entities(doc["text"])
    return {"entities": entities, "metadata": doc["metadata"]}


@router.post("/analyze/all", tags=["Analysis"])
async def analyze_all(file: UploadFile = File(...)):
    """
    Run all analysis features on the document in a single request.
    Returns summary, keywords, topics, sentiment, and named entities.
    """
    doc = await save_and_parse(file)
    text = doc["text"]

    return {
        "metadata": doc["metadata"],
        "summary": summarize(text),
        "keywords": extract_keywords(text),
        "sentiment": analyze_sentiment(text),
        "entities": extract_entities(text),
    }


@router.post("/chat/index", tags=["Q&A (RAG)"])
async def index_for_chat(file: UploadFile = File(...)):
    """
    Upload and index a document so it can be queried with /chat/ask.

    This step embeds all text chunks — it may take several seconds for
    large documents. Call this once, then call /chat/ask as many times
    as you like.
    """
    global _retriever
    doc = await save_and_parse(file)

    _retriever = DocumentRetriever()
    num_chunks = _retriever.index_document(doc["text"])

    return {
        "status": "indexed",
        "chunks": num_chunks,
        "metadata": doc["metadata"],
    }


@router.post("/chat/ask", tags=["Q&A (RAG)"])
async def ask(question: str = Form(...)):
    """
    Ask a question about the last indexed document.
    Call /chat/index first to load a document.
    """
    if not _retriever.is_indexed:
        raise HTTPException(
            status_code=400,
            detail="No document indexed yet. POST a file to /chat/index first.",
        )

    result = answer_question(question, _retriever)
    return result
