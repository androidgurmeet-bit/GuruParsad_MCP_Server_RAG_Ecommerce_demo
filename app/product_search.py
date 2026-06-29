"""Product search tool that returns structured data"""

import json
import re
from pathlib import Path


# Global cache for products - will be populated by MCP server
_products_cache = None


def set_products_cache(products: list) -> None:
    """Called by MCP server to provide loaded product data"""
    global _products_cache
    _products_cache = products


def search_products_by_specs(query: str) -> str:
    """
    Search products by RAM specifications and return structured JSON.
    
    Args:
        query: Search query (e.g., "8GB RAM", "phones with 12GB")
    
    Returns:
        JSON string with matching products including id, name, and price
    """
    # Use cached products from MCP server, or load if not available
    global _products_cache
    
    if _products_cache is None:
        # Fallback: try to load from file
        possible_paths = [
            Path(__file__).parent.parent / "data" / "product.json",
            Path(__file__).parent / "data" / "product.json",
            Path.cwd() / "data" / "product.json",
            Path("data/product.json"),
        ]
        
        data_path = None
        for path in possible_paths:
            if path.exists():
                data_path = path
                break
        
        if data_path is None:
            return json.dumps({
                "result": [],
                "message": f"Error: product.json not found. Tried: {[str(p) for p in possible_paths]}"
            })
        
        try:
            with open(data_path, 'r') as f:
                products = json.load(f)
                _products_cache = products
        except Exception as e:
            return json.dumps({
                "result": [],
                "message": f"Error loading product data: {str(e)}"
            })
    
    products = _products_cache
    
    # Extract RAM amount from query
    query_lower = query.lower()
    
    # Find RAM specification in query (e.g., "8GB" or "8GB RAM")
    ram_match = re.search(r'(\d+)\s*gb', query_lower)
    if not ram_match:
        return json.dumps({
            "result": [],
            "message": f"Could not find RAM specification in query: {query}. Try 'phones with 8GB RAM'"
        })
    
    target_ram = int(ram_match.group(1))
    # Pattern: matches the RAM number followed by GB, but NOT when preceded by a digit
    # This avoids matching "8GB" in "128GB"
    pattern = r'(?<!\d)' + str(target_ram) + r'(?:gb|GB)'
    
    matching_products = []
    
    for product in products:
        name = product.get("name", "")
        
        # Check if the specific RAM amount is in the product name using regex
        if re.search(pattern, name):
            matching_products.append({
                "id": product["id"],
                "name": product["name"],
                "price": product["price"],
                "quantity": product["quantity"],
                "productUrl": product.get("productUrl", "")
            })
    
    if not matching_products:
        return json.dumps({
            "result": [],
            "message": f"No products found with {target_ram}GB: {query}"
        })
    
    return json.dumps({
        "result": matching_products,
        "message": f"Found {len(matching_products)} products with {target_ram}GB"
    })


if __name__ == "__main__":
    # Test the function
    result = search_products_by_specs("8GB RAM phones")
    data = json.loads(result)
    print(json.dumps(data, indent=2))
    print(f"\nTotal products found: {len(data['result'])}")
