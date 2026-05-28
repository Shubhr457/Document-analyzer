# Document Analyzer

A CLI + REST API tool to extract, analyze, and chat with your PDF and DOCX documents — powered by **Google Gemini AI**.

## Features

| Feature | What it does |
|---|---|
| Text & Metadata Extraction | Reads title, author, page count, and raw text |
| Summarization | Gemini-generated concise summary |
| Keyword & Topic Extraction | Key phrases + high-level themes |
| Sentiment Analysis | Positive / Negative / Neutral / Mixed with explanation |
| Named Entity Recognition | People, orgs, locations, dates, money, products |
| Q&A over Document (RAG) | Ask questions; answers are grounded in your document |

---

## Setup

```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set your Gemini API key
cp .env.example .env
# Edit .env → paste your key from https://aistudio.google.com/app/apikey
```

---

## CLI Usage

```bash
# See all commands
python main.py --help

# View document info (no AI calls)
python main.py info report.pdf

# Run all analysis features
python main.py analyze report.pdf --all

# Run specific features
python main.py analyze report.pdf --summarize
python main.py analyze report.pdf --keywords
python main.py analyze report.pdf --sentiment
python main.py analyze report.pdf --ner
python main.py analyze report.pdf --summarize --keywords --ner

# Interactive Q&A chat session
python main.py chat report.pdf
```

---

## API Usage

```bash
# Start the server
python server.py

# API is live at http://localhost:8000
# Interactive docs at http://localhost:8000/docs
```

---

## Project Structure

```
Document-analyzer/
├── main.py          ← CLI entry point  (python main.py ...)
├── server.py        ← API entry point  (python server.py)
├── config.py        ← All settings (model names, chunk sizes, etc.)
├── .env             ← Your API key lives here (never commit this)
├── requirements.txt
└── app/
    ├── parsers/
    │   ├── pdf_parser.py    ← Extracts text + metadata from PDF
    │   └── docx_parser.py   ← Extracts text + metadata from DOCX
    ├── analysis/
    │   ├── summarizer.py    ← Gemini-powered summarization
    │   ├── keywords.py      ← Keyword + topic extraction
    │   ├── sentiment.py     ← Sentiment analysis
    │   ├── ner.py           ← Named entity recognition
    │   └── qa.py            ← RAG-based Q&A
    ├── rag/
    │   ├── chunker.py       ← Splits document into overlapping pieces
    │   ├── embeddings.py    ← Converts text to/from vectors
    │   └── retriever.py     ← Finds relevant chunks for a question
    ├── api/
    │   └── routes.py        ← FastAPI route handlers
    └── cli/
        └── commands.py      ← Typer CLI commands
```
