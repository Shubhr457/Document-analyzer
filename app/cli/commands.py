"""
app/cli/commands.py — All CLI commands for the Document Analyzer.

Libraries used:
  - Typer : builds the CLI from plain Python functions. Each function
            decorated with @app.command() becomes a CLI sub-command.
  - Rich  : makes terminal output beautiful. Panels, tables, spinners,
            colored text — all without any HTML or CSS.

COMMAND OVERVIEW:
  python main.py analyze <file> [options]   — run analysis on a document
  python main.py chat    <file>             — interactive Q&A session
  python main.py info    <file>             — show metadata only
"""

import sys
from pathlib import Path

import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text

# ── Import our analysis modules ───────────────────────────────────────────────
from app.analysis.keywords import extract_keywords
from app.analysis.ner import extract_entities
from app.analysis.qa import answer_question
from app.analysis.sentiment import analyze_sentiment
from app.analysis.summarizer import summarize

# ── Import our document parsers ───────────────────────────────────────────────
from app.parsers.docx_parser import extract_from_docx
from app.parsers.pdf_parser import extract_from_pdf
from app.rag.retriever import DocumentRetriever

# Rich console for styled output
console = Console()

# The Typer app instance — this is what main.py imports and runs
app = typer.Typer(
    name="docanalyzer",
    help="Analyze PDF and DOCX documents using Google Gemini AI.",
    add_completion=False,
)


# ── Helper functions ──────────────────────────────────────────────────────────


def load_document(file_path: str) -> dict:
    """
    Detect file type and call the right parser.
    Returns the parsed document dict (text, metadata, pages/paragraphs).
    """
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == ".pdf":
        return extract_from_pdf(file_path)
    elif ext == ".docx":
        return extract_from_docx(file_path)
    else:
        console.print(f"[bold red]Unsupported file type: {ext}[/bold red]")
        console.print("Supported formats: .pdf, .docx")
        raise typer.Exit(code=1)


def print_header(title: str, subtitle: str = "") -> None:
    """Print a styled section header."""
    content = f"[bold cyan]{title}[/bold cyan]"
    if subtitle:
        content += f"\n[dim]{subtitle}[/dim]"
    console.print(Panel(content, expand=False))


def print_metadata(metadata: dict) -> None:
    """Render metadata as a Rich table."""
    table = Table(
        title="Document Metadata", show_header=True, header_style="bold magenta"
    )
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")

    for key, value in metadata.items():
        if value:  # skip empty values
            table.add_row(key.replace("_", " ").title(), str(value))

    console.print(table)


# ── Commands ──────────────────────────────────────────────────────────────────


@app.command()
def analyze(
    file: str = typer.Argument(..., help="Path to the PDF or DOCX file"),
    summarize_doc: bool = typer.Option(
        False, "--summarize", "-s", help="Summarize the document"
    ),
    keywords: bool = typer.Option(
        False, "--keywords", "-k", help="Extract keywords and topics"
    ),
    sentiment: bool = typer.Option(False, "--sentiment", help="Analyze sentiment"),
    ner: bool = typer.Option(False, "--ner", "-n", help="Named entity recognition"),
    all_features: bool = typer.Option(
        False, "--all", "-a", help="Run all analysis features"
    ),
) -> None:
    """
    Analyze a document. Choose one or more features, or use --all.

    Examples:

        python main.py analyze report.pdf --all

        python main.py analyze report.pdf --summarize --keywords

        python main.py analyze contract.docx --ner --sentiment
    """
    # Validate file exists
    if not Path(file).exists():
        console.print(f"[bold red]File not found:[/bold red] {file}")
        raise typer.Exit(code=1)

    # If no specific feature flags were given, show help hint
    if not any([summarize_doc, keywords, sentiment, ner, all_features]):
        console.print(
            "[yellow]Tip:[/yellow] No analysis flags specified. Use --all or pick features:"
        )
        console.print("  --summarize   Summarize the document")
        console.print("  --keywords    Extract keywords and topics")
        console.print("  --sentiment   Sentiment analysis")
        console.print("  --ner         Named entity recognition")
        console.print("  --all         Run everything")
        raise typer.Exit()

    # ── Load the document ─────────────────────────────────────────────────────
    console.print(f"\n[bold]Loading:[/bold] {file}")
    with console.status("[bold green]Parsing document...[/bold green]"):
        doc = load_document(file)

    text = doc["text"]
    metadata = doc["metadata"]

    if not text.strip():
        console.print(
            "[bold red]No text could be extracted from this document.[/bold red]"
        )
        raise typer.Exit(code=1)

    # Always show metadata
    console.print()
    print_metadata(metadata)

    # ── Run selected analyses ─────────────────────────────────────────────────

    if summarize_doc or all_features:
        console.print()
        print_header("Summary", "Gemini-generated document summary")
        with console.status("[bold green]Generating summary...[/bold green]"):
            summary = summarize(text)
        console.print(Panel(summary, border_style="green"))

    if keywords or all_features:
        console.print()
        print_header("Keywords & Topics", "Key phrases and high-level themes")
        with console.status("[bold green]Extracting keywords...[/bold green]"):
            kw_result = extract_keywords(text)

        kw_text = (
            "  " + " • ".join(kw_result["keywords"])
            if kw_result["keywords"]
            else "  (none found)"
        )
        tp_text = (
            "  " + " • ".join(kw_result["topics"])
            if kw_result["topics"]
            else "  (none found)"
        )

        console.print(f"[bold cyan]Keywords:[/bold cyan]\n{kw_text}")
        console.print(f"\n[bold cyan]Topics:[/bold cyan]\n{tp_text}")

    if sentiment or all_features:
        console.print()
        print_header("Sentiment Analysis", "Overall emotional tone of the document")
        with console.status("[bold green]Analyzing sentiment...[/bold green]"):
            sent_result = analyze_sentiment(text)

        # Color-code the sentiment label
        sentiment_colors = {
            "Positive": "green",
            "Negative": "red",
            "Neutral": "yellow",
            "Mixed": "cyan",
        }
        color = sentiment_colors.get(sent_result["sentiment"], "white")
        console.print(
            f"  Sentiment  : [{color}]{sent_result['sentiment']}[/{color}]  (Confidence: {sent_result['confidence']})"
        )
        console.print(f"  Explanation: {sent_result['explanation']}")
        if sent_result["key_emotions"]:
            console.print(f"  Emotions   : {', '.join(sent_result['key_emotions'])}")

    if ner or all_features:
        console.print()
        print_header(
            "Named Entities", "People, organisations, locations, dates, and more"
        )
        with console.status("[bold green]Extracting entities...[/bold green]"):
            entities = extract_entities(text)

        if entities:
            ner_table = Table(show_header=True, header_style="bold magenta")
            ner_table.add_column("Entity Type", style="cyan", no_wrap=True)
            ner_table.add_column("Found Entities", style="white")
            for entity_type, items in entities.items():
                ner_table.add_row(entity_type, ", ".join(items))
            console.print(ner_table)
        else:
            console.print("  [dim]No named entities found.[/dim]")

    console.print("\n[bold green]Analysis complete![/bold green]\n")


