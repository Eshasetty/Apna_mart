import json
import chromadb
import os

# Use the absolute path for campaign_details.json
DATA_PATH = '/Users/eshasetty/Documents/Niti AI/Apna_market/data/campaign_details.json'

# Load campaign details
with open(DATA_PATH, 'r', encoding='utf-8') as f:
    campaigns = json.load(f)

# Set the ChromaDB directory to the absolute path
CHROMA_DIR = '/Users/eshasetty/Documents/Niti AI/Apna_market/data/chromadb_apna_mart'
os.makedirs(CHROMA_DIR, exist_ok=True)
print(f"Saving ChromaDB data to: {CHROMA_DIR}")

# Initialize ChromaDB persistent client (new API)
client = chromadb.PersistentClient(path=CHROMA_DIR)

# Create or get the 'campaigns' collection
collection = client.get_or_create_collection("campaigns")

# Prepare and insert documents
for campaign in campaigns:
    campaign_id = str(campaign.get("campaign_id"))
    # Extract name and type for the document text
    target = campaign.get("data", {}).get("response", {}).get("target", {})
    name = target.get("name", "")
    ctype = target.get("type", "")
    text = f"{name} {ctype}"
    # Store flat fields and the full campaign as a JSON string
    metadata = {
        "campaign_id": campaign_id,
        "name": name,
        "type": ctype,
        "full_campaign_json": json.dumps(campaign)
    }
    # Insert into ChromaDB
    collection.add(
        documents=[text],
        metadatas=[metadata],
        ids=[campaign_id]
    )

print("All campaigns uploaded to ChromaDB!")
