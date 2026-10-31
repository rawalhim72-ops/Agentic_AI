"""
Launcher Script for Intelligent Student Support Agent.
Initializes the database, loads vector indexes, and starts the Streamlit UI.
"""

import sys
import subprocess
from pathlib import Path

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from database.seed import seed_database
from rag.retriever import build_or_load_vector_store


def main():
    print("================================================================")
    print("   INTELLIGENT STUDENT SUPPORT AGENT - AGENTIC AI SYSTEM       ")
    print("================================================================")
    print("1. Initializing and verifying SQLite database...")
    seed_database()

    print("2. Verifying FAISS vector store & embeddings...")
    build_or_load_vector_store()

    print("3. Launching Streamlit Enterprise Interface on http://localhost:8501 ...")
    main_app_path = ROOT_DIR / "app" / "main.py"
    cmd = [sys.executable, "-m", "streamlit", "run", str(main_app_path)]

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nApplication stopped by user. Goodbye!")


if __name__ == "__main__":
    main()
