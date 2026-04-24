from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from .kg_graph import app as kg_app
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app_api = FastAPI()

# Add CORS middleware
app_api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the directory of the current file
current_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(current_dir, "templates")

# Mount templates directory so linked assets (CSS, JS) are served correctly
app_api.mount("/static", StaticFiles(directory=templates_dir), name="static")

@app_api.get("/", response_class=HTMLResponse)
def read_root():
    index_path = os.path.join(templates_dir, "index.html")
    logger.info(f"Serving index.html from {index_path}")
    if not os.path.exists(index_path):
        logger.error(f"index.html not found at {index_path}")
        return HTMLResponse(content="<h1>Chat UI not found</h1>", status_code=404)
    logger.info(f"Returning FileResponse for {index_path}")
    return FileResponse(index_path, media_type="text/html")

@app_api.get("/health")
def health_check():
    return {"status": "ok"}

class QueryRequest(BaseModel):
    message: str
    thread_id: str

@app_api.post("/chat")
def chat(req: QueryRequest):
    logger.info(f"Chat request: {req.message[:50]}... (Thread: {req.thread_id})")
    try:
        state = {
            "question": req.message,
            "messages": [HumanMessage(content=req.message)],
            "intent": None,
            "cypher": None,
            "cypher_result": None,
            "revision_count": 0
        }
        result = kg_app.invoke(
            state,
            config={"configurable": {"thread_id": req.thread_id}}
        )

        if not result or "messages" not in result or not result["messages"]:
            logger.error("Graph invocation returned no messages")
            return {"response": "I couldn't generate a response. Please try again."}

        ai_response = result["messages"][-1].content
        
        # Ensure it's a string
        if not isinstance(ai_response, str):
            ai_response = str(ai_response)

        return {"response": ai_response}
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Error in /chat: {error_trace}")
        # Return a 200 with error message in JSON, or could use 500
        return {"response": f"Sorry, an error occurred: {str(e)}"}
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app_api, host="0.0.0.0", port=8000)
