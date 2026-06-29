#!/usr/bin/env python
"""Debug script to test the product search tool directly"""

import json
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.product_search import search_products_by_specs

print("=" * 60)
print("DEBUG: Product Search Tool Test")
print("=" * 60)

# Test the search_products_by_specs function
print("\n1. Testing search_products_by_specs with '8GB RAM'...")
result_str = search_products_by_specs("8GB RAM")
print(f"   Raw result: {result_str[:200]}...")

result = json.loads(result_str)
print(f"\n   Parsed result structure:")
print(f"   - Message: {result['message']}")
print(f"   - Number of products: {len(result['result'])}")

if result['result']:
    print(f"\n   First 3 products:")
    for i, product in enumerate(result['result'][:3]):
        print(f"   {i+1}. {product['name']} - ${product['price']}")

# Test various queries
print("\n" + "=" * 60)
print("2. Testing various queries:")
print("=" * 60)

test_queries = [
    "Which phones have 8GB RAM and what are their prices?",
    "8GB RAM phones",
    "12GB RAM devices",
    "6GB storage phones",
]

for query in test_queries:
    result_str = search_products_by_specs(query)
    result = json.loads(result_str)
    count = len(result['result'])
    print(f"\n   Query: '{query}'")
    print(f"   Results: {count} products")

print("\n" + "=" * 60)
print("Debug complete")
print("=" * 60)
