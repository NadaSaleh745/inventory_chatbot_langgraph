from fastapi import FastAPI
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from .kg_graph import app

app_api = FastAPI()

class QueryRequest(BaseModel):
    message: str
    thread_id: str

@app_api.post("/chat")
async def chat(req: QueryRequest):
    state = {
        "question": req.message,
        "messages": [HumanMessage(content=req.message)],
        "intent": None,
        "cypher": None,
        "cypher_result": None,
        "revision_count": 0
    }
    result = app.invoke(
        state,
        config={"configurable": {"thread_id": req.thread_id}}
    )

    ai_response = result["messages"][-1].content
    return {"response": ai_response}