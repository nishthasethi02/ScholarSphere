# -*- coding: utf-8 -*-
"""
services/env_loader.py
-----------------------
Robust environment variable loader for ScholarSync AI.
Searches project root and parent directories for .env and loads with override=True.
"""

from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv


def load_project_env() -> str:
    """
    Search for .env in current working directory, script directory, and parent,
    then load it and return the current TAVILY_API_KEY (or empty string).
    """
    candidates = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parent.parent / ".env",
        Path(__file__).resolve().parent.parent.parent / ".env",
    ]
    for p in candidates:
        if p.exists() and p.is_file():
            load_dotenv(dotenv_path=p, override=True)
            break

    return os.getenv("TAVILY_API_KEY", "").strip()


def get_tavily_key() -> str:
    """Return the active Tavily API key, refreshing from .env if needed."""
    key = os.getenv("TAVILY_API_KEY", "").strip()
    if not key or key.startswith("tvly-xxx"):
        key = load_project_env()
    return key
