import os
from flask import Flask, render_template, request, jsonify
from rag import RAGPipeline
import auth_db

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
    {"id": 8, "name": "Charge 20K Power Bank", "cat": "Accessories", "price": 1299, "old": 1899, "rating": "4.2", "img": "https://images.unsplash.com/photo-1609091839311-d5365f9ff1c5?auto=format&fit=crop&w=800&q=85"},
    {"id": 9, "name": "Studio Pro ANC Headphones", "cat": "Audio", "price": 4999, "old": 6999, "rating": "4.8", "img": "https://images.unsplash.com/photo-1546435770-a3e426bf472b?auto=format&fit=crop&w=800&q=85"},
    {"id": 10, "name": "Retro Vinyl Bluetooth Turntable", "cat": "Audio", "price": 5499, "old": 7299, "rating": "4.7", "img": "https://images.unsplash.com/photo-1545454675-3531b543be5d?auto=format&fit=crop&w=800&q=85"},
    {"id": 11, "name": "Lumen AMOLED Fitness Band", "cat": "Wearables", "price": 1999, "old": 2999, "rating": "4.5", "img": "https://images.unsplash.com/photo-1575311373937-040b8e1fd5b6?auto=format&fit=crop&w=800&q=85"},
    {"id": 12, "name": "Horizon Titanium Smart Ring", "cat": "Wearables", "price": 6499, "old": 8999, "rating": "4.9", "img": "https://images.unsplash.com/photo-1603561591411-07134e71a2a9?auto=format&fit=crop&w=800&q=85"},
    {"id": 13, "name": "Pocket 4K Vlog Gimbal Cam", "cat": "Cameras", "price": 14299, "old": 17999, "rating": "4.8", "img": "https://images.unsplash.com/photo-1502920917128-1aa500764cbd?auto=format&fit=crop&w=800&q=85"},
    {"id": 14, "name": "Retro Instant Film Camera", "cat": "Cameras", "price": 3799, "old": 4999, "rating": "4.6", "img": "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?auto=format&fit=crop&w=800&q=85"},
    {"id": 15, "name": "Glow Sunrise Alarm & Lamp", "cat": "Smart devices", "price": 2899, "old": 3999, "rating": "4.7", "img": "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?auto=format&fit=crop&w=800&q=85"},
    {"id": 16, "name": "Nova 3-in-1 MagSafe Stand", "cat": "Smart devices", "price": 2199, "old": 3199, "rating": "4.6", "img": "https://images.unsplash.com/photo-1583863788434-e58a36330cf0?auto=format&fit=crop&w=800&q=85"}
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

    # If user is authenticated, save chat exchange to user history
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "").strip() or body.get("user_token", "")
    user = auth_db.get_user_by_token(token)
    if user:
        auth_db.add_chat_history_for_user(user["email"], {"message": msg, "reply": result["reply"]})

    return jsonify(
        reply=result["reply"],
        sources=result["sources"],
        retrieval_mode=result.get("retrieval_mode", "Vector Search"),
        generator=result.get("generator", "Groq LLM")
    )

# --- USER AUTHENTICATION & PROFILE ENDPOINTS ---

@app.route("/api/auth/register", methods=["POST"])
def api_register():
    body = request.json or {}
    res, err = auth_db.register_user(
        body.get("name", ""),
        body.get("email", ""),
        body.get("password", "")
    )
    if err:
        return jsonify(status="error", message=err), 400
    return jsonify(status="ok", token=res["token"], user=res["user"])

@app.route("/api/auth/login", methods=["POST"])
def api_login():
    body = request.json or {}
    res, err = auth_db.authenticate_user(
        body.get("email", ""),
        body.get("password", "")
    )
    if err:
        return jsonify(status="error", message=err), 401
    return jsonify(status="ok", token=res["token"], user=res["user"])

@app.route("/api/auth/me", methods=["GET"])
def api_me():
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "").strip()
    user = auth_db.get_user_by_token(token)
    if not user:
        return jsonify(status="error", message="Not authenticated"), 401
    return jsonify(status="ok", user=auth_db.get_public_user(user))

@app.route("/api/auth/logout", methods=["POST"])
def api_logout():
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "").strip()
    auth_db.logout_token(token)
    return jsonify(status="ok")

@app.route("/api/user/cards", methods=["POST"])
def api_add_card():
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "").strip()
    user = auth_db.get_user_by_token(token)
    if not user:
        return jsonify(status="error", message="Not authenticated"), 401
    body = request.json or {}
    cards, err = auth_db.add_card_for_user(user["email"], body)
    if err:
        return jsonify(status="error", message=err), 400
    return jsonify(status="ok", cards=cards)

@app.route("/api/user/cards/<card_id>", methods=["DELETE"])
def api_delete_card(card_id):
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "").strip()
    user = auth_db.get_user_by_token(token)
    if not user:
        return jsonify(status="error", message="Not authenticated"), 401
    cards, err = auth_db.delete_card_for_user(user["email"], card_id)
    return jsonify(status="ok", cards=cards)

@app.route("/api/user/orders", methods=["POST"])
def api_place_order():
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "").strip()
    user = auth_db.get_user_by_token(token)
    if not user:
        return jsonify(status="error", message="Not authenticated"), 401
    body = request.json or {}
    order, err = auth_db.add_order_for_user(user["email"], body)
    if err:
        return jsonify(status="error", message=err), 400
    return jsonify(status="ok", order=order, orders=user.get("orders", []))

@app.route("/api/user/history", methods=["GET"])
def api_user_history():
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "").strip()
    user = auth_db.get_user_by_token(token)
    if not user:
        return jsonify(status="error", message="Not authenticated"), 401
    return jsonify(status="ok", orders=user.get("orders", []), chat_history=user.get("chat_history", []))

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
