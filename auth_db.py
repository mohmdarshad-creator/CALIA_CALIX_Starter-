import json
import os
import secrets
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
USERS_FILE = os.path.join(DATA_DIR, "users.json")

# In-memory caches for fast reads
_USERS_CACHE = {}
_SESSIONS = {}  # token -> email

def _ensure_data_file():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(USERS_FILE):
        seed_users = {
            "demo@calia.tech": {
                "id": "usr_demo",
                "name": "Mohamed Arshad",
                "email": "demo@calia.tech",
                "password_hash": generate_password_hash("password123", method="pbkdf2:sha256"),
                "created_at": "2026-10-24T12:00:00Z",
                "tier": "✦ CALIA VIP Member",
                "cards": [
                    {
                        "id": "crd_1",
                        "brand": "Visa",
                        "last4": "4242",
                        "number_masked": "•••• •••• •••• 4242",
                        "exp": "12/28",
                        "holder": "Mohamed Arshad",
                        "is_default": True
                    },
                    {
                        "id": "crd_2",
                        "brand": "Mastercard",
                        "last4": "8899",
                        "number_masked": "•••• •••• •••• 8899",
                        "exp": "09/27",
                        "holder": "Mohamed Arshad",
                        "is_default": False
                    }
                ],
                "orders": [
                    {
                        "id": "CALIA-8921",
                        "date": "22 Oct 2026",
                        "items": [
                            {"name": "Aura Wireless Headphones", "qty": 1, "price": 2499, "img": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=400&q=80"}
                        ],
                        "total": 2499,
                        "card_last4": "4242",
                        "status": "Delivered"
                    },
                    {
                        "id": "CALIA-7430",
                        "date": "15 Oct 2026",
                        "items": [
                            {"name": "Orbit Mini Speaker", "qty": 1, "price": 1499, "img": "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?auto=format&fit=crop&w=400&q=80"}
                        ],
                        "total": 1499,
                        "card_last4": "8899",
                        "status": "Delivered"
                    }
                ],
                "chat_history": [
                    {
                        "id": "chat_1",
                        "timestamp": "2026-10-24 16:30",
                        "message": "Do you have any wireless headphones under ₹3,000?",
                        "reply": "Yes! The Aura Wireless Headphones are priced at ₹2,499 with 40h battery life and active noise cancellation."
                    }
                ]
            }
        }
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump({"users": seed_users}, f, indent=2)

def _load_users():
    global _USERS_CACHE
    _ensure_data_file()
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            _USERS_CACHE = data.get("users", {})
    except Exception as e:
        print(f"Error loading users file: {e}")
        _USERS_CACHE = {}
    return _USERS_CACHE

def _save_users():
    global _USERS_CACHE
    _ensure_data_file()
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump({"users": _USERS_CACHE}, f, indent=2)
    except Exception as e:
        print(f"Error saving users file: {e}")

# Initialize cache at import time
_load_users()

def get_public_user(user):
    if not user:
        return None
    return {
        "id": user.get("id"),
        "name": user.get("name"),
        "email": user.get("email"),
        "tier": user.get("tier", "✦ Calia Member"),
        "created_at": user.get("created_at"),
        "cards": user.get("cards", []),
        "orders": user.get("orders", []),
        "chat_history": user.get("chat_history", [])
    }

def get_user_by_email(email):
    _load_users()
    return _USERS_CACHE.get(email.strip().lower())

def get_user_by_token(token):
    if not token:
        return None
    email = _SESSIONS.get(token)
    if not email:
        return None
    return get_user_by_email(email)

def register_user(name, email, password):
    email = email.strip().lower()
    name = name.strip()
    if not email or "@" not in email:
        return None, "Invalid email address"
    if not name:
        return None, "Name is required"
    if not password or len(password) < 6:
        return None, "Password must be at least 6 characters"

    _load_users()
    if email in _USERS_CACHE:
        return None, "An account with this email already exists"

    user_id = f"usr_{secrets.token_hex(6)}"
    new_user = {
        "id": user_id,
        "name": name,
        "email": email,
        "password_hash": generate_password_hash(password, method="pbkdf2:sha256"),
        "created_at": datetime.utcnow().isoformat() + "Z",
        "tier": "✦ CALIA Member",
        "cards": [],
        "orders": [],
        "chat_history": []
    }
    _USERS_CACHE[email] = new_user
    _save_users()

    token = secrets.token_hex(24)
    _SESSIONS[token] = email
    return {"token": token, "user": get_public_user(new_user)}, None

def authenticate_user(email, password):
    email = email.strip().lower()
    _load_users()
    user = _USERS_CACHE.get(email)
    if not user:
        return None, "Account not found with this email"
    if not check_password_hash(user.get("password_hash", ""), password):
        return None, "Incorrect password"

    token = secrets.token_hex(24)
    _SESSIONS[token] = email
    return {"token": token, "user": get_public_user(user)}, None

def logout_token(token):
    if token in _SESSIONS:
        del _SESSIONS[token]
    return True

def add_card_for_user(email, card_data):
    user = get_user_by_email(email)
    if not user:
        return None, "User not found"

    number = card_data.get("number", "").replace(" ", "").replace("-", "")
    if len(number) < 12:
        return None, "Card number must be at least 12 digits"

    last4 = number[-4:]
    holder = card_data.get("holder", "").strip() or user.get("name")
    exp = card_data.get("exp", "").strip()
    brand = card_data.get("brand", "Visa")

    # Detect brand if not provided
    if number.startswith("4"):
        brand = "Visa"
    elif number.startswith(("51", "52", "53", "54", "55")):
        brand = "Mastercard"
    elif number.startswith(("34", "37")):
        brand = "American Express"
    elif number.startswith("6"):
        brand = "RuPay"

    card_id = f"crd_{secrets.token_hex(4)}"
    cards = user.setdefault("cards", [])
    is_default = len(cards) == 0 or card_data.get("is_default", False)

    if is_default:
        for c in cards:
            c["is_default"] = False

    new_card = {
        "id": card_id,
        "brand": brand,
        "last4": last4,
        "number_masked": f"•••• •••• •••• {last4}",
        "exp": exp or "12/29",
        "holder": holder,
        "is_default": is_default
    }
    cards.append(new_card)
    _save_users()
    return cards, None

def delete_card_for_user(email, card_id):
    user = get_user_by_email(email)
    if not user:
        return None, "User not found"
    cards = user.get("cards", [])
    user["cards"] = [c for c in cards if c["id"] != card_id]
    if user["cards"] and not any(c.get("is_default") for c in user["cards"]):
        user["cards"][0]["is_default"] = True
    _save_users()
    return user["cards"], None

def add_order_for_user(email, order_data):
    user = get_user_by_email(email)
    if not user:
        return None, "User not found"

    items = order_data.get("items", [])
    total = order_data.get("total", 0)
    card_last4 = order_data.get("card_last4", "4242")

    order_id = f"CALIA-{secrets.randbelow(9000) + 1000}"
    date_str = datetime.now().strftime("%d %b %Y, %I:%M %p")

    new_order = {
        "id": order_id,
        "date": date_str,
        "items": items,
        "total": total,
        "card_last4": card_last4,
        "status": "Order Placed (In Transit 🚚)"
    }
    user.setdefault("orders", []).insert(0, new_order)
    _save_users()
    return new_order, None

def add_chat_history_for_user(email, chat_entry):
    user = get_user_by_email(email)
    if not user:
        return False
    entry = {
        "id": f"chat_{secrets.token_hex(4)}",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "message": chat_entry.get("message", ""),
        "reply": chat_entry.get("reply", "")
    }
    user.setdefault("chat_history", []).append(entry)
    # keep last 50
    user["chat_history"] = user["chat_history"][-50:]
    _save_users()
    return True
