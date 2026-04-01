"""
Shared pytest fixtures and configuration.

Patches out Azure settings so tests run without real credentials.
"""

import os
import pytest
from unittest.mock import patch


# Provide fake env vars before any module imports settings
os.environ.setdefault("AZURE_OPENAI_ENDPOINT", "https://fake-openai.openai.azure.com")
os.environ.setdefault("AZURE_OPENAI_KEY", "fake-openai-key")
os.environ.setdefault("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
os.environ.setdefault("AZURE_SEARCH_ENDPOINT", "https://fake-search.search.windows.net")
os.environ.setdefault("AZURE_SEARCH_KEY", "fake-search-key")
os.environ.setdefault("AZURE_SEARCH_INDEX", "kb-index")
os.environ.setdefault("COSMOS_ENDPOINT", "https://fake-cosmos.documents.azure.com:443/")
os.environ.setdefault("COSMOS_KEY", "fake-cosmos-key==")
os.environ.setdefault("COSMOS_DB", "support_db")
os.environ.setdefault("COSMOS_CONTAINER", "conversations")
