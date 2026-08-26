from app.calculator import calculator_tool
from app.llm import ask_llm
from app.rag import rag_tool


class Agent:
    """Base interface for a named agent."""

    name = "agent"

    def can_handle(self, query: str) -> bool:
        raise NotImplementedError

    def run(self, query: str) -> str:
        raise NotImplementedError


class CalculatorAgent(Agent):
    name = "calculator"

    def can_handle(self, query: str) -> bool:
        # Only route clearly mathematical expressions to the calculator.
        return any(
            op in query for op in ["+", "-", "*", "/"]
        ) and not query.lower().strip().startswith("what")

    def run(self, query: str) -> str:
        return calculator_tool(query)


class RAGAgent(Agent):
    name = "rag"

    def __init__(self, model, index, chunks, memory):
        self.model = model
        self.index = index
        self.chunks = chunks
        self.memory = memory

    def can_handle(self, query: str) -> bool:
        return True

    def run(self, query: str) -> str:
        return rag_tool(
            query, self.model, self.index, self.chunks, ask_llm, self.memory
        )


class MultiAgent:
    def __init__(self, agents):
        self.agents = agents

    def dispatch(self, query: str) -> str:
        for agent in self.agents:
            if agent.can_handle(query):
                print(f"Routing to: {agent.name}")
                return agent.run(query)
        return "I don't know how to handle that query."
