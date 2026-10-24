const $ = id => document.getElementById(id);
let cart = {};
let speakOn = localStorage.getItem("calia_voice") === "true";
let currentUser = null;
let currentToken = localStorage.getItem("calia_auth_token") || "";

// Products list extracted from DOM
const items = [...document.querySelectorAll(".card")].map(c => ({
    id: +c.querySelector(".add").dataset.id,
    name: c.querySelector(".add").dataset.name,
    price: +c.querySelector(".add").dataset.price,
    img: c.querySelector("img").src
}));

let toastTimer;
function toast(t) {
    const el = $("toast");
    if (!el) return;
    el.textContent = t;
    el.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => el.classList.remove("show"), 2400);
}

// Drawer Controller
function overlay(which) {
    $("shade").classList.add("show");
    $(which).classList.add("open");
}
function closeAllDrawers() {
    ["cart", "chat", "userDrawer"].forEach(x => {
        const el = $(x);
        if (el) el.classList.remove("open");
    });
    $("shade").classList.remove("show");
}

$("shade").onclick = closeAllDrawers;
$("openCart").onclick = () => overlay("cart");
$("closeCart").onclick = closeAllDrawers;
$("closeChat").onclick = closeAllDrawers;
if ($("closeUser")) $("closeUser").onclick = closeAllDrawers;
if ($("openUser")) $("openUser").onclick = () => { overlay("userDrawer"); renderUserDrawer(); };

// Floating Action Button for CALIX AI Chatbot
if ($("floatingChatBtn")) $("floatingChatBtn").onclick = () => overlay("chat");
if ($("openChat2")) $("openChat2").onclick = () => overlay("chat");

// Cart rendering
function renderCart() {
    let n = Object.values(cart).reduce((a, b) => a + b, 0);
    $("count").textContent = n;
    $("cartCount").textContent = n;
    let total = 0;
    let html = "";
    for (let id in cart) {
        let p = items.find(x => x.id == id);
        if (p) {
            total += p.price * cart[id];
            html += `<div class="cartrow">
                <img src="${p.img}" alt="${p.name}">
                <div>
                    <b>${p.name}</b>
                    <small style="color:var(--muted)">₹${p.price.toLocaleString("en-IN")} × ${cart[id]}</small>
                </div>
                <span>₹${(p.price * cart[id]).toLocaleString("en-IN")}</span>
                <button data-remove="${id}" title="Remove item">×</button>
            </div>`;
        }
    }
    $("cartItems").innerHTML = html || "Your cart is waiting for something lovely ♡";
    $("total").textContent = "₹" + total.toLocaleString("en-IN");
}

function spawnSparkles(btn) {
    const rect = btn.getBoundingClientRect();
    const symbols = ["✦", "♡", "✧", "₊˚"];
    for (let i = 0; i < 4; i++) {
        const span = document.createElement("span");
        span.className = "sparkle-particle";
        span.textContent = symbols[i % symbols.length];
        span.style.left = `${rect.left + rect.width / 2 + (Math.random() * 40 - 20)}px`;
        span.style.top = `${rect.top + (Math.random() * 10 - 5)}px`;
        span.style.setProperty("--dx", `${(Math.random() - 0.5) * 60}px`);
        span.style.setProperty("--dy", `${-35 - Math.random() * 30}px`);
        document.body.appendChild(span);
        setTimeout(() => span.remove(), 750);
    }
}

