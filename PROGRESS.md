# Document Analyzer — Learning Progress

This file tracks your 10-step learning journey through the project.
Each step explains what was built, why it works, and what concepts to understand.

---

## Step 1 — Project Setup & Configuration ✅

**Files:** `requirements.txt`, `.env.example`, `config.py`

### What we did
Set up the project foundation: dependencies, environment variables, and a central config file.

### Why it matters
Every real project starts here. Before writing any feature code, you need:
- A **virtual environment** so your project's packages don't clash with other projects
- A **requirements file** so anyone can reproduce your setup with one command
- A **`.env` file** to keep secrets (API keys) out of your code — never hardcode them

### Key concepts

**Virtual environment (`venv`)**
A sandboxed Python installation just for this project. When you run `pip install` inside
a venv, it only installs there — not globally.
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Environment variables**
Instead of writing `api_key = "abc123"` in your code (which would leak if you push to GitHub),
we store secrets in a `.env` file and read them at runtime with `os.getenv()`.
The `python-dotenv` library loads `.env` automatically.

**`config.py` — single source of truth**
All project-wide settings live here. If you want to change the Gemini model, chunk size,
or number of results, you change it in one place and everything else picks it up.

### What to understand
- Why we use `.env` instead of hardcoding keys
- What `load_dotenv()` does and when it runs
- Why `CHUNK_SIZE`, `CHUNK_OVERLAP`, `TOP_K_CHUNKS` matter (you'll see in Steps 6–8)

---

## Step 2 — PDF Parser ✅

**File:** `app/parsers/pdf_parser.py`

### What we did
Built a function that opens a PDF file, reads every page, and returns the full text
plus metadata (title, author, page count, file size).

### Library: PyMuPDF (`import fitz`)
PyMuPDF is one of the fastest and most reliable PDF libraries in Python. It handles
scanned PDFs, multi-column layouts, and embedded fonts better than alternatives.

### Key concepts

**Why parse documents programmatically?**
Tools like Word or Acrobat show you a rendered view of the file. But to analyze
the content with code or AI, you need the raw text — no fonts, no images.

**PDF metadata**
PDF files store properties in a metadata block: title, author, the software used to
create it, creation date, etc. Most of these can be empty — many PDFs don't fill them in.

**Per-page extraction**
We extract text page by page and store it separately. This lets you later say
"the answer was found on page 3" instead of searching a wall of text.

### What to understand
- What `fitz.open()` returns and how to iterate pages
- Why we call `doc.close()` at the end (file handles)
- What `Path(file_path).stat().st_size` gives us

---

## Step 3 — DOCX Parser ✅

**File:** `app/parsers/docx_parser.py`

### What we did
Built a function that opens a DOCX file and extracts all text from paragraphs
and tables, plus metadata from the document's core properties.

### Library: python-docx
DOCX files are actually ZIP archives containing XML files. `python-docx` unpacks
the ZIP and gives you a clean Python API to navigate headings, paragraphs, tables,
and properties — without touching XML directly.

### Key concepts

**DOCX structure**
```
document.docx (ZIP file)
├── word/
│   ├── document.xml      ← The main body text
│   ├── styles.xml        ← Font/style definitions
│   └── ...
├── docProps/
│   └── core.xml          ← Metadata: author, title, dates
└── ...
```
`python-docx` reads `document.xml` for paragraphs and `core.xml` for metadata.

**Tables need separate handling**
Text inside tables is not in `doc.paragraphs` — it lives in cells. We iterate
`doc.tables → rows → cells` to catch all of it.

**No page count**
DOCX files don't store a page count. Pages are calculated by Word at render time
(it depends on screen size, fonts, margins). We use paragraph count instead.

### What to understand
- Difference between `doc.paragraphs` and table cells
- What `core_properties` contains
- Why DOCX and PDF parsers return the same dict shape (text, metadata, ...)

---

## Step 4 — Summarizer ✅

**File:** `app/analysis/summarizer.py`

### What we did
Used the Gemini API to generate a concise, coherent summary of the extracted document text.

### Key concepts

**Prompt engineering**
The quality of an LLM's output depends entirely on how well you write the prompt.
We structure ours with:
1. A clear task ("provide a clear and concise summary")
2. A constraint ("approximately 200 words")
3. Focus areas ("main ideas, key points, conclusions")
4. Clearly labeled sections ("Document:", "Summary:")

**Token limits**
LLMs process text as "tokens" (roughly 4 characters each). Even with Gemini's large
1-million-token context window, very long texts can be slow or costly. We cap input
at 30,000 characters (~7,500 words) — enough for most documents.

**`genai.GenerativeModel`**
We create the model instance once at module level (not inside the function).
This avoids recreating it on every call — a small but good performance habit.

### What to understand
- What `model.generate_content(prompt)` returns and why we use `.text`
- Why we truncate the text before sending
- How changing the prompt wording changes the output quality

---

## Step 5 — Keyword & Topic Extraction ✅

**File:** `app/analysis/keywords.py`

### What we did
Asked Gemini to extract specific keywords (granular terms) and broad topics (themes)
from the document, then parsed the structured response into Python lists.

### Key concepts

**Keywords vs Topics**
- **Keywords**: specific, precise terms — "neural networks", "backpropagation", "gradient descent"
- **Topics**: broad categories — "Machine Learning", "Computer Science"

Keywords help with search and indexing. Topics help with categorization and discovery.

**Structured output parsing**
LLMs return plain text. To get usable data (lists, dicts), we ask for a rigid format:
```
KEYWORDS: word1, word2, word3
TOPICS: theme1, theme2
```
Then we parse each line with `str.startswith()` and `str.split(",")`.

This is called **"format constraints"** in prompt engineering. In production systems
you'd use Gemini's native JSON mode, but string parsing teaches the concept clearly.

### What to understand
- Why we use a rigid response format in the prompt
- How `line.removeprefix("KEYWORDS:")` works
- The difference between prompting for keywords vs topics

---

## Step 6 — Sentiment Analysis ✅

**File:** `app/analysis/sentiment.py`

### What we did
Analyzed the overall emotional tone of the document — whether it's Positive, Negative,
Neutral, or Mixed — with a confidence level and explanation.

### Key concepts

**Why LLMs beat traditional sentiment tools**
Classic approaches used word lists: "excellent" → +1, "terrible" → -1.
LLMs understand:
- Context: "not bad" is positive
- Sarcasm: "Oh great, another meeting"
- Nuance: a research paper might be factual/neutral even about a negative topic
- Multiple sentiments in one document (Mixed)

**Four fields we extract**
1. `sentiment` — the overall label
2. `confidence` — how sure the model is (High/Medium/Low)
3. `explanation` — why it reached that conclusion (transparent AI)
4. `key_emotions` — specific emotions detected (joy, frustration, concern...)

**Why "transparent AI" matters for your resume**
Showing *why* a system made a decision (the explanation + confidence fields)
is called "explainability" — a hot topic in production AI systems.

### What to understand
- Why we pass only a sample (10k chars) for sentiment — tone tends to be consistent
- What `key_emotions` adds over a simple label
- How this could be used on customer feedback documents

---

## Step 7 — Named Entity Recognition (NER) ✅

**File:** `app/analysis/ner.py`

### What we did
Extracted all named real-world entities from the document: people, organizations,
locations, dates, monetary amounts, products, and events.

### Key concepts

**What is NER?**
NER = finding and labeling proper nouns in text.

```
"Elon Musk announced that Tesla will open a factory in Texas by 2025."
 ─────────                       ─────                  ─────    ────
   PERSON                   ORGANIZATION             LOCATION  DATE
```

**Zero-shot NER with an LLM**
Traditional NER uses ML models trained on labeled text (spaCy, Stanford NER).
LLM-based NER is "zero-shot" — we just describe what we want in the prompt.

Trade-offs:
| | LLM NER | Traditional NER |
|---|---|---|
| Context understanding | Excellent | Limited |
| Speed | Slower (API call) | Fast (local) |
| Cost | API credits | Free |
| Customization | Prompt only | Re-train model |

**Entity deduplication note**
Gemini may return the same entity in different forms ("NY" and "New York"). In
production you'd normalize and deduplicate — that's a good extension to add.

### What to understand
- The 7 entity types and what each covers
- Why we skip empty categories in the response
- How the parsing loop (`for entity_type in ENTITY_TYPES`) works

---

## Step 8 — Text Chunking ✅

**File:** `app/rag/chunker.py`

### What we did
Built a function that splits a long document into smaller, overlapping pieces called "chunks".

### Key concepts

**Why chunking is necessary for Q&A**
When a user asks a question, we can't send the entire 50-page document to Gemini
every time — it would be slow and expensive. Instead, we:
1. Pre-split the document into chunks
2. Convert each chunk to a searchable vector (Step 9)
3. At query time, only send the *relevant* chunks (Step 10)

**The overlap trick**
Imagine the answer to "What is the main conclusion?" sits right at the boundary
between chunk 1 and chunk 2:

```
Chunk 1: "...the analysis shows that revenue increased by 15%."
Chunk 2: "The main conclusion is that the strategy was successful..."
```

Without overlap, "The main conclusion" sentence might be split across both chunks
and never appear complete in either one. With overlap = 200, chunk 2 starts
200 chars before chunk 1 ended — so the sentence appears whole.

**Smart boundary detection**
We try to break at ". " (sentence end) or "\n" (paragraph end) rather than
mid-word. This keeps chunks semantically coherent.

### What to understand
- The sliding window: `start → end`, then `start = end - overlap`
- Why we search the last 20% of a chunk for a good break point
- What happens if we make chunks too small or too large

---

## Step 9 — Embeddings ✅

**File:** `app/rag/embeddings.py`

### What we did
Built functions to convert text into embedding vectors using Google's
`text-embedding-004` model, and implemented cosine similarity to compare vectors.

### Key concepts

**What is an embedding?**
An embedding is a list of numbers (a vector) that represents the *meaning* of text.

```
"The dog ran fast."      → [0.12, -0.45, 0.88, 0.31, ...]  (768 numbers)
"The puppy sprinted."    → [0.11, -0.43, 0.86, 0.29, ...]  ← very similar!
"The stock market fell." → [0.67,  0.22, -0.31, 0.88, ...] ← very different
```

Texts with similar meanings produce vectors that point in the same direction
— even if they use completely different words. This is semantic search.

**Two task types**
Google uses different optimizations for storing vs. searching:
- `retrieval_document` — for chunk vectors stored in the index
- `retrieval_query` — for the user's question vector at query time

**Cosine similarity**
Measures the angle between two vectors. If the angle is small (vectors point the
same way), similarity is close to 1. If vectors are perpendicular, similarity is 0.

```
similarity = (A · B) / (|A| × |B|)
```

We use numpy for this because it's much faster than doing the math in pure Python.

### What to understand
- Why 768 dimensions? More dimensions = richer representation
- Why cosine similarity instead of Euclidean distance?
  (Because we care about direction, not magnitude)
- What `np.dot(a, b)` and `np.linalg.norm(a)` compute

---

## Step 10 — RAG Retriever & Q&A ✅

**Files:** `app/rag/retriever.py`, `app/analysis/qa.py`

### What we did
Built the complete RAG pipeline:
1. **Index**: Chunk the document → embed each chunk → store in memory
2. **Retrieve**: Embed the question → find most similar chunks with cosine similarity
3. **Generate**: Build a prompt with the retrieved context → Gemini answers

### Key concepts

**The full RAG flow**

```
INDEXING (one time):
  Document text
       │
       ▼
  [chunker.py]  →  ["chunk1", "chunk2", "chunk3", ...]
       │
       ▼
  [embeddings.py]  →  [[0.12, -0.45, ...], [0.67, 0.22, ...], ...]
       │
       ▼
  Stored in DocumentRetriever (in memory)

QUERYING (every question):
  User question: "What is the main conclusion?"
       │
       ▼
  [embeddings.py]  →  query vector: [0.54, -0.12, ...]
       │
       ▼
  [cosine_similarity]  →  scores for every stored chunk
       │
       ▼
  Top 5 chunks by score  →  injected into Gemini prompt
       │
       ▼
  Gemini reads context and answers: "The main conclusion is..."
```

**Why "grounding" prevents hallucination**
Without RAG, if you ask Gemini "What does this contract say about termination?",
it might invent an answer based on typical contracts. With RAG, we inject the
*actual contract text* into the prompt and say "answer ONLY from this context."
If the answer isn't there, it says so — this is called a grounded response.

**In-memory vs vector database**
We store chunks in a Python list. This works for one document at a time and
is easy to understand. For production with many documents and users, you'd
use a vector database like ChromaDB, Pinecone, or pgvector (in Postgres).

### What to understand
- The difference between indexing (slow, done once) and querying (fast, done often)
- Why we show "sources" alongside the answer
- What `is_indexed` property does and why it matters
- How `top_indices = sorted(..., key=lambda i: scores[i], reverse=True)[:5]` works

---

## What You've Built — Summary

```
main.py              CLI entry point
server.py            FastAPI server entry point
config.py            Central settings
app/
  parsers/
    pdf_parser.py    PyMuPDF: text + metadata from PDF
    docx_parser.py   python-docx: text + metadata from DOCX
  analysis/
    summarizer.py    Gemini prompt → concise summary
    keywords.py      Gemini prompt → keywords + topics (structured parsing)
    sentiment.py     Gemini prompt → sentiment + emotions
    ner.py           Gemini prompt → entities by type
    qa.py            RAG pipeline: retrieve context → Gemini answers question
  rag/
    chunker.py       Sliding-window text splitter with smart boundaries
    embeddings.py    Gemini text-embedding-004 + cosine similarity
    retriever.py     In-memory vector store: index → retrieve → return top-K
  api/
    routes.py        FastAPI routes: one endpoint per feature + file upload
  cli/
    commands.py      Typer CLI: analyze, chat, info commands with Rich output
```

## Technologies Learned

| Technology | Used For |
|---|---|
| Python | Everything |
| FastAPI | REST API framework |
| Typer | CLI framework |
| Rich | Beautiful terminal output |
| PyMuPDF | PDF parsing |
| python-docx | DOCX parsing |
| Google Gemini API | Summarization, Keywords, Sentiment, NER, Q&A |
| Gemini Embeddings | Converting text to searchable vectors |
| NumPy | Cosine similarity math |
| python-dotenv | Loading secrets from `.env` files |
| uvicorn | ASGI server to run FastAPI |

## Resume Talking Points

- **"Built a RAG-based document Q&A system"** — you can explain chunking, embeddings, cosine similarity, and grounded generation
- **"Used Google Gemini API for multi-feature NLP"** — summarization, NER, sentiment, keyword extraction
- **"Designed a REST API with FastAPI + CLI with Typer"** — dual interface, clean separation of concerns
- **"Implemented semantic search using text embeddings"** — you understand why it beats keyword search
- **"Parsed PDF and DOCX files programmatically"** — PyMuPDF + python-docx

## Next Steps (Extensions)

- [ ] **Persist the RAG index** — save embeddings to disk (JSON/SQLite) so you don't re-embed on every run
- [ ] **Multi-document Q&A** — index multiple files and search across all of them
- [ ] **Frontend** — add a simple React or Streamlit UI instead of CLI
- [ ] **Traditional NER** — compare Gemini NER with spaCy for speed/accuracy trade-off
- [ ] **Chunking strategies** — try semantic chunking (split at paragraph/section boundaries)
- [ ] **Streaming responses** — stream Gemini's output token-by-token for a ChatGPT-like feel
- [ ] **Docker** — containerize the app so it runs anywhere
