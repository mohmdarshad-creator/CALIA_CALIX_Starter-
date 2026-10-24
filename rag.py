import os
import json
import math
import re
from typing import List, Dict, Any, Tuple
import requests
import numpy as np
def _load_local_env():
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_file):
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k, v = k.strip(), v.strip().strip('"').strip("'")
                        if k and k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass

_load_local_env()

DEFAULT_GROQ_KEY = os.getenv("GROQ_API_KEY", "")

STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by",
    "can", "could", "did", "do", "does", "doing", "down", "during", "each", "few", "for", "from",
    "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself", "him", "himself",
    "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just", "me", "more", "most",
    "my", "myself", "no", "nor", "not", "now", "of", "off", "on", "once", "only", "or", "other",
    "our", "ours", "ourselves", "out", "over", "own", "same", "she", "should", "so", "some", "such",
    "than", "that", "the", "their", "theirs", "them", "themselves", "then", "there", "these", "they",
    "this", "those", "through", "to", "too", "under", "until", "up", "very", "was", "we", "were",
    "what", "when", "where", "which", "while", "who", "whom", "why", "will", "with", "would", "you",
    "your", "yours", "yourself", "yourselves"
}

def is_code_or_programming_request(query: str) -> bool:
    """Detects requests for code, programming, or non-shopping technical tasks."""
    q = query.lower()
    patterns = [
        r"\b(?:give|write|generate|provide|create|show|print|need|share)\s+(?:me\s+)?(?:some\s+)?(?:python|javascript|typescript|js|html|css|c\+\+|java|c#|sql|php|rust|ruby|bash|shell|go|swift|react|vue|angular|node)?\s*(?:code|script|program|function|snippet|class|algo|algorithm|query|regex|payload)\b",
        r"\b(?:how to (?:code|program|implement|write code|build a script|hack|exploit))\b",
        r"\b(?:debug|fix this code|syntax error|compile error|runtime error|nullpointer)\b",
        r"\b(?:def\s+\w+\(|function\s+\w+\(|import\s+\w+|console\.log|print\(|public static void)\b",
        r"\b(?:write\s+a\s+(?:crawler|scraper|bot|api|server|macro|keylogger))\b"
    ]
    for p in patterns:
        if re.search(p, q):
            return True
    return False


