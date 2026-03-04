import sqlite3
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from .state import AgentState
from .prompts import SYSTEM_PROMPT, REPLAN_PROMPT, RESPONSE_PROMPT, INTENT_PROMPT, get_schema_string, CHITCHAT_PROMPT

load_dotenv()
llm = ChatOpenAI(model='gpt-5-mini', temperature=0)
DB_PATH = '/inventory_chatbot.db'

def intent_node(state: AgentState):
    """Determines the intent of the user's question."""
    question = state['question']
    system_prompt = SystemMessage(content=INTENT_PROMPT)
    human_prompt = HumanMessage(content=question)
    response = llm.invoke([system_prompt, human_prompt])
    return {
        **state,
        "intent": response.content.strip().upper(),
    }

def chitchat_node(state: AgentState):
    """Generates a response based on the user's question."""
    question = state['question']
    system_prompt = SystemMessage(content=CHITCHAT_PROMPT)
    human_prompt = HumanMessage(content=question)
    response = llm.invoke([system_prompt, human_prompt])
    return {
        **state,
        "messages": state['messages'] + [response],
    }

def sql_generator_node(state: AgentState):
    """Generates the initial SQL query based on the question."""
    question = state['question']

    system_prompt = SystemMessage(content=SYSTEM_PROMPT)
    human_prompt = HumanMessage(content=question)

    response = llm.invoke([system_prompt, human_prompt])

    def clean_sql(sql: str) -> str:
        sql = sql.strip()
        if sql.startswith("```"):
            sql = sql.split("```")[1]
        return sql.strip()

    sql_query = clean_sql(response.content)

    return {
        **state,
        'sql_query': sql_query,
        "messages": state['messages'] + [response],
        "error": None,
    }


def sql_executor_node(state: AgentState):
    """Executes the SQL query against the database."""
    sql_query = state["sql_query"]
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(sql_query)
        result = cursor.fetchall()
        conn.commit()
        conn.close()

        return {
            **state,
            "sql_result": result,
            "error": None,
        }
    except Exception as e:
        return {
            **state,
            "sql_result": None,
            "error": str(e),
        }

def sql_corrector_node(state: AgentState):
    """Refines the SQL if an error occurred."""
    error = state["error"]
    system_prompt = SystemMessage(content=REPLAN_PROMPT)
    human_prompt = HumanMessage(content=f"Here is the SQL error:\n{error}")
    response = llm.invoke([system_prompt, human_prompt])
    sql_query = response.content.strip()
    return {
        **state,
        "sql_query": sql_query,
        "error": None,
    }


def responder_node(state: AgentState):
    sql_result = state["sql_result"]
    system_prompt = SystemMessage(content=RESPONSE_PROMPT)
    human_prompt = HumanMessage(content=f"SQL Query:{state['sql_query']} Result Rows:{sql_result}")
    response = llm.invoke([system_prompt, human_prompt])
    return {
        **state,
        "messages": state["messages"] + [response],
    }
