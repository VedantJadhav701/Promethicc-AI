"""Script to download the 3B-class quantized GGUF model for offline mode."""

from __future__ import annotations

import os
from pathlib import Path
import urllib.request
import sys

MODEL_URL = "https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf"
DEST_DIR = Path(__file__).resolve().parent.parent / "models"
DEST_PATH = DEST_DIR / "model.gguf"


def progress_hook(count: int, block_size: int, total_size: int) -> None:
    """Print download progress percentage.

    Args:
        count: Block count.
        block_size: Size of each block in bytes.
        total_size: Total file size in bytes.
    """
    downloaded = count * block_size
    percent = min(100, int(downloaded * 100 / total_size))
    downloaded_mb = downloaded / (1024 * 1024)
    total_mb = total_size / (1024 * 1024)
    sys.stdout.write(
        f"\rDownloading: {percent}% ({downloaded_mb:.1f} MB / {total_mb:.1f} MB)"
    )
    sys.stdout.flush()


def download_model() -> None:
    """Download the GGUF model from Hugging Face."""
    if not DEST_DIR.exists():
        DEST_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {DEST_DIR}")

    if DEST_PATH.exists():
        print(f"Model already exists at: {DEST_PATH}")
        sys.exit(0)

    print(f"Starting download from: {MODEL_URL}")
    print(f"Saving to: {DEST_PATH}")
    print("This is a 2.0 GB download. Please wait...")
    
    try:
        urllib.request.urlretrieve(MODEL_URL, DEST_PATH, reporthook=progress_hook)
        print("\nDownload completed successfully!")
    except Exception as exc:
        print(f"\nError downloading model: {exc}")
        if DEST_PATH.exists():
            DEST_PATH.unlink()
        sys.exit(1)


if __name__ == "__main__":
    download_model()
