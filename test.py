import chromadb

CHROMA_DIR = '/Users/eshasetty/Documents/Niti AI/Apna_market/data/chromadb_apna_mart'
client = chromadb.PersistentClient(path=CHROMA_DIR)
collection = client.get_or_create_collection("campaigns")
results = collection.get()
print("Number of campaigns found:", len(results['ids']))
for i, id in enumerate(results['ids']):
    print(f"Campaign {i+1} ID:", id)