"""CLI script to ingest offline_database.json files into Supabase rag_documents table.

Usage:
    python -m scripts.ingest_docs

Reads each products/promethicc-*/offline_database.json and inserts rows
into the rag_documents table with the appropriate expert namespace.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import httpx

# Add parent directory to path so we can import app.config
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

_PRODUCTS_DIR = Path(__file__).resolve().parent.parent.parent / "products"

# Map directory names to expert namespaces
_NAMESPACE_MAP: dict[str, str] = {
    "promethicc-code": "code",
    "promethicc-eng": "eng",
    "promethicc-agri": "agri",
    "promethicc-med": "med",
    "promethicc-law": "law",
}


def _headers() -> dict[str, str]:
    """Build Supabase REST API headers.

    Returns:
        Dict of HTTP headers.
    """
    return {
        "apikey": settings.SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }


def _find_database_files() -> list[tuple[str, Path]]:
    """Discover all offline_database.json files under the products directory.

    Returns:
        List of (namespace, file_path) tuples.
    """
    found: list[tuple[str, Path]] = []

    if not _PRODUCTS_DIR.exists():
        logger.warning("Products directory not found: %s", _PRODUCTS_DIR)
        return found

    for dir_path in sorted(_PRODUCTS_DIR.iterdir()):
        if not dir_path.is_dir():
            continue
        namespace = _NAMESPACE_MAP.get(dir_path.name)
        if namespace is None:
            continue
        db_file = dir_path / "offline_database.json"
        if db_file.exists():
            found.append((namespace, db_file))
            logger.info("Found %s -> namespace '%s'", db_file, namespace)

    return found


def _load_entries(file_path: Path) -> list[dict]:
    """Load and parse a JSON database file.

    Args:
        file_path: Path to the offline_database.json file.

    Returns:
        List of document entries.
    """
    with open(file_path, encoding="utf-8") as fh:
        data = json.load(fh)

    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if "documents" in data:
            return data["documents"]
        if "entries" in data:
            return data["entries"]
        # Treat as flat key-value pair database
        return [{"title": k, "content": v} for k, v in data.items()]

    logger.warning("Unexpected format in %s, treating as single entry", file_path)
    return [data]


def _build_row(namespace: str, entry: dict) -> dict:
    """Convert a JSON entry into a rag_documents table row.

    Args:
        namespace: Expert namespace.
        entry: A single document entry.

    Returns:
        Dict suitable for Supabase insertion.
    """
    return {
        "expert": namespace,
        "content": entry.get("content", entry.get("text", "")),
        "source_title": entry.get("title", entry.get("source_title", "")),
        "source_url": entry.get("url", entry.get("source_url", "")),
    }


def main() -> None:
    """Entry point: discover, parse, and upload all offline database files."""
    files = _find_database_files()
    if not files:
        logger.info("No offline_database.json files found. Nothing to ingest.")
        return

    total_inserted = 0

    with httpx.Client(timeout=30.0) as client:
        for namespace, file_path in files:
            entries = _load_entries(file_path)
            logger.info("Ingesting %d entries from %s", len(entries), file_path)

            for entry in entries:
                row = _build_row(namespace, entry)
                if not row["content"]:
                    continue

                url = f"{settings.SUPABASE_URL}/rest/v1/rag_documents"
                resp = client.post(url, headers=_headers(), json=row)

                if resp.status_code >= 400:
                    logger.error(
                        "Failed to insert row: %s %s",
                        resp.status_code,
                        resp.text,
                    )
                else:
                    total_inserted += 1

    logger.info("Ingestion complete. Total rows inserted: %d", total_inserted)


if __name__ == "__main__":
    main()
