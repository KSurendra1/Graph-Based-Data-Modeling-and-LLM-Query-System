# Graph-Based Data Modeling and LLM Query System

This project is a powerful context-graph generation and querying platform. It automatically ingests structured business data (Order-to-Cash process from SAP) into an SQLite database, transforms it into a highly interactive NetworkX dependency graph, and allows users to query entire business flows using Natural Language powered by the **Groq API**.

![Groq Powered](https://img.shields.io/badge/LLM-Groq%20Llama%203.3-orange)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)
![React](https://img.shields.io/badge/Frontend-React%2BVite-61DAFB)

## Features
- **Data Ingestion Engine**: Dynamically parses nested JSONL files (`sap-o2c-data`) including Sales Orders, Deliveries, Invoices, Payments, and Customers.
- **Graph Transformation**: Automatically builds semantic edges across disconnected datasets (e.g. Sales Order -> Delivery -> Invoice -> Payment).
- **LLM Text-to-SQL Engine**: Integrates **Groq (llama-3.3-70b-versatile)** to securely translate natural language into complex multi-table SQL joins, returning exact schema-aligned responses.
- **Interactive Visualizer**: Modern, lightweight Cytoscape.js frontend to visualize the data flow mapping and interact with entities in real-time. Nodes intelligently highlight based on chat queries!
- **Strict Guardrails**: Refuses to answer out-of-domain questions to ensure business relevance operations (e.g. rejects "What is a recipe for cookies?").

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- **Python 3.9+**
- **Node.js 18+ (Node 20+ Recommended)**
- **Groq API Key**: Get one free at [console.groq.com](https://console.groq.com/)

### 2. Backend Setup
The backend runs on Python/FastAPI. It will construct the SQLite database and the graph automatically upon execution.

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a Virtual Environment (Recommended):
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Mac/Linux:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   
4. Configure your API key:
   Ensure the `.env` file exists in the `backend/` folder:
   ```env
   GROQ_API_KEY=gsk_your_groq_api_key_here
   ```
5. Start the API Server:
   ```bash
   uvicorn main:app --port 8000
   ```
   *The server will take ~5 seconds on first boot to digest the real dataset JSONL files into the local database.*

### 3. Frontend Setup
The frontend runs on React & Vite, utilizing Tailwind CSS.

1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the Vite Development Server:
   ```bash
   npm run dev
   ```
4. Open your browser to the URL displayed (usually **http://localhost:5173**).

---

## 🧠 System Architecture & Design Decisions

### 1. Database Choice: SQLite
We chose **SQLite** as the primary backend database rather than a heavy graph database like Neo4j. 
- **Reasoning**: The assignment specifically evaluates the ability to map disconnected datasets. By parsing the `sap-o2c-data` JSONL records directly into relational SQLite tables, we prove that we can bridge disparate structured data programmatically. SQLite is lightweight, fast, requires zero configuration, and serves as the perfect structured SQL sandbox for the Groq LLM to safely generate standard ANSI SQL queries against.

### 2. Architecture Decisions: Separation of Concerns
The system utilizes a clean microservice-style split:
- **FastAPI Backend**: Acts as the orchestrator. Contains independent modules for Database ingestion (`database.py`), LLM interfacing (`llm_service.py`), SQL Execution (`query_engine.py`), and Graph Transformation (`graph_builder.py`).
- **Graph Engine (NetworkX)**: Reads the SQLite rows on startup and explicitly maps the isolated tables into connected semantic nodes (`Sales Order -> Delivery -> Invoice`). It then exports a clean JSON structure formatted exactly for Cytoscape.js.
- **Split-Pane Frontend (React)**: Implements an interactive Cytoscape.js canvas running concurrently alongside a chat interface. We explicitly designed the frontend to capture node highlighting (`affected_nodes`) natively from the LLM response, allowing users to physically "see" the data their query isolated.

### 3. LLM Prompting Strategy
The platform utilizes **Groq's `llama-3.3-70b-versatile`** through a highly tuned System Instruction Prompt.
- **Zero-Shot Schema Injection**: The system prompt rigidly defines the exact table schema, columns, and foreign key relationships of the SQLite database.
- **Alias Enforcement**: The prompt strictly instructs the LLM to use proper Table Aliases in all `JOIN` and `FROM` clauses to prevent `OperationalError: ambiguous column` exceptions during complex 6-table joins tracking documents from Order to Payment.
- **Regex Extraction**: Because LLMs are prone to "chatting" (e.g. outputting "Here is your SQL:" alongside the code), the `llm_service.py` runs a robust Regular Expression to surgically extract ONLY the valid SQLite syntax enclosed in the ` ```sql ... ``` ` blocks, guaranteeing parse safety.

### 4. Guardrails & Safety
Enterprise AI systems must only answer queries within their domain boundaries. 
- **Prompt Isolation**: We enforce a hard guardrail within the System Prompt explicitly stating: *"If the query is NOT related to the order-to-cash process (orders, deliveries, invoices, payments, customers, products), you MUST return exactly the literal string: 'This system only answers dataset-related queries.'"*
- **Execution Defense**: If the LLM generates a non-SQL conversational response anyway (e.g. failing the regex extraction), the `query_engine.py` will catch the empty/invalid format and safely return the static rejection text instead of crashing the database.
