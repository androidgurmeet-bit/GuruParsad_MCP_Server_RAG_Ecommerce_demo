#!/usr/bin/env python
"""Debug script to test the RAG system"""

import json
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.embeddings import load_json, clean_text, chunk_text, create_embeddings
from app.rag import create_index, rag_tool
from app.llm import ask_llm

print("=" * 60)
print("DEBUG: RAG System Test")
print("=" * 60)

# Load and process data
print("\n1. Loading product data...")
text = load_json("data/product.json")
print(f"   Loaded {len(text)} characters of JSON")

# Check if 8GB is in the text
print("\n2. Checking for '8GB' in product data...")
if "8GB" in text:
    print("   ✓ Found '8GB' in product data")
    # Find all products with 8GB
    matches = text.count('"8GB"')
    print(f"   Found {matches} instances of '8GB'")
else:
    print("   ✗ '8GB' NOT found in product data")

# Clean and chunk
print("\n3. Cleaning and chunking text...")
clean = clean_text(text)
print(f"   After cleaning: {len(clean)} characters")

chunks = chunk_text(clean, size=500, overlap=100)
print(f"   Created {len(chunks)} chunks")

# Show first few chunks
print("\n4. First 2 chunks (first 200 chars each):")
for i, chunk in enumerate(chunks[:2]):
    print(f"   Chunk {i}: {chunk[:200]}...")

# Create embeddings
print("\n5. Creating embeddings...")
model, embeddings = create_embeddings(chunks)
print(f"   Created {len(embeddings)} embeddings of dimension {len(embeddings[0])}")

# Create FAISS index
print("\n6. Creating FAISS index...")
index = create_index(embeddings)
print(f"   Index created with {index.ntotal} vectors")

# Test query
print("\n7. Testing RAG query for '8GB RAM phones'...")
query = "Which phones have 8GB RAM and what are their prices?"

# Get embeddings for query
query_vector = model.encode([query])
print(f"   Query embedding created with dimension {len(query_vector[0])}")

# Search index
import numpy as np
D, I = index.search(np.array(query_vector).astype("float32"), k=5)
print(f"   Found top 5 nearest chunks (distances: {D[0]})")

# Show retrieved chunks
print("\n8. Retrieved chunks:")
for i, idx in enumerate(I[0]):
    chunk = chunks[idx]
    print(f"   Chunk {idx}: {chunk[:150]}...")
    if "8GB" in chunk:
        print(f"   ✓ Contains '8GB'")
    else:
        print(f"   ✗ Does NOT contain '8GB'")

# Test the full RAG tool
print("\n9. Testing full RAG tool...")
memory = []
try:
    result = rag_tool(query, model, index, chunks, ask_llm, memory)
    print(f"   Result: {result[:200]}...")
except Exception as e:
    print(f"   Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Debug complete")
print("=" * 60)
