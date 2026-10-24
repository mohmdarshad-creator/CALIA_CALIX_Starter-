# CALIA × CALIX AI (with RAG Pipeline & Groq LLM)

## Run it
1. Install Python 3.9 or newer.
2. Open terminal in this folder and install dependencies:
   ```bash
   python3 -m pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python3 app.py
   ```
4. Open [http://127.0.0.1:5001](http://127.0.0.1:5001) in your browser (automatically falls back to 5001 if port 5000 is occupied by macOS AirPlay).

## RAG & Groq LLM Architecture
CALIX is powered by an active RAG (Retrieval-Augmented Generation) pipeline integrated with **Groq LLM**:
- **Groq AI Generation**: Uses high-speed inference via `openai/gpt-oss-120b` (and `openai/gpt-oss-20b`) to answer open-ended questions conversationally.
- **Customer Support Persona**: Tuned specifically for CALIA retail shoppers with warm, polite, and helpful customer-care responses.
- **Strict Guardrails**: Politely declines any requests for code, programming, scripts, or non-shopping tasks while staying in character.
- **Knowledge Base (`knowledge/`)**:
  - `knowledge/products.json`: Detailed specifications, pricing, ratings, battery, dimensions, and box contents.
  - `knowledge/policies.json`: Shipping timelines, 7-day returns, damaged goods protocol, billing duplicate charge escalation to specialist Maya, and 1-year warranty guidelines.
- **Context Injection & Provenance**: Top retrieved knowledge chunks are injected into the LLM prompt and cited below every response in the chat UI.
- **API Status**: `GET /rag/status` reports active LLM, guardrail status, and indexed knowledge sources.

## Features
- Full Theme Customization: Light Mode ☀️, Dark Mode 🌙, and System Default 💻 with instant zero-flash switching.
- Add-to-cart flying item arc and spring bounce animations.
- Pastel storefront with product catalog and category filters.
- Add-to-cart drawer with subtotal calculations.
- CALIX AI Chatbot with live RAG source inspection and Groq LLM integration.
- Speech recognition and voice synthesis in supported browsers.
- Simulated workflows for damaged goods and duplicate charges.
