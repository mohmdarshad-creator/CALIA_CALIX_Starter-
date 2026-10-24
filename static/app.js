const $=id=>document.getElementById(id);let cart={},speakOn=localStorage.getItem("calia_voice")==="true";
const items=[...document.querySelectorAll(".card")].map(c=>({id:+c.querySelector(".add").dataset.id,name:c.querySelector(".add").dataset.name,price:+c.querySelector(".add").dataset.price,img:c.querySelector("img").src}));
let toastTimer;
function toast(t){const el=$("toast");el.textContent=t;el.classList.add("show");clearTimeout(toastTimer);toastTimer=setTimeout(()=>el.classList.remove("show"),2000)}
function overlay(which){$("shade").classList.add("show");$(which).classList.add("open")}function close(){["cart","chat"].forEach(x=>$(x).classList.remove("open"));$("shade").classList.remove("show")}
$("shade").onclick=close;$("openCart").onclick=()=>overlay("cart");$("closeCart").onclick=close;$("openChat").onclick=$("openChat2").onclick=()=>overlay("chat");$("closeChat").onclick=close;
function renderCart(){let n=Object.values(cart).reduce((a,b)=>a+b,0);$("count").textContent=n;$("cartCount").textContent=n;let total=0;let html="";for(let id in cart){let p=items.find(x=>x.id==id);total+=p.price*cart[id];html+=`<div class="cartrow"><img src="${p.img}"><b>${p.name}<br>₹${p.price.toLocaleString("en-IN")} × ${cart[id]}</b><button data-remove="${id}">×</button></div>`} $("cartItems").innerHTML=html||"Your cart is waiting for something lovely ♡";$("total").textContent="₹"+total.toLocaleString("en-IN")}
function spawnSparkles(btn){const rect=btn.getBoundingClientRect();const symbols=["✦","♡","✧","₊˚"];for(let i=0;i<4;i++){const span=document.createElement("span");span.className="sparkle-particle";span.textContent=symbols[i%symbols.length];span.style.left=`${rect.left+rect.width/2+(Math.random()*40-20)}px`;span.style.top=`${rect.top+(Math.random()*10-5)}px`;span.style.setProperty("--dx",`${(Math.random()-0.5)*60}px`);span.style.setProperty("--dy",`${-35-Math.random()*30}px`);document.body.appendChild(span);setTimeout(()=>span.remove(),750)}}
function flyToCart(imgElement,cartBtnElement,onLand){if(!imgElement||!cartBtnElement){if(onLand)onLand();return}const imgRect=imgElement.getBoundingClientRect();const cartRect=cartBtnElement.getBoundingClientRect();const flyer=document.createElement("img");flyer.src=imgElement.src;flyer.className="flying-cart-item";flyer.style.top=`${imgRect.top}px`;flyer.style.left=`${imgRect.left}px`;flyer.style.width=`${imgRect.width}px`;flyer.style.height=`${imgRect.height}px`;document.body.appendChild(flyer);void flyer.offsetWidth;const targetX=cartRect.left+cartRect.width/2-16;const targetY=cartRect.top+cartRect.height/2-16;flyer.style.top=`${targetY}px`;flyer.style.left=`${targetX}px`;flyer.style.width="32px";flyer.style.height="32px";flyer.style.opacity="0.25";flyer.style.transform="rotate(25deg) scale(0.6)";setTimeout(()=>{flyer.remove();if(onLand)onLand();cartBtnElement.classList.remove("cart-bump");void cartBtnElement.offsetWidth;cartBtnElement.classList.add("cart-bump")},650)}
document.querySelectorAll(".add").forEach(b=>{b.onclick=()=>{const id=b.dataset.id;const card=b.closest(".card");const img=card?card.querySelector(".photo img"):null;const cartBtn=$("openCart");b.classList.add("btn-added");const origContent=b.innerHTML;b.innerHTML=`Added! <b style="font-size:13px">✓</b>`;spawnSparkles(b);setTimeout(()=>{b.classList.remove("btn-added");b.innerHTML=origContent},900);flyToCart(img,cartBtn,()=>{cart[id]=(cart[id]||0)+1;renderCart();toast("Added to cart ♡")})}});$("cartItems").onclick=e=>{if(e.target.dataset.remove){delete cart[e.target.dataset.remove];renderCart()}};$("checkout").onclick=()=>toast("Demo only — no payment taken");
document.querySelectorAll(".heart").forEach(b=>b.onclick=()=>{b.textContent=b.textContent==="♡"?"♥":"♡";toast("Favourites updated")});
document.querySelectorAll(".cats button").forEach(b=>b.onclick=()=>{document.querySelectorAll(".cats button").forEach(x=>x.classList.remove("selected"));b.classList.add("selected");document.querySelectorAll(".card").forEach(c=>c.style.display=b.dataset.cat==="All"||c.dataset.cat===b.dataset.cat?"":"none")});
$("search").oninput=e=>{let q=e.target.value.toLowerCase();document.querySelectorAll(".card").forEach(c=>c.style.display=c.dataset.name.includes(q)||c.dataset.cat.toLowerCase().includes(q)?"":"none")};
function add(text,who,sources,retrievalMode){
    let d=document.createElement("div");
    d.className="msg "+who;
    let t=document.createElement("div");
    t.textContent=text;
    d.append(t);
    if(who==="bot"&&sources&&sources.length>0){
        let badge=document.createElement("div");
        badge.className="rag-badge";
        let items=sources.map(s=>`<div class="rag-item"><b>${s.title}</b> <span class="rag-cat">${s.category||"Knowledge"}</span><p>${s.snippet||""}</p></div>`).join("");
        badge.innerHTML=`<div class="rag-header"><span class="rag-pill">📚 RAG Grounded</span><span class="rag-mode">${retrievalMode||"Vector Index"}</span></div><details class="rag-sources"><summary>View ${sources.length} retrieved source${sources.length>1?"s":""} ▾</summary><div class="rag-list">${items}</div></details>`;
        d.append(badge);
    }
    $("messages").append(d);
    $("messages").scrollTop=$("messages").scrollHeight;
}
function speak(t){if(speakOn&&"speechSynthesis"in window){speechSynthesis.cancel();let u=new SpeechSynthesisUtterance(t);u.lang="en-IN";speechSynthesis.speak(u)}}
async function send(text){
    text=(text||$("input").value).trim();
    if(!text)return;
    $("input").value="";
    add(text,"user");
    $("send").disabled=true;
    let apiKey=localStorage.getItem("calia_api_key")||"";
    try{
        let r=await fetch("/chat",{
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body:JSON.stringify({message:text,api_key:apiKey})
        });
        let d=await r.json();
        add(d.reply,"bot",d.sources,d.retrieval_mode);
        speak(d.reply);
    }catch(e){
        add("I couldn't connect just now. Please try again.","bot");
    }finally{
        $("send").disabled=false;
    }
}
$("send").onclick=()=>send();
$("input").onkeydown=e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();send()}};
document.querySelectorAll(".quick").forEach(b=>b.onclick=()=>send(b.textContent));
if($("voiceToggle")){$("voiceToggle").textContent=speakOn?"🔊":"🔇";$("voiceToggle").onclick=()=>{speakOn=!speakOn;localStorage.setItem("calia_voice",speakOn?"true":"false");$("voiceToggle").textContent=speakOn?"🔊":"🔇";toast(speakOn?"Voice replies on 🔊":"Voice replies off 🔇")}}
if($("keyToggle")){$("keyToggle").onclick=()=>{
    let cur=localStorage.getItem("calia_api_key")||"";
    let val=prompt("Custom Groq or Gemini API Key (Default Groq key is already active on the server):",cur);
    if(val!==null){
        val=val.trim();
        if(val){localStorage.setItem("calia_api_key",val);toast("Custom API key active! ✨")}
        else{localStorage.removeItem("calia_api_key");toast("Using pre-configured Groq AI key! ✨")}
    }
}}
$("mic").onclick=()=>{let SR=window.SpeechRecognition||window.webkitSpeechRecognition;if(!SR){toast("Voice input works best in Chrome; please type instead.");return}let rec=new SR();rec.lang="en-IN";rec.onstart=()=>toast("Listening… speak now");rec.onresult=e=>send(e.results[0][0].transcript);rec.onerror=()=>toast("Could not hear you; try again.");rec.start()};

// Theme Controller (Light, Dark, System)
const themeBtns = document.querySelectorAll(".theme-btn");
function setTheme(mode, notify = false) {
    let effective = mode;
    if (mode === "system") {
        effective = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    }
    document.documentElement.setAttribute("data-theme", effective);
    localStorage.setItem("calia_theme", mode);
    themeBtns.forEach(btn => {
        btn.classList.toggle("active", btn.dataset.themeVal === mode);
    });
    if (notify) {
        const labels = { light: "Light mode ☀️", dark: "Dark mode 🌙", system: "System default 💻" };
        toast(`Theme: ${labels[mode] || mode}`);
    }
}
const initialTheme = localStorage.getItem("calia_theme") || "system";
setTheme(initialTheme, false);
themeBtns.forEach(b => {
    b.onclick = () => setTheme(b.dataset.themeVal, true);
});
window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
    if ((localStorage.getItem("calia_theme") || "system") === "system") {
        setTheme("system", false);
    }
});