@app.command()
def chat(
    file: str = typer.Argument(..., help="Path to the PDF or DOCX file to chat with"),
) -> None:
    """
    Start an interactive Q&A session with a document (RAG-powered).

    The document is indexed once, then you can ask as many questions as you
    want. Type 'exit' or 'quit' to end the session.

    Example:

        python main.py chat research_paper.pdf
    """
    if not Path(file).exists():
        console.print(f"[bold red]File not found:[/bold red] {file}")
        raise typer.Exit(code=1)

    # ── Load and display document info ────────────────────────────────────────
    console.print(f"\n[bold]Loading:[/bold] {file}")
    with console.status("[bold green]Parsing document...[/bold green]"):
        doc = load_document(file)

    text = doc["text"]
    metadata = doc["metadata"]

    if not text.strip():
        console.print(
            "[bold red]No text could be extracted from this document.[/bold red]"
        )
        raise typer.Exit(code=1)

    console.print()
    print_metadata(metadata)

    # ── Build the RAG index ───────────────────────────────────────────────────
    # This is the most time-consuming step: chunking + embedding every chunk.
    retriever = DocumentRetriever()
    with console.status(
        "[bold green]Building search index (this may take a moment)...[/bold green]"
    ):
        num_chunks = retriever.index_document(text)

    console.print(
        f"\n[bold green]Index ready![/bold green] {num_chunks} chunks embedded."
    )
    console.print("[dim]Type your question below. Enter 'exit' to quit.[/dim]\n")

    # ── Interactive Q&A loop ──────────────────────────────────────────────────
    while True:
        try:
            question = console.input("[bold cyan]You:[/bold cyan] ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not question:
            continue

        if question.lower() in ("exit", "quit", "q", "bye"):
            console.print("\n[bold]Goodbye![/bold]")
            break

        with console.status("[bold green]Thinking...[/bold green]"):
            result = answer_question(question, retriever)

        console.print(f"\n[bold green]Answer:[/bold green]")
        console.print(Panel(result["answer"], border_style="green"))

        # Optionally show which chunks were used as evidence
        if result["sources"]:
            show_sources = (
                console.input("\n[dim]Show source chunks? (y/n):[/dim] ")
                .strip()
                .lower()
            )
            if show_sources == "y":
                for i, source in enumerate(result["sources"], 1):
                    console.print(
                        Panel(
                            source["chunk"],
                            title=f"[dim]Source {i} (score: {source['score']})[/dim]",
                            border_style="dim",
                        )
                    )
        console.print()


@app.command()
def info(
    file: str = typer.Argument(..., help="Path to the PDF or DOCX file"),
) -> None:
    """
    Display metadata and basic statistics for a document (no AI calls).

    Example:

        python main.py info report.pdf
    """
    if not Path(file).exists():
        console.print(f"[bold red]File not found:[/bold red] {file}")
        raise typer.Exit(code=1)

    with console.status("[bold green]Reading document...[/bold green]"):
        doc = load_document(file)

    console.print()
    print_metadata(doc["metadata"])

    text = doc["text"]
    word_count = len(text.split())
    char_count = len(text)

    stats_table = Table(
        title="Text Statistics", show_header=True, header_style="bold magenta"
    )
    stats_table.add_column("Metric", style="cyan")
    stats_table.add_column("Value", style="white")
    stats_table.add_row("Word Count", f"{word_count:,}")
    stats_table.add_row("Character Count", f"{char_count:,}")
    console.print(stats_table)
    console.print()
