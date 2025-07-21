import sys
print("Python executable:", sys.executable)
import os
print("Current working directory:", os.getcwd())
print("Script directory:", os.path.dirname(__file__))
print("Looking for .env at:", os.path.join(os.path.dirname(__file__), '.env'))
print("Files in script directory:", os.listdir(os.path.dirname(__file__)))
import json
from dotenv import load_dotenv
import openai
from fastapi import FastAPI, Body
from typing import List, Dict, Any
# Add ChromaDB imports
import chromadb
from chromadb.config import Settings

# Import the prompt builder from prompts.py
from prompts import build_effectiveness_report_prompt

# Load environment variables from .env
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
print("OPENAI_API_KEY loaded:", OPENAI_API_KEY)  # For debugging
openai.api_key = OPENAI_API_KEY

app = FastAPI()

# Function to call OpenAI for the overall effectiveness report
def analyze_effectiveness_report(campaigns, customer_name="[Customer Name]", period="[Q2 2025]"):
    prompt = build_effectiveness_report_prompt(campaigns, customer_name, period)
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000
    )
    content = response.choices[0].message.content
    if content is not None:
        return content.strip()
    else:
        print("Warning: OpenAI response content is None for effectiveness report")
        return ""

# Add this function to clean text for PDF
def clean_text_for_pdf(text):
    return (
        text.replace('“', '"')
            .replace('”', '"')
            .replace('‘', "'")
            .replace('’', "'")
            .replace('–', '-')
            .replace('—', '-')
            .replace('…', '...')
    )

@app.post("/analyze_campaigns")
def analyze_campaigns_api(campaigns: List[Dict[str, Any]] = Body(default=None), customer_name: str = "[Customer Name]", period: str = "[Q2 2025]"):
    """
    Generate a single AI Marketing Effectiveness Report for all campaigns together using OpenAI. If no campaigns are provided, load from ChromaDB.
    """
    print("Endpoint /analyze_campaigns called")
    if campaigns is None:
        print("No campaigns provided in request. Loading from ChromaDB.")
        CHROMA_DIR = '/Users/eshasetty/Documents/Niti AI/Apna_market/data/chromadb_apna_mart'
        client = chromadb.PersistentClient(path=CHROMA_DIR)
        collection = client.get_or_create_collection("campaigns")
        results = collection.get()
        campaigns = []
        for i in range(len(results['ids'])):
            metadata = results['metadatas'][i]
            full_campaign = json.loads(metadata['full_campaign_json'])
            campaigns.append(full_campaign)
        print(f"Loaded {len(campaigns)} campaigns from ChromaDB.")
    else:
        print(f"Received {len(campaigns)} campaigns in request.")

    print("Generating overall effectiveness report for all campaigns...")
    effectiveness_report = analyze_effectiveness_report(campaigns, customer_name, period)
    print("Effectiveness report generation complete.")

    # PDF generation removed

    return {
        "effectiveness_report": effectiveness_report
    } 