function flyToCart(imgElement, cartBtnElement, onLand) {
    if (!imgElement || !cartBtnElement) { if (onLand) onLand(); return; }
    const imgRect = imgElement.getBoundingClientRect();
    const cartRect = cartBtnElement.getBoundingClientRect();
    const flyer = document.createElement("img");
    flyer.src = imgElement.src;
    flyer.className = "flying-cart-item";
    flyer.style.top = `${imgRect.top}px`;
    flyer.style.left = `${imgRect.left}px`;
    flyer.style.width = `${imgRect.width}px`;
    flyer.style.height = `${imgRect.height}px`;
    document.body.appendChild(flyer);
    void flyer.offsetWidth;

    const targetX = cartRect.left + cartRect.width / 2 - 16;
    const targetY = cartRect.top + cartRect.height / 2 - 16;
    flyer.style.top = `${targetY}px`;
    flyer.style.left = `${targetX}px`;
    flyer.style.width = "32px";
    flyer.style.height = "32px";
    flyer.style.opacity = "0.25";
    flyer.style.transform = "rotate(25deg) scale(0.6)";

    setTimeout(() => {
        flyer.remove();
        if (onLand) onLand();
        cartBtnElement.classList.remove("cart-bump");
        void cartBtnElement.offsetWidth;
        cartBtnElement.classList.add("cart-bump");
    }, 650);
}

document.querySelectorAll(".add").forEach(b => {
    b.onclick = () => {
        const id = b.dataset.id;
        const card = b.closest(".card");
        const img = card ? card.querySelector(".photo img") : null;
        const cartBtn = $("openCart");
        b.classList.add("btn-added");
        const origContent = b.innerHTML;
        b.innerHTML = `Added! <b style="font-size:13px">✓</b>`;
        spawnSparkles(b);
        setTimeout(() => {
            b.classList.remove("btn-added");
            b.innerHTML = origContent;
        }, 900);
        flyToCart(img, cartBtn, () => {
            cart[id] = (cart[id] || 0) + 1;
            renderCart();
            toast("Added to cart ♡");
        });
    };
});

$("cartItems").onclick = e => {
    if (e.target.dataset.remove) {
        delete cart[e.target.dataset.remove];
        renderCart();
    }
};

// Checkout tied to user account & saved card
$("checkout").onclick = async () => {
    const totalItems = Object.values(cart).reduce((a, b) => a + b, 0);
    if (totalItems === 0) {
        toast("Your cart is empty! Add a gadget first ♡");
        return;
    }

    if (!currentUser) {
        toast("Please sign in or use Demo Login to place your order! ♡");
        overlay("userDrawer");
        renderUserDrawer();
        return;
    }

    const cards = currentUser.cards || [];
    if (cards.length === 0) {
        toast("Please add a card to your account to complete checkout! 💳");
        overlay("userDrawer");
        renderUserDrawer("cards");
        return;
    }

    const defaultCard = cards.find(c => c.is_default) || cards[0];
    let cartList = [];
    let grandTotal = 0;
    for (let id in cart) {
        let p = items.find(x => x.id == id);
        if (p) {
            cartList.push({ name: p.name, qty: cart[id], price: p.price, img: p.img });
            grandTotal += p.price * cart[id];
        }
    }

    try {
        const res = await fetch("/api/user/orders", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${currentToken}`
            },
            body: JSON.stringify({
                items: cartList,
                total: grandTotal,
                card_last4: defaultCard.last4
            })
        });
        const data = await res.json();
        if (data.status === "ok") {
            cart = {};
            renderCart();
            currentUser.orders = data.orders;
            localStorage.setItem("calia_user_data", JSON.stringify(currentUser));
            closeAllDrawers();
            toast(`Order #${data.order.id} placed with ${defaultCard.brand} •••• ${defaultCard.last4}! 💳📦`);
            setTimeout(() => {
                overlay("userDrawer");
                renderUserDrawer("orders");
            }, 600);
        } else {
            toast(data.message || "Could not place order");
        }
    } catch (err) {
        toast("Error placing order. Please try again.");
    }
};

document.querySelectorAll(".heart").forEach(b => b.onclick = () => {
    b.textContent = b.textContent === "♡" ? "♥" : "♡";
    toast("Favourites updated ♡");
});

