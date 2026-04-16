from kg_graph import app
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


def main():
    print("Hello, I'm your assistant! How can I help you today. (Type 'exit/quit' to quit.)\n")
    conversation_history = []
    while True:
        user_input = input("You: ")
        if not user_input.strip():
            print("Please enter a valid question.")
            continue

        if user_input.strip().lower() in ["exit", "quit"]:
            break

        new_message = HumanMessage(content=user_input)
        conversation_history.append(new_message)

        state = {
            "messages": conversation_history,
            "question": user_input,
            "intent": None,
            "cypher": None,
            "cypher_result": None,
            "revision_count": 0
        }

        result = app.invoke(state, config=config)

        conversation_history.append(result["messages"][-1])

        print("\nBot:")
        print(result["messages"][-1].content)
        print("\n" + "-"*50 + "\n")

if __name__ == '__main__':
    main()