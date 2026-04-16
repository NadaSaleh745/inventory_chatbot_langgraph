import operator
from typing import TypedDict, Annotated, List, Optional
from langchain_core.messages import BaseMessage

def add_memories(left: list[str], right: list[str]) -> list[str]:
    """Append memories to existing memories."""
    return left + right

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    question: str
    intent: str
    cypher: str
    cypher_result: str
    error: Optional[str]
    semantic_memory: Annotated[list[str], add_memories]