document.querySelectorAll(".cats button").forEach(b => b.onclick = () => {
    document.querySelectorAll(".cats button").forEach(x => x.classList.remove("selected"));
    b.classList.add("selected");
    document.querySelectorAll(".card").forEach(c => c.style.display = b.dataset.cat === "All" || c.dataset.cat === b.dataset.cat ? "" : "none");
});

$("search").oninput = e => {
    let q = e.target.value.toLowerCase();
    document.querySelectorAll(".card").forEach(c => c.style.display = c.dataset.name.includes(q) || c.dataset.cat.toLowerCase().includes(q) ? "" : "none");
};

// CALIX Chat Support
function addMessage(text, who, sources, retrievalMode) {
    let d = document.createElement("div");
    d.className = "msg " + who;
    let t = document.createElement("div");
    t.textContent = text;
    d.append(t);
    if (who === "bot" && sources && sources.length > 0) {
        let badge = document.createElement("div");
        badge.className = "rag-badge";
        let itemsHtml = sources.map(s => `<div class="rag-item"><b>${s.title}</b> <span class="rag-cat">${s.category || "Knowledge"}</span><p>${s.snippet || ""}</p></div>`).join("");
        badge.innerHTML = `<div class="rag-header"><span class="rag-pill">📚 RAG Grounded</span><span class="rag-mode">${retrievalMode || "Vector Index"}</span></div><details class="rag-sources"><summary>View ${sources.length} retrieved source${sources.length > 1 ? "s" : ""} ▾</summary><div class="rag-list">${itemsHtml}</div></details>`;
        d.append(badge);
    }
    $("messages").append(d);
    $("messages").scrollTop = $("messages").scrollHeight;
}

function speak(t) {
    if (speakOn && "speechSynthesis" in window) {
        speechSynthesis.cancel();
        let u = new SpeechSynthesisUtterance(t);
        u.lang = "en-IN";
        speechSynthesis.speak(u);
    }
}

async function send(text) {
    text = (text || $("input").value).trim();
    if (!text) return;
    $("input").value = "";
    addMessage(text, "user");
    $("send").disabled = true;
    let apiKey = localStorage.getItem("calia_api_key") || "";

    const headers = { "Content-Type": "application/json" };
    if (currentToken) {
        headers["Authorization"] = `Bearer ${currentToken}`;
    }

    try {
        let r = await fetch("/chat", {
            method: "POST",
            headers: headers,
            body: JSON.stringify({ message: text, api_key: apiKey, user_token: currentToken })
        });
        let d = await r.json();
        addMessage(d.reply, "bot", d.sources, d.retrieval_mode);
        speak(d.reply);

        // Append to local user chat history if logged in
        if (currentUser) {
            currentUser.chat_history = currentUser.chat_history || [];
            currentUser.chat_history.push({
                id: "chat_" + Date.now(),
                timestamp: new Date().toLocaleString(),
                message: text,
                reply: d.reply
            });
            localStorage.setItem("calia_user_data", JSON.stringify(currentUser));
        }
    } catch (e) {
        addMessage("I couldn't connect just now. Please try again.", "bot");
    } finally {
        $("send").disabled = false;
    }
}

$("send").onclick = () => send();
$("input").onkeydown = e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } };
document.querySelectorAll(".quick").forEach(b => b.onclick = () => send(b.textContent));

// Voice Replies Toggle
function updateVoiceUI() {
    if ($("voiceToggle")) $("voiceToggle").textContent = speakOn ? "🔊" : "🔇";
    if ($("voiceToggleSetting")) $("voiceToggleSetting").textContent = speakOn ? "🔊 On" : "🔇 Off";
}
updateVoiceUI();

if ($("voiceToggle")) {
    $("voiceToggle").onclick = () => {
        speakOn = !speakOn;
        localStorage.setItem("calia_voice", speakOn ? "true" : "false");
        updateVoiceUI();
        toast(speakOn ? "Voice replies on 🔊" : "Voice replies off 🔇");
    };
}
if ($("voiceToggleSetting")) {
    $("voiceToggleSetting").onclick = () => {
        speakOn = !speakOn;
        localStorage.setItem("calia_voice", speakOn ? "true" : "false");
        updateVoiceUI();
        toast(speakOn ? "Voice replies on 🔊" : "Voice replies off 🔇");
    };
}

