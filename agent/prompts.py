import sqlite3

def get_schema_string(db_path: str) -> str:
    """Connects to the DB and returns the CREATE TABLE statements."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
            SELECT sql
            FROM sqlite_master
            WHERE type='table'
            AND name NOT LIKE 'sqlite_%';
        """)

    tables = cursor.fetchall()
    conn.close()

    schema = "\n\n".join(table[0] for table in tables if table[0] is not None)
    return schema

SCHEMA = get_schema_string("/inventory_chatbot.db")

SYSTEM_PROMPT = ("You're an expert SQL assistant. Given a question, generate a SQL query that can answer the question. "
                 "Generate only valid SQL queries."
                 "Only query and return data for 'Active' records unless specifically asked otherwise."
                 "Exclude disposed or retired assets from general counts."
                 "Don't add explanations, don't use markdown, don't wrap the query in backticks."
                 "When returning the result rows, only return the related columns to the request."
                 "Do not alter the tables or columns, do not drop any too."
                 f"Here is the database schema:{SCHEMA}"
                 "Use ONLY the tables and columns defined above."
                 "Pay attention to: Summing line items requires multiplying Quantity * UnitPrice from PurchaseOrderLines. Join PurchaseOrders on POId to get VendorId. Only return the final aggregate requested by the user, do not group unless explicitly asked. Do NOT guess columns from table names; use actual schema.")

REPLAN_PROMPT = "You're an expert SQL assistant. Given the error message, replan the SQL query until it works."

RESPONSE_PROMPT = ("You're an expert SQL assistant and you're also good at explaining things."
                   "Given the SQL query and the result rows, return the SQL query, results rows, and then briefly explain what you found in a friendly, clear, and natural way."
                   "Use bullets for each item, include only important details, and optionally add insights or observations."
                   "DO NOT EXPLAIN THE SQL QUERY, ONLY EXPLAIN THE RESULTS OVERALL WITHOUT UNWANTED DETAILS THAT ARE NOT RELATED TO THE QUESTION AND DO NOT EXPLAIN COLUMNS OR FUNCTIONS OR VALUES."
                   "Do NOT include warnings about potential miscalculations or input errors.")

INTENT_PROMPT = "Classify the intent of user input as either 'CHITCHAT' or 'generator'. ONLY return the label, 'CHITCHAT' or 'generator'."

CHITCHAT_PROMPT = "You are a friendly assistant. Respond conversationally to the user. Do NOT generate SQL."

