import json
import re
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ecommerce-products")
PRODUCT_DATA_PATH = Path(__file__).parent / "data" / "product.json"



def load_products() -> list[dict]:
    with PRODUCT_DATA_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


@mcp.tool()
def list_products(limit: int = 20) -> list[dict]:
    """Return all available ecommerce products."""
    return load_products()[:limit]


@mcp.tool()
def get_product(product_id: int) -> dict:
    """Return a single product by id."""
    for product in load_products():
        if product.get("id") == product_id:
            return product
    return {"error": f"Product with id {product_id} was not found."}


@mcp.tool()
def search_products(query: str, limit: int = 20) -> list[dict]:
    """Search products by name, description, or specifications."""
    query = query.lower().strip()
    if not query:
        return []

    ram_match = re.search(r"\b\d+\s*gb\b", query)
    ram_term = ram_match.group(0).replace(" ", "") if ram_match else None

    matches = []
    for product in load_products():
        searchable_text = " ".join(
            str(product.get(field, ""))
            for field in ("name", "description", "specifications")
        ).lower()
        compact_searchable_text = searchable_text.replace(" ", "")
        has_matching_ram = bool(
            ram_term
            and (
                f"{ram_term}/" in compact_searchable_text
                or f"{ram_term}ram" in compact_searchable_text
            )
        )

        if query in searchable_text or has_matching_ram:
            matches.append(product)
            if len(matches) >= limit:
                break

    return matches


if __name__ == "__main__":
    mcp.run(transport="stdio")
