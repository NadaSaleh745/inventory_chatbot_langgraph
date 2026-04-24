import uvicorn
import os
import sys

# Add project root to sys.path to allow absolute imports
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

if __name__ == "__main__":
    uvicorn.run("inventory_chatbot_langgraph.KG_neo4j.KG_agent_api:app_api", host="0.0.0.0", port=8000, reload=True)
