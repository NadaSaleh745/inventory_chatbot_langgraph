import os
from langchain_openai import OpenAIEmbeddings
from langgraph.graph import StateGraph, END
from langgraph.store.base import IndexConfig
from langgraph.store.redis import RedisStore
from kg_nodes import intent_node, execute_cypher, synthesize_node, add_node, inquire_node, update_node, delete_node, replan_node, chitchat_node
from kg_state import AgentState
from langgraph.checkpoint.redis import RedisSaver
from dotenv import load_dotenv

load_dotenv()

REDIS_URI = os.getenv("REDIS_URI")

index_config: IndexConfig = {
    "dims": 1536,
    "embed": OpenAIEmbeddings(model="text-embedding-3-small"),
    "ann_index_config": {
        "vector_type": "vector",
    },
    "distance_type": "cosine",
}

checkpointer_cm = RedisSaver.from_conn_string(REDIS_URI)
checkpointer = checkpointer_cm.__enter__()
checkpointer.setup()

redis_store_cm = RedisStore.from_conn_string(REDIS_URI, index=index_config)
redis_store = redis_store_cm.__enter__()
redis_store.setup()

def intent_router(state: AgentState):
    intent = state.get("intent", "INQUIRE")
    if intent == "ADD":
        return "add"
    elif intent == "INQUIRE":
        return "inquire"
    elif intent == "UPDATE":
        return "update"
    elif intent == "DELETE":
        return "delete"
    elif intent == "CHITCHAT":
        return "chitchat"
    else:
        return "inquire"

def executor_should_continue(state: AgentState):
    if state.get("error"):
        return "replan"
    else:
        return "synthesize"

workflow = StateGraph(AgentState)
workflow.add_node('intent', intent_node)
workflow.add_node('execute', execute_cypher)
workflow.add_node('synthesize', synthesize_node)
workflow.add_node('replan', replan_node)

workflow.add_node('add', add_node)
workflow.add_node('inquire', inquire_node)
workflow.add_node('update', update_node)
workflow.add_node('delete', delete_node)
workflow.add_node('chitchat', chitchat_node)

workflow.set_entry_point('intent')

workflow.add_conditional_edges('intent', intent_router, {'add': 'add', 'inquire': 'inquire', 'update': 'update', 'delete': 'delete', 'chitchat': 'chitchat'})
workflow.add_conditional_edges('execute', executor_should_continue, {'replan': 'replan', 'synthesize': 'synthesize'})
workflow.add_edge('add', 'execute')
workflow.add_edge('inquire', 'execute')
workflow.add_edge('update', 'execute')
workflow.add_edge('delete', 'execute')
workflow.add_edge('replan', 'execute')
workflow.add_edge('synthesize', END)
workflow.add_edge('chitchat', END)
app = workflow.compile(checkpointer=checkpointer, store=redis_store)

print("GRAPH COMPILED")

