from database import engine
from sqlalchemy import text
from llm_service import generate_sql_from_text, format_natural_response

def execute_query(user_query: str) -> dict:
    # 1. Convert Natural Language to SQL
    try:
        sql_query = generate_sql_from_text(user_query)
    except Exception as e:
        return {
            "natural_response": f"Failed to generate SQL: {str(e)}",
            "sql_query": None,
            "structured_data": None
        }
        
    # Check guardrails
    if "This system only answers dataset-related queries." in sql_query:
        return {
            "natural_response": "This system only answers dataset-related queries.",
            "sql_query": None,
            "structured_data": None
        }

    # 2. Execute SQL
    try:
        with engine.connect() as connection:
            result = connection.execute(text(sql_query))
            keys = result.keys()
            data = [dict(zip(keys, row)) for row in result.fetchall()]
    except Exception as e:
        return {
            "natural_response": f"Error executing query: {str(e)}",
            "sql_query": sql_query,
            "structured_data": None
        }
        
    # 3. Format Natural Response
    try:
        natural_response = format_natural_response(user_query, sql_query, data)
    except Exception as e:
        natural_response = "Generated SQL successfully, but failed to format natural language response due to an LLM error."
        
    return {
        "natural_response": natural_response,
        "sql_query": sql_query,
        "structured_data": data,
        "affected_nodes": _extract_node_ids(data)
    }

def _extract_node_ids(data: list) -> list:
    """Guess node IDs in results to highlight them on the graph."""
    nodes = set()
    for row in data:
        for key, value in row.items():
            if not value: 
                continue
                
            val_str = str(value)
            k = str(key).lower()
            
            # Based on the new real schema IDs
            if 'salesorder' in k or k == 'order_num':
                nodes.add(f"SO_{val_str}")
            elif 'billingdocument' in k or k == 'billing':
                nodes.add(f"BD_{val_str}")
            elif 'deliverydocument' in k or k == 'delivery':
                nodes.add(f"OD_{val_str}")
            elif 'journalentry' in k or k == 'accountingdocument' or k == 'reference_je':
                # Since payments also use accountingDocument, and JEs use it:
                # We add both to be safe, Cytoscape ignores missing IDs
                nodes.add(f"JE_{val_str}")
                nodes.add(f"PAY_{val_str}")
            elif 'businesspartner' in k or 'soldtoparty' in k:
                nodes.add(f"BP_{val_str}")
            elif 'product' in k or 'material' in k:
                nodes.add(f"PR_{val_str}")
            elif 'plant' in k:
                nodes.add(f"PL_{val_str}")
                
    return list(nodes)
