"""
main.py — Entry point for the Document Analyzer CLI.

This file is intentionally tiny. All the real logic lives in app/cli/commands.py.
Keeping the entry point thin is a good practice — it makes the code easier to
test and reuse.

HOW TO RUN:
  python main.py --help
  python main.py analyze document.pdf --all
  python main.py chat    document.pdf
  python main.py info    document.pdf
"""

from app.cli.commands import app

if __name__ == "__main__":
    # typer's app() reads sys.argv and routes to the right command function.
    app()
