from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from database import init_db, generate_mock_data
from graph_builder import build_graph, get_graph_data
from query_engine import execute_query
from models import GraphData, QueryRequest, QueryResponse

app = FastAPI(title="Graph-Based LLM Query API")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DB on Startup
@app.on_event("startup")
def startup_event():
    init_db()
    generate_mock_data()
    print("Database initialized and mock data generated.")

@app.get("/graph", response_model=GraphData)
def get_graph():
    """Returns nodes and edges for Cytoscape.js visualization."""
    try:
        G = build_graph()
        return get_graph_data(G)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/node/{id}")
def get_node_metadata(id: str):
    """Returns metadata for a specific Node."""
    try:
        G = build_graph()
        if id not in G.nodes:
            raise HTTPException(status_code=404, detail="Node not found")
        data = G.nodes[id]
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=QueryResponse)
def query_graph(request: QueryRequest):
    """Accepts natural language query and returns SQL results & insights."""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
        
    try:
        result = execute_query(request.query)
        if result["sql_query"] is None and "only answers dataset-related queries" in result["natural_response"]:
             return dict(
                 natural_response=result["natural_response"],
                 sql_query=result["sql_query"],
                 structured_data=result["structured_data"],
                 affected_nodes=result.get("affected_nodes")
             )
        return dict(
            natural_response=result["natural_response"],
            sql_query=result["sql_query"],
            structured_data=result["structured_data"],
            affected_nodes=result.get("affected_nodes")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