// API Key Config
function promptApiKey() {
    let cur = localStorage.getItem("calia_api_key") || "";
    let val = prompt("Custom Groq or Gemini API Key (Default Groq key is already active on the server):", cur);
    if (val !== null) {
        val = val.trim();
        if (val) {
            localStorage.setItem("calia_api_key", val);
            toast("Custom API key active! ✨");
        } else {
            localStorage.removeItem("calia_api_key");
            toast("Using pre-configured Groq AI key! ✨");
        }
    }
}
if ($("keyToggle")) $("keyToggle").onclick = promptApiKey;
if ($("keyToggleSetting")) $("keyToggleSetting").onclick = promptApiKey;

$("mic").onclick = () => {
    let SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { toast("Voice input works best in Chrome; please type instead."); return; }
    let rec = new SR();
    rec.lang = "en-IN";
    rec.onstart = () => toast("Listening… speak now");
    rec.onresult = e => send(e.results[0][0].transcript);
    rec.onerror = () => toast("Could not hear you; try again.");
    rec.start();
};

// ==========================================
// Settings Popover & Theme Controller
// ==========================================
if ($("openSettings")) {
    $("openSettings").onclick = e => {
        e.stopPropagation();
        $("settingsDropdown").classList.toggle("show");
    };
}
document.addEventListener("click", e => {
    if (!e.target.closest(".settings-wrap") && $("settingsDropdown")) {
        $("settingsDropdown").classList.remove("show");
    }
});

const themeOptBtns = document.querySelectorAll(".theme-opt-btn");
function setTheme(mode, notify = false) {
    let effective = mode;
    if (mode === "system") {
        effective = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    }
    document.documentElement.setAttribute("data-theme", effective);
    localStorage.setItem("calia_theme", mode);
    themeOptBtns.forEach(btn => {
        btn.classList.toggle("active", btn.dataset.themeVal === mode);
    });
    if (notify) {
        const labels = { light: "Bright mode ☀️", dark: "Dark mode 🌙", system: "System default 💻" };
        toast(`Appearance: ${labels[mode] || mode}`);
    }
}
const initialTheme = localStorage.getItem("calia_theme") || "system";
setTheme(initialTheme, false);

themeOptBtns.forEach(b => {
    b.onclick = () => {
        setTheme(b.dataset.themeVal, true);
        $("settingsDropdown").classList.remove("show");
    };
});
window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
    if ((localStorage.getItem("calia_theme") || "system") === "system") {
        setTheme("system", false);
    }
});

// ==========================================
// User Authentication, Cards & Caching
// ==========================================

// Hydrate cached user from localStorage immediately
const cachedUserStr = localStorage.getItem("calia_user_data");
if (cachedUserStr) {
    try {
        currentUser = JSON.parse(cachedUserStr);
    } catch (e) {
        currentUser = null;
    }
}
updateUserHeaderIcon();

// Background sync with server
async function syncUserAuth() {
    if (!currentToken) return;
    try {
        const res = await fetch("/api/auth/me", {
            headers: { "Authorization": `Bearer ${currentToken}` }
        });
        const data = await res.json();
        if (data.status === "ok" && data.user) {
            currentUser = data.user;
            localStorage.setItem("calia_user_data", JSON.stringify(currentUser));
            updateUserHeaderIcon();
        } else if (res.status === 401) {
            logoutLocal();
        }
    } catch (err) {
        console.warn("Using offline cached account data");
    }
}
syncUserAuth();

