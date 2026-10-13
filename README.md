# CALIA × CALIX AI starter

## Run it
1. Install Python 3.10 or newer.
2. Extract this ZIP and open the folder in VS Code.
3. In the VS Code terminal run:
   `python -m pip install -r requirements.txt`
   `python app.py`
4. Open http://127.0.0.1:5000

## Enable open-ended AI answers
The site works in demo-response mode without a key. For Gemini responses, get a Gemini API key through Google AI Studio. In Windows PowerShell, set it in the same terminal:
`$env:GEMINI_API_KEY="YOUR_KEY_HERE"`
Then run `python app.py`. Never paste the key into your source code or upload it to GitHub.

## Features
Pastel storefront, product photos/prices, search, category filters, add-to-cart and subtotal, CALIX chatbot drawer, browser speech recognition in supported Chrome browsers, spoken replies, Gemini API support, demo support flows for damaged products and duplicate-payment escalation to Maya.

This is a student prototype: checkout, order changes, refunds and replacements are simulated; no real transactions occur. Product photos and fonts need internet access.