class LocalVectorIndex:
    """In-memory TF-IDF vector index with field weighting and stopword removal."""
    def __init__(self, chunks: List[Dict[str, Any]]):
        self.chunks = chunks
        self.doc_freq = {}
        self.doc_vectors = []
        self.vocabulary = {}
        self._build_index()

    def _tokenize(self, text: str, remove_stopwords: bool = True) -> List[str]:
        words = re.findall(r"\b[a-zA-Z0-9_\u0900-\u097F]+\b", text.lower())
        if remove_stopwords:
            filtered = [w for w in words if w not in STOPWORDS and len(w) > 1]
            return filtered if filtered else words
        return words

    def _build_index(self):
        total_docs = len(self.chunks)
        if total_docs == 0:
            return

        doc_tokens = []
        for chunk in self.chunks:
            title_text = f" {chunk.get('title', '')}" * 3
            cat_text = f" {chunk.get('category', '')}" * 2
            tags_text = f" {' '.join(chunk.get('tags', []))}" * 2
            content_text = chunk.get('content', '')
            full_text = f"{title_text} {cat_text} {tags_text} {content_text}"
            
            tokens = self._tokenize(full_text)
            doc_tokens.append(tokens)
            unique_terms = set(tokens)
            for term in unique_terms:
                self.doc_freq[term] = self.doc_freq.get(term, 0) + 1

        vocab_list = list(self.doc_freq.keys())
        self.vocabulary = {term: idx for idx, term in enumerate(vocab_list)}
        vocab_size = len(vocab_list)

        self.doc_vectors = np.zeros((total_docs, vocab_size), dtype=np.float32)
        for doc_idx, tokens in enumerate(doc_tokens):
            term_counts = {}
            for t in tokens:
                term_counts[t] = term_counts.get(t, 0) + 1
            for term, count in term_counts.items():
                col_idx = self.vocabulary[term]
                tf = 1 + math.log(count) if count > 0 else 0
                idf = math.log((1 + total_docs) / (1 + self.doc_freq[term])) + 1.0
                self.doc_vectors[doc_idx, col_idx] = tf * idf

        norms = np.linalg.norm(self.doc_vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self.doc_vectors = self.doc_vectors / norms

    def search(self, query: str, top_k: int = 3) -> List[Tuple[Dict[str, Any], float]]:
        if len(self.chunks) == 0:
            return []
        tokens = self._tokenize(query)
        if not tokens:
            return [(self.chunks[i], 0.0) for i in range(min(top_k, len(self.chunks)))]

        query_vec = np.zeros(len(self.vocabulary), dtype=np.float32)
        total_docs = len(self.chunks)
        term_counts = {}
        for t in tokens:
            term_counts[t] = term_counts.get(t, 0) + 1

        for term, count in term_counts.items():
            if term in self.vocabulary:
                col_idx = self.vocabulary[term]
                tf = 1 + math.log(count) if count > 0 else 0
                idf = math.log((1 + total_docs) / (1 + self.doc_freq[term])) + 1.0
                query_vec[col_idx] = tf * idf

        q_norm = np.linalg.norm(query_vec)
        if q_norm > 0:
            query_vec = query_vec / q_norm
            scores = np.dot(self.doc_vectors, query_vec)
        else:
            scores = np.zeros(len(self.chunks), dtype=np.float32)

        top_indices = np.argsort(scores)[::-1][:top_k]
        results = []
        for idx in top_indices:
            results.append((self.chunks[idx], float(scores[idx])))
        return results


class RAGPipeline:
    """Production RAG Pipeline with Groq LLM integration, customer support persona, and strict guardrails."""
    def __init__(self, knowledge_dir: str = None):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.knowledge_dir = knowledge_dir or os.path.join(base_dir, "knowledge")
        self.chunks = []
        self.products_data = []
        self.load_documents()
        self.local_index = LocalVectorIndex(self.chunks)

    def load_documents(self):
        """Loads and prepares chunks from products and policies."""
        self.chunks = []
        self.products_data = []
        products_file = os.path.join(self.knowledge_dir, "products.json")
        if os.path.exists(products_file):
            try:
                with open(products_file, "r", encoding="utf-8") as f:
                    self.products_data = json.load(f)
                    for p in self.products_data:
                        self.chunks.append({
                            "id": p.get("id"),
                            "title": p.get("name", "Product Info"),
                            "category": p.get("category", "Products"),
                            "tags": p.get("tags", []),
                            "content": p.get("content", ""),
                            "is_product": True,
                            "price": p.get("price"),
                            "original_price": p.get("original_price"),
                            "rating": p.get("rating")
                        })
            except Exception as e:
                print(f"[RAG] Error loading products: {e}")

        policies_file = os.path.join(self.knowledge_dir, "policies.json")
        if os.path.exists(policies_file):
            try:
                with open(policies_file, "r", encoding="utf-8") as f:
                    policies = json.load(f)
                    for pol in policies:
                        self.chunks.append({
                            "id": pol.get("id"),
                            "title": pol.get("title", "Store Policy"),
                            "category": pol.get("category", "Policies"),
                            "tags": pol.get("tags", []),
                            "content": pol.get("content", ""),
                            "is_product": False
                        })
            except Exception as e:
                print(f"[RAG] Error loading policies: {e}")

        print(f"[RAG] Indexed {len(self.chunks)} knowledge chunks.")

    def retrieve(self, query: str, top_k: int = 3) -> Tuple[List[Dict[str, Any]], str]:
        """Retrieves top_k relevant chunks using vector similarity."""
        ranked = self.local_index.search(query, top_k=top_k)
        retrieved = []
        for chunk, score in ranked:
            c = dict(chunk)
            c["score"] = round(score, 3)
            retrieved.append(c)
        return retrieved, "In-Memory Semantic TF-IDF Vector Index"

    def _call_groq(self, query: str, context_str: str, api_key: str) -> str:
        """Invokes Groq LLM API with customer support context and guardrails."""
        system_prompt = (
            "You are CALIX, the warm, polite, and friendly customer support assistant for CALIA, a modern lifestyle gadget store.\n\n"
            "CRITICAL INSTRUCTIONS & GUARDRAILS:\n"
            "1. CUSTOMER SERVICE PERSONA: Always speak directly to retail shoppers and customers in a warm, polite, helpful, and conversational customer-care tone. Use friendly formatting and pleasant emojis (✨, 🛍️, 📦, 🎧, etc.).\n"
            "2. STRICT CODING & OFF-TOPIC REFUSAL: If the user asks for ANY code, programming help, script writing, software engineering, technical algorithms, homework, or anything outside of shopping, gadgets, and customer support, you MUST POLITELY DECLINE. Remind them gently that you are CALIX, dedicated exclusively to assisting customers with CALIA's gadgets, product inquiries, orders, and store policies.\n"
            "3. RAG GROUNDING: Ground your answers strictly on the provided RETRIEVED KNOWLEDGE CONTEXT. When discussing gadgets, cite exact specs, battery life, and prices in ₹ (INR). If information is not in the context, politely state what you know or offer recommendations based on our catalog.\n"
            "4. STORE POLICIES & PROTOTYPE:\n"
            "   - Delivery is simulated 3-5 business days; free on orders over ₹999.\n"
            "   - Returns: 7-day return window for eligible unused items in original packaging.\n"
            "   - Damaged items: ask for demo Order ID (#CAL-XXXX) to initiate a simulated replacement.\n"
            "   - Duplicate charge: reassure customer and escalate to Human Billing Specialist Maya.\n"
            "   - Reminder: CALIA is a student prototype storefront so real payments or shipments are simulated.\n"
            "5. CONCISENESS: Keep answers concise (2 to 4 sentences or a neat bulleted list), natural, and focused on helping the customer."
        )

        user_content = f"RETRIEVED KNOWLEDGE CONTEXT:\n{context_str}\n\nCUSTOMER INQUIRY: {query}"
        
        models_to_try = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]
        for model in models_to_try:
            try:
                res = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_content}
                        ],
                        "temperature": 0.4,
                        "max_tokens": 400
                    },
                    timeout=15
                )
                if res.status_code == 200:
                    data = res.json()
                    content = data["choices"][0]["message"]["content"]
                    if content and content.strip():
                        return content.strip()
                else:
                    print(f"[RAG] Groq model {model} status {res.status_code}: {res.text}")
            except Exception as e:
                print(f"[RAG] Groq API call error with model {model}: {e}")

        return None

    def _call_gemini(self, query: str, context_str: str, api_key: str) -> str:
        """Fallback to Gemini API if a Gemini key was supplied."""
        system_instruction = (
            "You are CALIX, the warm, polite, and friendly customer support assistant for CALIA gadget store. "
            "Speak to customers in a warm, helpful customer-care tone. If the user asks for code or programming, "
            "politely decline and state you only help with CALIA products and shopping. Ground answers on the retrieved context."
        )
        try:
            endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
            r = requests.post(
                endpoint,
                params={"key": api_key},
                json={
                    "systemInstruction": {"parts": [{"text": system_instruction}]},
                    "contents": [{"role": "user", "parts": [{"text": f"RETRIEVED KNOWLEDGE CONTEXT:\n{context_str}\n\nCUSTOMER INQUIRY: {query}"}]}],
                    "generationConfig": {"maxOutputTokens": 350, "temperature": 0.4}
                },
                timeout=15
            )
            if r.status_code == 200:
                return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            print(f"[RAG] Gemini call error: {e}")
        return None

    def generate_response(self, query: str, top_k: int = 3, api_key: str = None) -> Dict[str, Any]:
        """Main RAG pipeline entry point."""
        effective_key = (api_key or DEFAULT_GROQ_KEY).strip()

        # Guardrail: Check for code or programming requests
        if is_code_or_programming_request(query):
            decline_message = (
                "I’m CALIX, your CALIA customer shopping & support buddy! ✨ "
                "I’m dedicated exclusively to helping customers with our gadgets, product specifications, "
                "orders, delivery, and store policies. I'm unable to write code, provide scripts, or assist "
                "with software development tasks. Please let me know if you have any questions about our "
                "products or your shopping experience! 🛍️"
            )
            return {
                "reply": decline_message,
                "sources": [],
                "retrieval_mode": "Guardrail Check",
                "generator": "CALIX Customer Safety Guardrail"
            }

        # 1. Retrieval step
        retrieved_chunks, mode_used = self.retrieve(query, top_k=top_k)

        # Build clean source references
        sources = [
            {
                "id": c.get("id"),
                "title": c.get("title"),
                "category": c.get("category"),
                "snippet": c.get("content")[:180] + "..." if len(c.get("content", "")) > 180 else c.get("content"),
                "score": c.get("score")
            }
            for c in retrieved_chunks if c.get("score", 0) > 0.04 or len(retrieved_chunks) == 1
        ]

        # Context block
        context_blocks = [f"[Document {i}: {c.get('title')} ({c.get('category')})]\n{c.get('content')}" for i, c in enumerate(retrieved_chunks, 1)]
        context_str = "\n\n".join(context_blocks)

        # 2. Augmented Generation via Groq or Gemini
        llm_reply = None
        generator_name = "Groq LLM (RAG Grounded)"

        if effective_key.startswith("gsk_"):
            llm_reply = self._call_groq(query, context_str, effective_key)
            generator_name = "Groq LLM (openai/gpt-oss-120b · RAG Grounded)"
        elif effective_key.startswith("AIza") or "gemini" in effective_key.lower():
            llm_reply = self._call_gemini(query, context_str, effective_key)
            generator_name = "Gemini 2.5 Flash (RAG Grounded)"
        else:
            # Try Groq first, then fallback
            llm_reply = self._call_groq(query, context_str, effective_key)
            if not llm_reply:
                llm_reply = self._call_gemini(query, context_str, effective_key)

        if llm_reply:
            return {
                "reply": llm_reply,
                "sources": sources,
                "retrieval_mode": mode_used,
                "generator": generator_name
            }

        # 3. Fallback to adaptive local synthesis if API call somehow failed
        return {
            "reply": "I apologize, but I had trouble reaching our AI service just now. Please ask again in a moment, or ask about our headphones, watches, speakers, or store return policy! ✨",
            "sources": sources,
            "retrieval_mode": mode_used,
            "generator": "CALIA Backup Handler"
        }