function updateUserHeaderIcon() {
    const symbol = $("userIconSymbol");
    const dot = $("userAvatarDot");
    if (!symbol) return;
    if (currentUser) {
        const initial = (currentUser.name || "U").charAt(0).toUpperCase();
        symbol.textContent = initial;
        symbol.style.fontWeight = "800";
        symbol.style.fontFamily = "Manrope, sans-serif";
        symbol.style.color = "var(--lav-dark)";
        if (dot) dot.classList.add("active");
    } else {
        symbol.textContent = "👤";
        symbol.style.fontWeight = "normal";
        if (dot) dot.classList.remove("active");
    }
}

function logoutLocal() {
    currentUser = null;
    currentToken = "";
    localStorage.removeItem("calia_auth_token");
    localStorage.removeItem("calia_user_data");
    updateUserHeaderIcon();
    renderUserDrawer();
    toast("Signed out successfully ♡");
}

let activeUserTab = "cards";

function renderUserDrawer(defaultTab) {
    if (defaultTab) activeUserTab = defaultTab;
    const container = $("userDrawerContent");
    if (!container) return;

    if (!currentUser) {
        // Render Sign In / Sign Up Forms + Quick Demo Button
        container.innerHTML = `
            <div style="margin-bottom:18px">
                <small style="font-weight:800;letter-spacing:1px;color:var(--lav-dark);font-size:10px">WELCOME TO CALIA</small>
                <h2 style="font:800 22px Manrope;margin:4px 0 12px;color:var(--ink-heading)">Your Account</h2>
                <p style="font-size:12px;color:var(--muted);line-height:1.5">Sign in to save payment cards, view order history, and personalize your experience.</p>
            </div>

            <button type="button" class="btn-demo-quick" id="btnQuickDemo">
                <span>⚡ Instant Demo Login (Mohamed Arshad)</span>
            </button>

            <div class="user-tabs">
                <button type="button" class="user-tab-btn active" id="tabSignIn">Sign In</button>
                <button type="button" class="user-tab-btn" id="tabSignUp">Create Account</button>
            </div>

            <div id="authFormContainer">
                <form id="signInForm" class="user-form-card" style="margin-top:0">
                    <div class="user-form-group">
                        <label>Email Address</label>
                        <input type="email" id="loginEmail" required placeholder="name@example.com" value="demo@calia.tech">
                    </div>
                    <div class="user-form-group">
                        <label>Password</label>
                        <input type="password" id="loginPass" required placeholder="••••••••" value="password123">
                    </div>
                    <button type="submit" class="btn-submit-action" id="btnLoginSubmit">Sign In ↗</button>
                </form>

                <form id="signUpForm" class="user-form-card" style="display:none;margin-top:0">
                    <div class="user-form-group">
                        <label>Full Name</label>
                        <input type="text" id="regName" required placeholder="e.g. Alex Rivera">
                    </div>
                    <div class="user-form-group">
                        <label>Email Address</label>
                        <input type="email" id="regEmail" required placeholder="alex@example.com">
                    </div>
                    <div class="user-form-group">
                        <label>Password</label>
                        <input type="password" id="regPass" required placeholder="At least 6 characters">
                    </div>
                    <button type="submit" class="btn-submit-action" id="btnRegSubmit">Create Account ↗</button>
                </form>
            </div>
            <div class="cache-sync-badge">
                <span>✓</span> Offline Caching & Local Storage Active
            </div>
        `;

        $("btnQuickDemo").onclick = () => doLogin("demo@calia.tech", "password123");

        $("tabSignIn").onclick = () => {
            $("tabSignIn").classList.add("active");
            $("tabSignUp").classList.remove("active");
            $("signInForm").style.display = "block";
            $("signUpForm").style.display = "none";
        };
        $("tabSignUp").onclick = () => {
            $("tabSignUp").classList.add("active");
            $("tabSignIn").classList.remove("active");
            $("signInForm").style.display = "none";
            $("signUpForm").style.display = "block";
        };

        $("signInForm").onsubmit = async e => {
            e.preventDefault();
            await doLogin($("loginEmail").value, $("loginPass").value);
        };
        $("signUpForm").onsubmit = async e => {
            e.preventDefault();
            await doRegister($("regName").value, $("regEmail").value, $("regPass").value);
        };

    } else {
        // Logged-in profile view with tabs
        const initial = (currentUser.name || "U").charAt(0).toUpperCase();
        const cards = currentUser.cards || [];
        const orders = currentUser.orders || [];
        const chats = currentUser.chat_history || [];
        const defaultCard = cards.find(c => c.is_default) || cards[0];

        let tabContentHtml = "";

        if (activeUserTab === "cards") {
            // Cards tab
            let cardVisualHtml = "";
            if (defaultCard) {
                cardVisualHtml = `
                    <div class="card-visual">
                        <div class="card-brand-badge">${defaultCard.brand}</div>
                        <div class="card-chip"></div>
                        <div class="card-number-display">${defaultCard.number_masked}</div>
                        <div class="card-details-row">
                            <div>
                                <span>CARDHOLDER</span>
                                <b>${defaultCard.holder || currentUser.name}</b>
                            </div>
                            <div style="text-align:right">
                                <span>EXPIRES</span>
                                <b>${defaultCard.exp || "12/28"}</b>
                            </div>
                        </div>
                    </div>
                `;
            } else {
                cardVisualHtml = `
                    <div class="card-visual" style="background:linear-gradient(135deg,#3c2b48,#261935);text-align:center;padding:30px 20px">
                        <p style="margin:0;font-size:12px;opacity:0.8">No saved cards yet.<br>Add a payment card below to enable 1-click checkout.</p>
                    </div>
                `;
            }

            let cardsListHtml = cards.map(c => `
                <div class="saved-card-item">
                    <span class="card-brand-icon">${c.brand === "Visa" ? "💳" : "🪙"}</span>
                    <div class="card-meta">
                        <b>${c.brand} •••• ${c.last4} ${c.is_default ? '<small style="color:var(--lav-dark);font-weight:700">· DEFAULT</small>' : ''}</b>
                        <span>Expires ${c.exp} · ${c.holder}</span>
                    </div>
                    <button class="btn-delete-card" data-delete-card="${c.id}" title="Remove Card">🗑</button>
                </div>
            `).join("");

            tabContentHtml = `
                ${cardVisualHtml}
                <div style="display:flex;justify-content:space-between;align-items:center;margin:14px 2px 8px">
                    <b style="font-size:12px;color:var(--ink-heading)">Your Saved Cards (${cards.length})</b>
                    <small style="color:var(--muted);font-size:10px">Tied to ${currentUser.email}</small>
                </div>
                <div>${cardsListHtml}</div>

                <!-- Add New Card Form -->
                <details style="margin-top:14px">
                    <summary style="cursor:pointer;font-size:11px;font-weight:700;color:var(--accent);user-select:none;outline:0">＋ Add a new card</summary>
                    <form id="addCardForm" class="user-form-card">
                        <div class="user-form-group">
                            <label>Cardholder Name</label>
                            <input type="text" id="newCardHolder" required placeholder="Name on card" value="${currentUser.name}">
                        </div>
                        <div class="user-form-group">
                            <label>Card Number</label>
                            <input type="text" id="newCardNum" required placeholder="4242 •••• •••• 4242" maxlength="19">
                        </div>
                        <div class="form-row">
                            <div class="user-form-group">
                                <label>Expiry (MM/YY)</label>
                                <input type="text" id="newCardExp" required placeholder="12/28" maxlength="5">
                            </div>
                            <div class="user-form-group">
                                <label>CVV</label>
                                <input type="password" id="newCardCvv" required placeholder="•••" maxlength="4">
                            </div>
                        </div>
                        <button type="submit" class="btn-submit-action">Save Card to Account ↗</button>
                    </form>
                </details>
            `;

        } else if (activeUserTab === "orders") {
            // Orders tab
            if (orders.length === 0) {
                tabContentHtml = `<div style="text-align:center;padding:30px;color:var(--muted);font-size:12px">No orders placed yet. Add items to your cart and checkout! ♡</div>`;
            } else {
                tabContentHtml = orders.map(ord => {
                    const itemsHtml = (ord.items || []).map(it => `
                        <div class="order-item-mini">
                            <img src="${it.img || 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=100&q=80'}">
                            <div style="flex:1">
                                <b>${it.name}</b>
                                <div style="color:var(--muted);font-size:10px">Qty: ${it.qty || 1} · ₹${(it.price || 0).toLocaleString("en-IN")}</div>
                            </div>
                        </div>
                    `).join("");

                    return `
                        <div class="order-card">
                            <div class="order-header-row">
                                <div><b>${ord.id}</b> <span style="color:var(--muted)">· ${ord.date}</span></div>
                                <span class="order-status-tag">${ord.status || 'Delivered'}</span>
                            </div>
                            <div class="order-item-list">${itemsHtml}</div>
                            <div class="order-total-bar">
                                <span>Paid with card •••• ${ord.card_last4 || '4242'}</span>
                                <b>Total: ₹${(ord.total || 0).toLocaleString("en-IN")}</b>
                            </div>
                        </div>
                    `;
                }).join("");
            }

        } else if (activeUserTab === "chat") {
            // Chat history tab
            if (chats.length === 0) {
                tabContentHtml = `<div style="text-align:center;padding:30px;color:var(--muted);font-size:12px">No recent support chats. Talk with CALIX using the floating icon! ✦</div>`;
            } else {
                tabContentHtml = [...chats].reverse().map(ch => `
                    <div class="chat-history-card">
                        <div class="chat-history-time">✦ ${ch.timestamp || 'Recent inquiry'}</div>
                        <div class="chat-q">Q: ${ch.message}</div>
                        <div class="chat-a">A: ${ch.reply}</div>
                    </div>
                `).join("");
            }
        }

        container.innerHTML = `
            <div class="user-profile-card">
                <div class="user-avatar-big">${initial}</div>
                <div class="user-meta">
                    <h3>${currentUser.name}</h3>
                    <p>${currentUser.email}</p>
                    <span class="user-vip-chip">${currentUser.tier || '✦ CALIA Member'}</span>
                </div>
                <button type="button" class="btn-logout" id="btnLogout" title="Log out">Sign Out</button>
            </div>

            <div class="user-tabs">
                <button type="button" class="user-tab-btn ${activeUserTab === 'cards' ? 'active' : ''}" id="tabCards">💳 Cards</button>
                <button type="button" class="user-tab-btn ${activeUserTab === 'orders' ? 'active' : ''}" id="tabOrders">📦 Orders (${orders.length})</button>
                <button type="button" class="user-tab-btn ${activeUserTab === 'chat' ? 'active' : ''}" id="tabChatHistory">💬 Chat</button>
            </div>

            <div id="tabContentArea">${tabContentHtml}</div>

            <div class="cache-sync-badge">
                <span>✓</span> Data Cached Locally · Synced with CALIA Server
            </div>
        `;

        $("btnLogout").onclick = async () => {
            try {
                await fetch("/api/auth/logout", {
                    method: "POST",
                    headers: { "Authorization": `Bearer ${currentToken}` }
                });
            } catch (e) {}
            logoutLocal();
        };

        $("tabCards").onclick = () => renderUserDrawer("cards");
        $("tabOrders").onclick = () => renderUserDrawer("orders");
        $("tabChatHistory").onclick = () => renderUserDrawer("chat");

        // Delete card button handlers
        container.querySelectorAll("[data-delete-card]").forEach(btn => {
            btn.onclick = async () => {
                const cardId = btn.dataset.deleteCard;
                try {
                    const res = await fetch(`/api/user/cards/${cardId}`, {
                        method: "DELETE",
                        headers: { "Authorization": `Bearer ${currentToken}` }
                    });
                    const d = await res.json();
                    if (d.status === "ok") {
                        currentUser.cards = d.cards;
                        localStorage.setItem("calia_user_data", JSON.stringify(currentUser));
                        toast("Card removed");
                        renderUserDrawer("cards");
                    }
                } catch (e) {
                    toast("Failed to delete card");
                }
            };
        });

        // Add Card Form Submission
        const addCardForm = $("addCardForm");
        if (addCardForm) {
            // Auto format card number with spaces
            const numInput = $("newCardNum");
            numInput.oninput = e => {
                let v = e.target.value.replace(/\D/g, "").substring(0, 16);
                e.target.value = v.replace(/(\d{4})(?=\d)/g, "$1 ");
            };
            const expInput = $("newCardExp");
            expInput.oninput = e => {
                let v = e.target.value.replace(/\D/g, "").substring(0, 4);
                if (v.length >= 2) e.target.value = v.substring(0, 2) + "/" + v.substring(2);
                else e.target.value = v;
            };

            addCardForm.onsubmit = async e => {
                e.preventDefault();
                const cardData = {
                    holder: $("newCardHolder").value.trim(),
                    number: $("newCardNum").value.trim(),
                    exp: $("newCardExp").value.trim()
                };

                try {
                    const res = await fetch("/api/user/cards", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            "Authorization": `Bearer ${currentToken}`
                        },
                        body: JSON.stringify(cardData)
                    });
                    const data = await res.json();
                    if (data.status === "ok") {
                        currentUser.cards = data.cards;
                        localStorage.setItem("calia_user_data", JSON.stringify(currentUser));
                        toast("New card saved to your account! 💳");
                        renderUserDrawer("cards");
                    } else {
                        toast(data.message || "Failed to save card");
                    }
                } catch (err) {
                    toast("Network error saving card");
                }
            };
        }
    }
}

