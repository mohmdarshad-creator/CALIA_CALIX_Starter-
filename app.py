import os
from flask import Flask, render_template, request, jsonify
from rag import RAGPipeline

app = Flask(__name__)
rag_pipeline = RAGPipeline()

PRODUCTS = [
    {"id": 1, "name": "Aura Wireless Headphones", "cat": "Audio", "price": 2499, "old": 3499, "rating": "4.6", "img": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=800&q=85"},
    {"id": 2, "name": "Pulse Smart Watch", "cat": "Wearables", "price": 3299, "old": 4999, "rating": "4.4", "img": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=800&q=85"},
    {"id": 3, "name": "Nova Wireless Earbuds", "cat": "Audio", "price": 1799, "old": 2599, "rating": "4.5", "img": "https://images.unsplash.com/photo-1606220945770-b5b6c2c55bf1?auto=format&fit=crop&w=800&q=85"},
    {"id": 4, "name": "Orbit Mini Speaker", "cat": "Audio", "price": 1499, "old": 2199, "rating": "4.3", "img": "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?auto=format&fit=crop&w=800&q=85"},
    {"id": 5, "name": "Snap Compact Camera", "cat": "Cameras", "price": 8999, "old": 10999, "rating": "4.7", "img": "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?auto=format&fit=crop&w=800&q=85"},
    {"id": 6, "name": "Flex Tablet", "cat": "Smart devices", "price": 12499, "old": 14999, "rating": "4.5", "img": "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?auto=format&fit=crop&w=800&q=85"},
    {"id": 7, "name": "Click Mechanical Keyboard", "cat": "Accessories", "price": 2899, "old": 3799, "rating": "4.6", "img": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?auto=format&fit=crop&w=800&q=85"},
    {"id": 8, "name": "Charge 20K Power Bank", "cat": "Accessories", "price": 1299, "old": 1899, "rating": "4.2", "img": "https://images.unsplash.com/photo-1609091839311-d5365f9ff1c5?auto=format&fit=crop&w=800&q=85"}
]

@app.route("/")
def home():
    return render_template("index.html", products=PRODUCTS)

@app.route("/chat", methods=["POST"])
def chat():
    body = request.json or {}
    msg = body.get("message", "").strip()
    api_key = body.get("api_key", "").strip() or request.headers.get("X-API-Key", "").strip() or os.getenv("GROQ_API_KEY", "").strip() or os.getenv("GEMINI_API_KEY", "").strip()
    if not msg:
        return jsonify(reply="Please type a question or product inquiry!", sources=[])
    result = rag_pipeline.generate_response(msg, api_key=api_key)
    return jsonify(
        reply=result["reply"],
        sources=result["sources"],
        retrieval_mode=result.get("retrieval_mode", "Vector Search"),
        generator=result.get("generator", "Groq LLM")
    )

@app.route("/rag/status", methods=["GET"])
def rag_status():
    return jsonify(
        status="active",
        chunks_indexed=len(rag_pipeline.chunks),
        llm="Groq (openai/gpt-oss-120b)",
        guardrails="Active (Customer support persona + Code refusal)",
        knowledge_sources=[c.get("title") for c in rag_pipeline.chunks]
    )
if __name__=="__main__":
    import socket
    port = int(os.getenv("PORT", 0))
    if not port:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', 5000))
                port = 5000
        except OSError:
            port = 5001
    print(f" * CALIA frontend running on http://127.0.0.1:{port}")
    app.run(debug=True, host="127.0.0.1", port=port)
