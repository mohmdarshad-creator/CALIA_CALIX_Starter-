import os, requests
from flask import Flask, render_template, request, jsonify
app=Flask(__name__)
PRODUCTS=[
{"id":1,"name":"Aura Wireless Headphones","cat":"Audio","price":2499,"old":3499,"rating":"4.6","img":"https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=800&q=85"},
{"id":2,"name":"Pulse Smart Watch","cat":"Wearables","price":3299,"old":4999,"rating":"4.4","img":"https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=800&q=85"},
{"id":3,"name":"Nova Wireless Earbuds","cat":"Audio","price":1799,"old":2599,"rating":"4.5","img":"https://images.unsplash.com/photo-1606220945770-b5b6c2c55bf1?auto=format&fit=crop&w=800&q=85"},
{"id":4,"name":"Orbit Mini Speaker","cat":"Audio","price":1499,"old":2199,"rating":"4.3","img":"https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?auto=format&fit=crop&w=800&q=85"},
{"id":5,"name":"Snap Compact Camera","cat":"Cameras","price":8999,"old":10999,"rating":"4.7","img":"https://images.unsplash.com/photo-1516035069371-29a1b244cc32?auto=format&fit=crop&w=800&q=85"},
{"id":6,"name":"Flex Tablet","cat":"Smart devices","price":12499,"old":14999,"rating":"4.5","img":"https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?auto=format&fit=crop&w=800&q=85"},
{"id":7,"name":"Click Mechanical Keyboard","cat":"Accessories","price":2899,"old":3799,"rating":"4.6","img":"https://images.unsplash.com/photo-1587829741301-dc798b83add3?auto=format&fit=crop&w=800&q=85"},
{"id":8,"name":"Charge 20K Power Bank","cat":"Accessories","price":1299,"old":1899,"rating":"4.2","img":"https://images.unsplash.com/photo-1609091839311-d5365f9ff1c5?auto=format&fit=crop&w=800&q=85"}]
SYSTEM="""You are CALIX, the friendly voice-powered support assistant for CALIA, a fictional gadget store. Answer general questions naturally and help with listed products, prices, demo delivery and returns. Demo delivery is 3-5 business days; eligible unused products can be returned within 7 days. For damaged items, ask for an order ID and explain this is only a simulated request. For duplicate payment, explain escalation to human specialist Maya. Never claim real orders, refunds, replacements, or payments were changed. Be concise. Products: Aura headphones ₹2499, Pulse watch ₹3299, Nova earbuds ₹1799, Orbit speaker ₹1499, Snap camera ₹8999, Flex tablet ₹12499, Click keyboard ₹2899, Charge power bank ₹1299."""
@app.route("/")
def home(): return render_template("index.html",products=PRODUCTS)
@app.route("/chat",methods=["POST"])
def chat():
 msg=(request.json or {}).get("message","").strip()
 key=os.getenv("GEMINI_API_KEY","")
 if key and msg:
  try:
   r=requests.post("https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",params={"key":key},json={"systemInstruction":{"parts":[{"text":SYSTEM}]},"contents":[{"role":"user","parts":[{"text":msg}]}],"generationConfig":{"maxOutputTokens":400}},timeout=20)
   r.raise_for_status()
   return jsonify(reply=r.json()["candidates"][0]["content"]["parts"][0]["text"])
  except Exception: pass
 q=msg.lower()
 if any(x in q for x in ["hi","hello","hey"]): ans="Hey there! ✨ I’m CALIX, your CALIA support buddy. Are you shopping for a gadget or do you need help with an order?"
 elif any(x in q for x in ["damaged","broken","replacement","not working"]): ans="I’m sorry that happened 💜 Share your demo order ID and tell me what is damaged. I can prepare a simulated support request; no real replacement will be created."
 elif any(x in q for x in ["duplicate","charged twice","payment","double charge"]): ans="I understand. I’d escalate this to Maya, our human support specialist. Keep your transaction reference handy. This demo cannot access real payments."
 elif any(x in q for x in ["delivery","shipping","arrive"]): ans="The demo delivery estimate is 3–5 business days. CALIA is a prototype, so no real shipment is created."
 elif any(x in q for x in ["return","refund","exchange"]): ans="Our demo policy allows eligible unused products to be returned within 7 days. This prototype does not process real refunds."
 elif any(x in q for x in ["price","recommend","headphone","earbud","watch","speaker","camera","tablet","keyboard","budget"]): ans="Some CALIA picks: Nova Earbuds ₹1,799, Aura Headphones ₹2,499, Pulse Smart Watch ₹3,299 and Orbit Speaker ₹1,499. Tell me your budget and what you need it for!"
 else: ans="I can help with gadget recommendations, prices, demo delivery and returns, damaged-item support, or duplicate-payment escalation. For open-ended AI answers, add a Gemini API key as shown in README.md."
 return jsonify(reply=ans)
if __name__=="__main__": app.run(debug=True,port=5000)
