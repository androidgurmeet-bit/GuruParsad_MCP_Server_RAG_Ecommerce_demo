import sys
from contextlib import AsyncExitStack, asynccontextmanager
from pathlib import Path
import json

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import tool
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_ollama import ChatOllama
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pydantic import BaseModel

from app.embeddings import chunk_text, clean_text, create_embeddings, load_json
from app.rag import create_index, retrieve_chunks

load_dotenv()


class QueryRequest(BaseModel):
    query: str


PRODUCT_RESPONSE_FIELDS = ("id", "name", "price", "quantity", "productUrl")
PRODUCT_DATA_PATH = Path(__file__).parent / "data" / "product.json"


def load_product_details() -> list[dict]:
    with PRODUCT_DATA_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def normalize_product(product: dict) -> dict:
    return {field: product.get(field) for field in PRODUCT_RESPONSE_FIELDS}


def get_final_answer(messages: list) -> str:
    for message in reversed(messages):
        if isinstance(message, AIMessage) and message.content:
            return str(message.content)
    return ""


def extract_products(messages: list) -> list[dict]:
    products_by_id = {}

    for message in messages:
        if not isinstance(message, ToolMessage):
            continue

        # Try to parse JSON response from search_products or other tools
        result = None
        
        # First try artifact (LangChain structured format)
        artifact = getattr(message, "artifact", None)
        if isinstance(artifact, dict):
            result = artifact.get("structured_content", {}).get(
                "result"
            ) or artifact.get("result")
        
        # If no artifact, try to parse the message content as JSON
        if result is None:
            try:
                content = message.content
                if isinstance(content, str) and content.strip():
                    parsed = json.loads(content)
                    result = parsed.get("result") or parsed
            except (json.JSONDecodeError, AttributeError):
                pass

        if result is None:
            continue

        candidates = result if isinstance(result, list) else [result]
        for candidate in candidates:
            if isinstance(candidate, dict) and "id" in candidate:
                products_by_id[candidate["id"]] = normalize_product(candidate)

    return list(products_by_id.values())


def extract_rag_sources(messages: list) -> list[str]:
    sources: list[str] = []

    for message in messages:
        if not isinstance(message, ToolMessage):
            continue

        # ToolMessage.name is the tool name for LangChain tools.
        if getattr(message, "name", None) != "rag_query":
            continue

        payload = None

        artifact = getattr(message, "artifact", None)
        if isinstance(artifact, dict):
            payload = (
                artifact.get("structured_content", {}).get("result")
                or artifact.get("result")
                or artifact
            )

        if payload is None:
            try:
                if isinstance(message.content, str) and message.content.strip():
                    payload = json.loads(message.content)
            except json.JSONDecodeError:
                payload = None

        if isinstance(payload, dict):
            raw_sources = payload.get("sources") or []
            if isinstance(raw_sources, list):
                for item in raw_sources:
                    if isinstance(item, str) and item.strip():
                        sources.append(item)

    # de-dup while preserving order
    uniq: list[str] = []
    seen: set[str] = set()
    for s in sources:
        if s in seen:
            continue
        seen.add(s)
        uniq.append(s)
    return uniq


def build_answer(llm_answer: str, products: list[dict]) -> str:
    if llm_answer and llm_answer.strip():
        return llm_answer.strip()

    if not products:
        return "I couldn't find matching products for your query."

    count = len(products)
    preview = ", ".join(product.get("name", "Product") for product in products[:3])
    if count > 3:
        preview += f", and {count - 3} more"
    return f"Found {count} matching product{'s' if count != 1 else ''}: {preview}."


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncExitStack() as stack:
        server_params = StdioServerParameters(
            command=sys.executable,
            args=["mcp_server_fastmcp.py"],
        )
        read, write = await stack.enter_async_context(stdio_client(server_params))
        session = await stack.enter_async_context(ClientSession(read, write))
        await session.initialize()

        tools = await load_mcp_tools(session)
        llm = ChatOllama(model="qwen3:1.7b")

        # Build a small local RAG index once at startup (from product.json).
        rag_text = load_json(str(PRODUCT_DATA_PATH))
        rag_clean = clean_text(rag_text)
        rag_chunks = chunk_text(rag_clean, size=600, overlap=120)
        rag_embed_model, rag_embeddings = create_embeddings(rag_chunks)
        rag_index = create_index(rag_embeddings)

        app.state.rag_chunks = rag_chunks
        app.state.rag_embed_model = rag_embed_model
        app.state.rag_index = rag_index
        app.state.llm = llm

        @tool("rag_query")
        def rag_query(query: str, k: int = 5) -> dict:
            """
            Use RAG to answer questions from document context (policies, explanations, long specs).
            Do NOT use this for product listing/price/stock queries; use search_products instead.
            Returns an answer plus retrieved context chunks as sources.
            """
            chunks = retrieve_chunks(
                query,
                embed_model=app.state.rag_embed_model,
                index=app.state.rag_index,
                chunks=app.state.rag_chunks,
                k=k,
            )

            context = "\n\n---\n\n".join(chunks)
            prompt = (
                "You are a strict ecommerce assistant.\n"
                "Rules:\n"
                "- Answer ONLY using the provided Context.\n"
                "- If the answer is not in Context, say: Not found in context.\n"
                "- Keep the answer short and user-friendly.\n\n"
                f"Context:\n{context}\n\n"
                f"Question: {query}\n"
            )

            answer = str(app.state.llm.invoke(prompt).content)
            return {"answer": answer, "sources": chunks}

        app.state.agent = create_agent(
            model=llm,
            tools=[*tools, rag_query],
            system_prompt=(
                "You are an ecommerce assistant. When users ask about products, RAM, storage, prices, stock, "
                "specifications, or any product details, ALWAYS use the search_products tool first to find matching "
                "products. Never use rag_query for product searches - use search_products instead. "
                "The search_products tool returns structured data with product IDs and prices. "
                "Keep your final answer concise and user-friendly."
            ),
        )
        yield


app = FastAPI(title="Ecommerce MCP RAG Agent", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/query")
async def query(req: QueryRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="query must not be empty")

    result = await app.state.agent.ainvoke(
        {"messages": [{"role": "user", "content": req.query}]}
    )

    messages = result.get("messages", [])
    products = extract_products(messages)
    sources = extract_rag_sources(messages)
    llm_answer = get_final_answer(messages)

    return {
        "query": req.query,
        "answer": build_answer(llm_answer, products),
        "products": products,
        "sources": sources,
    }


@app.get("/products/{product_id}")
async def product_details(product_id: int):
    for product in load_product_details():
        if product.get("id") == product_id:
            return normalize_product(product)

    raise HTTPException(status_code=404, detail="product not found")
