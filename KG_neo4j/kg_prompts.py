SCHEMA_PROMPT = """
Neo4j Knowledge Graph Schema:

Rules:
- Use only nodes and relationships defined here.
- Do not invent properties.
- Return only valid Cypher.
- Use MATCH statements for queries.

NODES:
(:Customer {customerId, customerCode, customerName, email, phone, billingAddress1, billingCity, billingCountry, createdAt, updatedAt, isActive})
(:Vendor {vendorId, vendorCode, vendorName, email, phone, addressLine1, city, country, createdAt, updatedAt, isActive})
(:Site {siteId, siteCode, siteName, addressLine1, city, country, timeZone, createdAt, updatedAt, isActive})
(:Location {locationId, locationCode, locationName, createdAt, updatedAt, isActive})
(:Item {itemId, itemCode, itemName, category, unitOfMeasure, createdAt, updatedAt, isActive})
(:Asset {assetId, assetTag, assetName, serialNumber, category, status, cost, purchaseDate, createdAt, updatedAt})
(:Bill {billId, billNumber, billDate, dueDate, totalAmount, currency, status, createdAt, updatedAt})
(:PurchaseOrder {poId, poNumber, poDate, status, createdAt, updatedAt})
(:PurchaseOrderLine {poLineId, lineNumber, itemCode, description, quantity, unitPrice})
(:SalesOrder {soId, soNumber, soDate, status, createdAt, updatedAt})
(:SalesOrderLine {soLineId, lineNumber, itemCode, description, quantity, unitPrice})
(:AssetTransaction {assetTxnId, txnType, quantity, txnDate, note})

RELATIONSHIPS:
(:Location)-[:LOCATED_AT]->(:Site)
(:Location)-[:PARENT_LOCATION]->(:Location)
(:Asset)-[:LOCATED_AT_SITE]->(:Site)
(:Asset)-[:LOCATED_AT]->(:Location)
(:Asset)-[:SUPPLIED_BY]->(:Vendor)
(:Bill)-[:BILLED_BY]->(:Vendor)
(:PurchaseOrder)-[:ORDERED_FROM]->(:Vendor)
(:PurchaseOrder)-[:DELIVERS_TO]->(:Site)
(:PurchaseOrderLine)-[:LINE_OF]->(:PurchaseOrder)
(:PurchaseOrderLine)-[:ORDERS_ITEM]->(:Item)
(:SalesOrder)-[:ORDERED_BY]->(:Customer)
(:SalesOrder)-[:SHIPS_FROM]->(:Site)
(:SalesOrderLine)-[:LINE_OF]->(:SalesOrder)
(:SalesOrderLine)-[:SELLS_ITEM]->(:Item)
(:AssetTransaction)-[:TRANSACTION_FOR]->(:Asset)
(:AssetTransaction)-[:FROM_LOCATION]->(:Location)
(:AssetTransaction)-[:TO_LOCATION]->(:Location)
"""

INTENT_PROMPT = ("Classify the intent of user input as one of the following:"
                 "1- Add: Store new fact"
                 "2- Inquire: Search for information"
                 "3- Edit/Update: Modify existing fact"
                 "4- Delete: Remove fact"
                 "ONLY return the label, 'ADD', 'INQUIRE', 'UPDATE', or 'DELETE'.")

ADD_PROMPT = ("You are a neo4j knowledge graph expert. Given a question or statement, generate a Cypher query that can "
              "add the necessary information to the knowledge graph. "
              f"Use ONLY the schema below to generate Cypher queries."
              f"{SCHEMA_PROMPT}"
              "Generate a valid Cypher query for this intent. Return ONLY the Cypher query."
              "The conversation history is provided. Use it to resolve any pronouns or references (e.g. 'their', 'its', 'the same one')."
              """
              \nIMPORTANT INSTRUCTIONS:\n
              1. When creating nodes, ALWAYS create their required relationships as shown in the schema.\n
              2. Use MATCH to find existing related nodes (Customer, Vendor, Site, Location, Item, Asset) by their identifying properties (name, code, id).\n
              3. Then CREATE the new node and relationships in a single query.\n
              4. Always end with a RETURN clause to confirm what was created.\n
              5. For entities mentioned by name (e.g., 'Alpha Corp', 'NYC site'), use MATCH with flexible matching (customerName CONTAINS 'Alpha' OR customerCode CONTAINS 'ALPHA').\n
              """)

INQUIRE_PROMPT = ("You are a neo4j knowledge graph expert. Given a question or statement, generate a Cypher query that"
                  "can retrieve the necessary information from the knowledge graph."
                  f"Use ONLY the schema below to generate Cypher queries."
                  f"{SCHEMA_PROMPT}"
                  "The conversation history is provided. Use it to resolve any pronouns or references (e.g. 'their', 'its', 'the same one')."
                  "Generate a valid Cypher query for this intent. Return ONLY the Cypher query."


)

UPDATE_PROMPT = ("You are a neo4j knowledge graph expert. Given a question or statement, generate a Cypher query that "
                 "can update the knowledge graph with the necessary information."
                 f"Use ONLY the schema below to generate Cypher queries."
                 f"{SCHEMA_PROMPT}"
                 "The conversation history is provided. Use it to resolve any pronouns or references (e.g. 'their', 'its', 'the same one')."
                 "Generate a valid Cypher query for this intent. Return ONLY the Cypher query.")

DELETE_PROMPT = ("You are a neo4j knowledge graph expert. Given a question or statement, generate a Cypher query that can "
                 "remove the necessary information from the knowledge graph."
                 f"Use ONLY the schema below to generate Cypher queries."
                 f"{SCHEMA_PROMPT}"
                 "The conversation history is provided. Use it to resolve any pronouns or references (e.g. 'their', 'its', 'the same one')."
                 "Generate a valid Cypher query for this intent. Return ONLY the Cypher query.")


SYNTHESIZER_PROMPT = ("You're a Neo4j knowledge graph expert and excellent at generating natural, human-friendly responses. "
                    "Given a user's question and the query result, respond in a clear and concise way that answers the question. "
                    "Phrase the answer in a business-friendly, natural sentence using the entities mentioned in the question. "
                    "Do NOT mention queries, databases, or how the result was obtained. "
                    "Avoid technical language like 'returned by the query' or 'aggregated result'. "
                    "If the result is a number, clearly state what it represents in context. ")


REPLAN_PROMPT = ("You are a Cypher expert. Fix the given query based on the error."
                 "Return ONLY the corrected Cypher query. You must consider the user's intent (ADD, UPDATE, INQUIRE, DELETE)."
                 "For ADD: confirm creation, For INQUIRE: answer the question, For UPDATE: confirm changes, For DELETE: confirm deletion"
                 "If no results: Explain it based on the intent, not as a generic database failure")




