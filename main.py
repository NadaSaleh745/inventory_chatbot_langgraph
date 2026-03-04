from inventory_chatbot_langgraph.agent.graph import app
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
import os

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

config = {
    "configurable": {
        "thread_id": "temp_thread_001"
    }
}


def print_stream(stream):
    for s in stream:
        message = s["message"][-1]
        if isinstance(message, tuple):
            print(message)
        else:
            message.pretty_print()

def main():
    print("Hello, I'm your assistant! How can I help you today. (Type 'exit/quit' to quit.)\n")
    while True:
        user_input = input("You: ")
        if not user_input.strip():
            print("Please enter a valid question.")
            continue

        if user_input.lower() in ["exit", "quit"]:
            break

        state = {
            "messages": [HumanMessage(content=user_input)],
            "question": user_input,
            "sql_query": None,
            "sql_result": None,
            "error": None,
            "intent": None,
            "revision_count": 0
        }

        result = app.invoke(state, config=config)

        print("\nBot:")
        print(result["messages"][-1].content)
        print("\n" + "-"*50 + "\n")

if __name__ == '__main__':
    main()