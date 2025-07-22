from nodes import load_campaigns_from_chromadb_node, upload_to_supabase_node, analyze_campaigns_node

def main():
    context = {}
    # Step 1: Load campaigns from ChromaDB
    context = load_campaigns_from_chromadb_node(context)
    # Step 2: (Optional) Upload to Supabase (currently commented out)
    # context = upload_to_supabase_node(context)
    print('[INFO] Skipping upload to Supabase.')
    # Step 3: Analyze campaigns
    context = analyze_campaigns_node(context)
    # Print the final analysis report
    print("\n=== Analysis Report ===\n")
    print(context.get('analysis_report'))

if __name__ == "__main__":
    main() 