async function doLogin(email, password) {
    try {
        const res = await fetch("/api/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();
        if (data.status === "ok") {
            currentToken = data.token;
            currentUser = data.user;
            localStorage.setItem("calia_auth_token", currentToken);
            localStorage.setItem("calia_user_data", JSON.stringify(currentUser));
            updateUserHeaderIcon();
            toast(`Welcome back, ${currentUser.name}! ✦`);
            renderUserDrawer("cards");
        } else {
            toast(data.message || "Login failed");
        }
    } catch (e) {
        toast("Login failed due to connection error");
    }
}

async function doRegister(name, email, password) {
    try {
        const res = await fetch("/api/auth/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, email, password })
        });
        const data = await res.json();
        if (data.status === "ok") {
            currentToken = data.token;
            currentUser = data.user;
            localStorage.setItem("calia_auth_token", currentToken);
            localStorage.setItem("calia_user_data", JSON.stringify(currentUser));
            updateUserHeaderIcon();
            toast(`Account created! Welcome, ${currentUser.name}! ✦`);
            renderUserDrawer("cards");
        } else {
            toast(data.message || "Registration failed");
        }
    } catch (e) {
        toast("Registration error. Please try again.");
    }
}

// Deep link hash helper (e.g. #user, #orders, #settings, #demo)
function handleHash() {
    const hash = window.location.hash;
    if (hash === "#user") {
        overlay("userDrawer");
        renderUserDrawer();
    } else if (hash === "#orders") {
        overlay("userDrawer");
        renderUserDrawer("orders");
    } else if (hash === "#cards") {
        overlay("userDrawer");
        renderUserDrawer("cards");
    } else if (hash === "#settings" && $("settingsDropdown")) {
        $("settingsDropdown").classList.add("show");
    } else if (hash === "#chat") {
        overlay("chat");
    } else if (hash === "#demo") {
        doLogin("demo@calia.tech", "password123").then(() => {
            overlay("userDrawer");
            renderUserDrawer("cards");
        });
    }
}
window.addEventListener("hashchange", handleHash);
handleHash();

