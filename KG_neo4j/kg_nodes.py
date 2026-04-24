import json
import os
import uuid
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from neo4j import GraphDatabase
from neo4j.time import Date, DateTime, Time, Duration
from .kg_state import AgentState
from .kg_prompts import INTENT_PROMPT, SYNTHESIZER_PROMPT, ADD_PROMPT, UPDATE_PROMPT, INQUIRE_PROMPT, DELETE_PROMPT, \
    REPLAN_PROMPT
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI as LlamaOpenAI
from dotenv import load_dotenv, find_dotenv
from langgraph.store.base import BaseStore

load_dotenv(find_dotenv())

llm = ChatOpenAI(model='gpt-5-mini', temperature=0)
Settings.llm = LlamaOpenAI(model='gpt-5-mini', temperature=0)

_neo4j_driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD")),
)


class _AuraGraphStore:
    """Minimal Neo4j graph store compatible with Aura Free (no APOC, no routing issues)."""

    def structured_query(self, query: str, param_map: dict = None) -> list:
        """Execute a Cypher query and return results as a list of dicts."""
        param_map = param_map or {}
        if query.startswith("```"):
            query = query.split("```")[1]
            if query.startswith("cypher"):
                query = query[6:]
            query = query.strip()
        with _neo4j_driver.session() as session:
            result = session.run(query, param_map)
            return [record.data() for record in result]


neo4j_graph_store = _AuraGraphStore()


