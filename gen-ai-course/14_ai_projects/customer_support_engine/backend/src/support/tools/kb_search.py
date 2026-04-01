"""Azure AI Search wrapper for knowledge base retrieval."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import QueryType

logger = logging.getLogger(__name__)


class KnowledgeBaseSearch:
    """
    Thin wrapper around Azure AI Search for retrieving KB chunks.

    Parameters
    ----------
    endpoint:
        Azure AI Search service endpoint URL.
    api_key:
        Admin or query API key.
    index_name:
        Name of the search index to query.
    """

    def __init__(self, endpoint: str, api_key: str, index_name: str) -> None:
        self._client = SearchClient(
            endpoint=endpoint,
            index_name=index_name,
            credential=AzureKeyCredential(api_key),
        )

    def search(self, query: str, top_k: int = 5) -> List[str]:
        """
        Run a semantic / keyword search against the knowledge base index.

        Parameters
        ----------
        query:
            The search query (typically the customer's message or a
            reformulated version of it).
        top_k:
            Maximum number of documents to return.

        Returns
        -------
        List[str]
            A list of plain-text content chunks ordered by relevance score.
        """
        if not query.strip():
            return []

        try:
            results = self._client.search(
                search_text=query,
                top=top_k,
                query_type=QueryType.SIMPLE,
                include_total_count=False,
            )

            chunks: List[str] = []
            for doc in results:
                # Support both 'content' and 'chunk' field names
                content = doc.get("content") or doc.get("chunk") or ""
                if content:
                    chunks.append(str(content))

            logger.debug("KB search returned %d chunks for query: %.60s", len(chunks), query)
            return chunks

        except Exception as exc:
            logger.error("KB search failed: %s", exc, exc_info=True)
            return []


def create_index(client: SearchClient, index_name: str) -> None:
    """Create the search index if it doesn't exist."""
    from azure.search.documents.indexes import SearchIndexClient
    from azure.search.documents.indexes.models import SearchIndex, SearchField, SearchFieldDataType
    
    logger.info(f"Creating search index: {index_name}")
    
    index_client = SearchIndexClient(
        endpoint=client._endpoint,
        credential=client._credential
    )
    
    fields = [
        SearchField(name="id", type=SearchFieldDataType.String, key=True),
        SearchField(name="content", type=SearchFieldDataType.String, searchable=True),
    ]
    
    try:
        index = SearchIndex(name=index_name, fields=fields)
        index_client.create_index(index)
        logger.info(f"Successfully created search index: {index_name}")
    except Exception as exc:
        logger.warning(f"Index may already exist or error occurred: {exc}")


def ingest_knowledge_base(file_path: str, index_name: str) -> None:
    """Ingest knowledge base from JSONL file into Azure AI Search."""
    import json
    import os
    from azure.search.documents import SearchClient
    from azure.core.credentials import AzureKeyCredential
    from dotenv import load_dotenv
    
    logger.info("=" * 60)
    logger.info("KB INGESTION PROCESS STARTED")
    logger.info("=" * 60)
    logger.info(f"Input file: {file_path}")
    logger.info(f"Target index: {index_name}")

    # Load .env and only require Azure Search variables for ingestion.
    load_dotenv()
    search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    search_key = os.getenv("AZURE_SEARCH_KEY")

    if not search_endpoint or not search_key:
        logger.error("Missing AZURE_SEARCH_ENDPOINT or AZURE_SEARCH_KEY in environment")
        raise ValueError(
            "Missing AZURE_SEARCH_ENDPOINT or AZURE_SEARCH_KEY. "
            "Set them in environment or .env before ingestion."
        )
    
    logger.info(f"Azure Search endpoint: {search_endpoint}")

    credential = AzureKeyCredential(search_key)
    client = SearchClient(
        endpoint=search_endpoint,
        index_name=index_name,
        credential=credential
    )
    
    # Create index
    create_index(client, index_name)
    
    # Read and ingest documents
    logger.info(f"Reading knowledge base from: {file_path}")
    documents = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                doc = {
                    "id": data.get("id", f"doc-{line_num}"),
                    "content": data.get("content", data.get("text", ""))
                }
                if doc["content"]:
                    documents.append(doc)
            except json.JSONDecodeError as e:
                logger.warning("Skipping invalid JSON on line %d: %s", line_num, e)
    
    logger.info(f"Parsed {len(documents)} valid documents from {file_path}")
    
    if documents:
        logger.info(f"Preparing to upload {len(documents)} documents to index: {index_name}")
        try:
            result = client.upload_documents(documents)
            # Log upload results
            succeeded = sum(1 for r in result if r.succeeded)
            failed = len(result) - succeeded
            logger.info(f"Upload complete: {succeeded} succeeded, {failed} failed")
            if failed > 0:
                for r in result:
                    if not r.succeeded:
                        logger.error(f"Failed to upload document ID {r.key}: {r.error_message}")
        except Exception as exc:
            logger.error(f"Failed to upload documents: {exc}", exc_info=True)
            raise
    else:
        logger.warning("No documents to ingest from: %s", file_path)


if __name__ == "__main__":
    import argparse
    import os
    from logging.handlers import RotatingFileHandler
    
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "logs")
    logs_dir = os.path.normpath(logs_dir)
    os.makedirs(logs_dir, exist_ok=True)
    
    # Configure logging with rotation
    log_file = os.path.join(logs_dir, f"kb_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10 MB
                backupCount=5
            ),
            logging.StreamHandler()
        ]
    )
    logger.info("Starting KB ingestion script")
    logger.info(f"Log file: {log_file}")
    
    parser = argparse.ArgumentParser(description="Knowledge Base Search Tool")
    parser.add_argument("--ingest", type=str, help="Path to JSONL file to ingest")
    parser.add_argument("--index", type=str, default="support-kb-index", help="Search index name")
    
    args = parser.parse_args()
    
    if args.ingest:
        # Check file exists
        if not os.path.exists(args.ingest):
            logger.error(f"File not found: {args.ingest}")
            print(f"Error: File not found: {args.ingest}")
            exit(1)
        try:
            ingest_knowledge_base(args.ingest, args.index)
            logger.info("=" * 60)
            logger.info("KB INGESTION COMPLETED SUCCESSFULLY")
            logger.info("=" * 60)
            print(f"Successfully ingested knowledge base from: {args.ingest}")
        except Exception as exc:
            logger.error(f"KB ingestion failed: {exc}", exc_info=True)
            print(f"Error: {exc}")
            exit(1)
    else:
        parser.print_help()
