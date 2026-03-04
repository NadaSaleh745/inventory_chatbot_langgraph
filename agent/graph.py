from langgraph.graph import StateGraph, END
from inventory_chatbot_langgraph.agent.state import AgentState
from inventory_chatbot_langgraph.agent.nodes import sql_generator_node, sql_executor_node, sql_corrector_node, responder_node, intent_node, chitchat_node
from langgraph.checkpoint.memory import MemorySaver

def executor_should_continue(state: AgentState):
    if state.get("error"):
        return "corrector"
    else:
        return "responder"

def intent_should_continue(state: AgentState):
    if state["intent"] == "CHITCHAT":
        return "chitchat"
    else:
        return "generator"

workflow = StateGraph(AgentState)
workflow.add_node('generator', sql_generator_node)
workflow.add_node('executor', sql_executor_node)
workflow.add_node('corrector', sql_corrector_node)
workflow.add_node('responder', responder_node)
workflow.add_node('intent', intent_node)
workflow.add_node('chitchat', chitchat_node)
workflow.set_entry_point('intent')
workflow.add_edge('generator', 'executor')
workflow.add_conditional_edges('intent', intent_should_continue, {'chitchat': 'chitchat', 'generator': 'generator'})
workflow.add_conditional_edges('executor', executor_should_continue, {'corrector': 'corrector', 'responder': 'responder'})
workflow.add_edge('corrector', 'executor')
workflow.add_edge('responder', END)
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)