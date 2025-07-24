from nodes import load_campaigns_from_chromadb_node, upload_to_supabase_node, analyze_campaigns_node, fetch_and_upload_clevertap_node, fetch_and_save_all_journey_details_node
import json

def main():
    context = {}
    # Step 0: Fetch and save all journey details from CleverTap
    context = fetch_and_save_all_journey_details_node(context)
    # Step 0: Fetch from CleverTap and upload to Supabase
    context = fetch_and_upload_clevertap_node(context)
    # Step 1: Load campaigns from ChromaDB
    # context = load_campaigns_from_chromadb_node(context)
    # Step 2: Upload to Supabase (optional, but kept for compatibility)
    # context = upload_to_supabase_node(context)
    # Instead, load campaigns from the provided JSON file
    with open('/Users/eshasetty/Documents/Niti AI/Apna_market/data/campaign_relevant_information.json', 'r') as f:
        campaigns = json.load(f)
    context['campaigns'] = campaigns
    # Step 3: Analyze campaigns
    context = analyze_campaigns_node(context)
    # Print the final analysis report
    print("\n=== Analysis Report ===\n")
    print(context.get('analysis_report'))

if __name__ == "__main__":
    main() 