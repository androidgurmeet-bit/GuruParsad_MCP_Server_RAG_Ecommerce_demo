from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

import numpy as np
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer


def load_pdf(path):
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def load_json(path):
    with open(path, 'r') as f:
        data = json.load(f)
    
    # Convert JSON to text format
    text = ""
    if isinstance(data, list):
        for item in data:
            text += json.dumps(item) + "\n"
    else:
        text += json.dumps(data)
    return text

def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip()

def chunk_text(text, size=500, overlap=100):
    chunks = []
    for i in range(0, len(text), size - overlap):
        chunks.append(text[i:i+size])
    return chunks


@dataclass(frozen=True)
class HashEmbedder:
    """Offline-safe embedder (no downloads). Uses a hashing trick into a fixed vector size."""

    dim: int = 384

    def encode(self, texts: list[str]):
        vecs = np.zeros((len(texts), self.dim), dtype="float32")
        for i, text in enumerate(texts):
            # simple tokenization
            for token in re.findall(r"[a-zA-Z0-9]+", (text or "").lower()):
                h = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
                idx = int.from_bytes(h, "little") % self.dim
                vecs[i, idx] += 1.0
            # normalize to unit length (avoid divide by zero)
            norm = float(np.linalg.norm(vecs[i]))
            if norm > 0:
                vecs[i] /= norm
        return vecs


def create_embeddings(chunks: list[str]):
    """
    Create embeddings for chunks.

    - Tries to load SentenceTransformer in offline/local mode first.
    - Falls back to a deterministic HashEmbedder if model files aren't available
      (keeps the app runnable in restricted-network environments).
    """
    try:
        model = SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)
        embeddings = model.encode(chunks)
        return model, embeddings
    except Exception:
        model = HashEmbedder()
        embeddings = model.encode(chunks)
        return model, embeddings