def _convert_neo4j_types(obj):
    """Recursively convert Neo4j native types to Python native types for serialization."""
    if isinstance(obj, DateTime):
        # Convert Neo4j DateTime to Python datetime (ISO format string)
        return obj.isoformat()
    elif isinstance(obj, Date):
        # Convert Neo4j Date to Python date string
        return obj.isoformat()
    elif isinstance(obj, Time):
        # Convert Neo4j Time to Python time string
        return obj.isoformat()
    elif isinstance(obj, Duration):
        # Convert Neo4j Duration to total seconds
        return obj.total_seconds()
    elif isinstance(obj, dict):
        # Recursively convert dictionary values
        return {key: _convert_neo4j_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        # Recursively convert list items
        return [_convert_neo4j_types(item) for item in obj]
    else:
        # Return primitive types as-is
        return obj


def intent_node(state: AgentState, config: RunnableConfig, store: BaseStore):
    """Determines the intent of the user's question."""
    print("start intent")
    user_id = config["configurable"].get("thread_id", "default")
    memory_namespace = ("user_memories", user_id)
    messages = state["messages"]
    last_user_message = messages[-1].content if messages else ""

    combined_prompt = f"""
    Extract intent and facts from the user message.

    Intent must be one of the following exactly:
    CHITCHAT: User is just making conversation, greeting, or providing general facts/preferences without requesting a database operation.
    ADD: User explicitly requests to create/add records to the inventory database (e.g. SalesOrders, Items).
    UPDATE: User explicitly requests modifying database records.
    DELETE: User explicitly requests removing database records.
    INQUIRE: User asks a specific question about inventory data or operations that requires querying the database.

    Crucially:
    - If the user provides a fact or instruction to remember, but does NOT explicitly tell you to create/update an inventory database record, the intent is CHITCHAT.
    - INQUIRE should only be used when the user is clearly asking for specific inventory information from the database.


    Also extract facts if they exist:
    - Preferences
    - Goals
    - Important values
    - Instructions 

    Message:
    {last_user_message}

    Return JSON:
    {{
      "intent": "...",
      "facts": ["...", "..."]
    }}
    """

    response = llm.invoke(combined_prompt).content
    try:
        parsed = json.loads(response)
        intent = parsed.get("intent", "INQUIRE").upper()
        facts = parsed.get("facts", [])
    except:
        intent = "INQUIRE"
        facts = []

    for fact in facts:
        if isinstance(fact, str) and fact.strip():
            if len(fact) > 2000:
                print(f"Ignored massive fact: {len(fact)} characters")
                continue
            store.put(memory_namespace, str(uuid.uuid4()), {"fact": fact.strip()})

    all_items = store.search(memory_namespace, query="", limit=100)

    print("\n CURRENT MEMORY STATE:")

    for item in all_items:
        print(item.value)
    print("-" * 40)
    retrieved_items = store.search(memory_namespace, query=state["question"], limit=5)
    semantic_memory = []

    if retrieved_items:
        # Extract the 'fact' strings from the dictionary we stored them in
        semantic_memory = [item.value["fact"] for item in retrieved_items]
        print(f"Retrieved {len(semantic_memory)} memories for context.")

    print("stop intent")

    return {
        "intent": intent,
        "semantic_memory": semantic_memory
    }


def replan_node(state: AgentState):
    system_prompt = SystemMessage(content=REPLAN_PROMPT)

    human_prompt = HumanMessage(content=f"""
                                User request:
                                {state['question']}

                                Broken query:
                                {state['cypher']}

                                Error:
                                {state['error']}
                                """)

    response = llm.invoke([system_prompt, human_prompt])

    return {
        "cypher": response.content.strip(),
        "error": None,
        "revision_count": state.get("revision_count", 0) + 1
    }


def execute_cypher(state: AgentState):
    """Executes Cypher query using _AuraGraphStore"""
    query = state.get('cypher')
    print("CYPHER QUERY TO EXECUTE:\n", query)

    # If no Cypher query is provided, return error
    if not query:
        return {
            "error": "No Cypher query generated",
            "cypher_result": None
        }

    try:
        # Clean up the query (remove markdown code fences if present)
        if query.startswith("```"):
            query = query.split("```")[1]
            if query.startswith("cypher"):
                query = query[6:]
            query = query.strip()

        # Execute query using _AuraGraphStore
        result = neo4j_graph_store.structured_query(query)
        MAX_RESULTS = 10
        if result and len(result) > MAX_RESULTS:
            print(f"Truncating results from {len(result)} to {MAX_RESULTS}")
            result = result[:MAX_RESULTS]
        serializable_result = _convert_neo4j_types(result) if result else []
        print(serializable_result)

        return {
            "cypher_result": serializable_result,
            "error": None
        }
    except Exception as e:
        return {
            "error": str(e),
            "cypher_result": None
        }


def synthesize_node(state: AgentState):
    """Synthesizes the cypher query result into a human-readable response."""
    print("start syn")

    cypher_result = state['cypher_result']
    intent = state.get('intent')
    semantic_memory = state.get("semantic_memory", [])

    # Build context from semantic memory
    context = ""
    if semantic_memory:
        context = f"\nRelevant facts from memory:\n" + "\n".join(semantic_memory)

    # Handle None or error cases
    if cypher_result is None:
        error_msg = state.get('error', 'No results found or an error occurred.')
        error_response = AIMessage(content=f"I encountered an issue while querying the database: {error_msg}")
        return {
            "messages": [error_response],
        }

    # Convert result to string if it's a list (from Cypher query results)
    if isinstance(cypher_result, list):
        if len(cypher_result) == 0:
            has_return = 'RETURN' in state.get('cypher', '').upper()
            if has_return and intent in ['ADD', 'UPDATE']:
                failure_msg = AIMessage(
                    content="The operation failed. The required related entities (like the customer, site, or item) could not be found in the database. Please verify they exist and try again.")
                return {
                    "messages": [failure_msg],
                }
            elif intent == 'ADD':
                success_response = AIMessage(content="The data has been successfully added to the knowledge graph.")
                return {
                    "messages": [success_response],
                }
            elif intent == 'UPDATE':
                success_response = AIMessage(content="The data has been successfully updated in the knowledge graph.")
                return {
                    "messages": [success_response],
                }
            elif intent == 'DELETE':
                success_response = AIMessage(content="The data has been successfully deleted from the knowledge graph.")
                return {
                    "messages": [success_response],
                }
            else:
                empty_response = AIMessage(
                    content="I couldn't find any information matching your query in the database.")
                return {
                    "messages": [empty_response],
                }

        # Format the list of dictionaries as a readable string
        cypher_result_str = str(cypher_result)
    else:
        cypher_result_str = str(cypher_result)

    MAX_CHAR_LIMIT = 8000
    if len(cypher_result_str) > MAX_CHAR_LIMIT:
        cypher_result_str = cypher_result_str[:MAX_CHAR_LIMIT] + "\n... [RESULTS TRUNCATED DUE TO LENGTH]"

    # Check if the result is empty after conversion
    if not cypher_result_str.strip() or cypher_result_str == "[]":
        empty_response = AIMessage(content="I couldn't find any information matching your query in the database.")
        return {
            "messages": [empty_response],
        }

    # Generate synthesized response using LLM
    system_prompt = SystemMessage(content=SYNTHESIZER_PROMPT)
    last_user_message = state["messages"][-1].content

    human_prompt = HumanMessage(
        content=f"""
    User request:
    {last_user_message}

    Database result:
    {cypher_result_str}

    {context}
    """
    )

    response = llm.invoke(
        [system_prompt, human_prompt],
        config={"max_tokens": 300}
    )

    print("stop syn")

    return {
        "messages": [response],
    }


def add_node(state: AgentState):
    """Adds a new node to the graph"""
    print("start add")
    semantic_memory = state.get("semantic_memory", [])
    # Build context from semantic memory
    context = ""
    if semantic_memory:
        context = f"\nRelevant facts from memory:\n" + "\n".join(semantic_memory)
    system_prompt = SystemMessage(content=ADD_PROMPT)
    last_user_message = state["messages"][-1].content

    human_prompt = HumanMessage(
        content=f"""
    User request:
    {last_user_message}

    {context}
    """
    )

    response = llm.invoke(
        [system_prompt, human_prompt],
        config={"max_tokens": 300}
    )
    print(response)
    print("stop add")
    return {
        "cypher": response.content.strip(),
    }


def update_node(state: AgentState):
    """Updates an existing node in the graph"""
    semantic_memory = state.get("semantic_memory", [])
    # Build context from semantic memory
    context = ""
    if semantic_memory:
        context = f"\nRelevant facts from memory:\n" + "\n".join(semantic_memory)
    last_user_message = state["messages"][-1].content
    system_prompt = SystemMessage(content=UPDATE_PROMPT)
    human_prompt = HumanMessage(content=f"""
    User request:
    {last_user_message}

    {context}
    """)
    response = llm.invoke([system_prompt, human_prompt])
    return {
        "cypher": response.content.strip(),
    }


def inquire_node(state: AgentState):
    """Inquires about a node in the graph"""
    print("start inq")

    semantic_memory = state.get("semantic_memory", [])
    # Build context from semantic memory
    context = ""
    if semantic_memory:
        context = f"\nRelevant facts from memory:\n" + "\n".join(semantic_memory)
    last_user_message = state["messages"][-1].content
    system_prompt = SystemMessage(content=INQUIRE_PROMPT)
    human_prompt = HumanMessage(content=f"""
    User request:
    {last_user_message}

    {context}
    """)
    response = llm.invoke([system_prompt, human_prompt])

    print("stop inq")

    return {
        "cypher": response.content.strip(),
    }


def delete_node(state: AgentState):
    """Deletes a node from the graph"""
    semantic_memory = state.get("semantic_memory", [])
    # Build context from semantic memory
    context = ""
    if semantic_memory:
        context = f"\nRelevant facts from memory:\n" + "\n".join(semantic_memory)
    last_user_message = state["messages"][-1].content
    system_prompt = SystemMessage(content=DELETE_PROMPT)
    human_prompt = HumanMessage(content=f"""
    User request:
    {last_user_message}

    {context}
    """)
    response = llm.invoke([system_prompt, human_prompt])
    return {
        "cypher": response.content.strip(),
    }


def chitchat_node(state: AgentState):
    """Handles general conversational interaction without querying the database."""
    print("start chitchat")

    system_prompt = SystemMessage(
        content="You are a helpful and polite inventory management chatbot. The user is just chatting with you, greeting, or providing some information without asking for a database operation. Respond conversationally, acknowledge any facts they shared if relevant, and ask how you can help them with their inventory or sales orders. Do not mention databases or internal operations.")
    last_user_message = state["messages"][-1].content
    human_prompt = HumanMessage(content=last_user_message)

    response = llm.invoke([system_prompt, human_prompt], config={"max_tokens": 150})

    print("stop chitchat")

    return {
        "messages": [response],
    }