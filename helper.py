import os
import json
from dotenv import load_dotenv

def upload_to_chromadb(campaigns, chroma_dir, collection_name="campaigns"):
    try:
        import chromadb
        os.makedirs(chroma_dir, exist_ok=True)
        client = chromadb.PersistentClient(path=chroma_dir)
        collection = client.get_or_create_collection(collection_name)
        for campaign in campaigns:
            campaign_id = str(campaign.get("campaign_id"))
            name = campaign.get("name", "")
            ctype = campaign.get("type", "")
            text = f"{name} {ctype}"
            metadata = {
                "campaign_id": campaign_id,
                "name": name,
                "type": ctype,
                "full_campaign_json": json.dumps(campaign)
            }
            collection.add(
                documents=[text],
                metadatas=[metadata],
                ids=[campaign_id]
            )
        print(f"Uploaded {len(campaigns)} campaigns to ChromaDB at {chroma_dir}")
    except Exception as e:
        print(f"[ERROR] Failed to upload to ChromaDB: {e}")


def upload_to_supabase(campaigns, table_name, supabase_url=None, supabase_key=None):
    try:
        from supabase import create_client, Client
        load_dotenv()
        supabase_url = supabase_url or os.getenv('SUPABASE_URL')
        supabase_key = supabase_key or os.getenv('SUPABASE_KEY')
        if not supabase_url or not supabase_key:
            print("[ERROR] SUPABASE_URL or SUPABASE_KEY is missing from .env or arguments.")
            return
        supabase: Client = create_client(supabase_url, supabase_key)
        for campaign in campaigns:
            row = {
                'campaign_id': campaign.get('campaign_id'),
                'name': campaign.get('name'),
                'status': campaign.get('status'),
                'type': campaign.get('type'),
                'created_by': campaign.get('created_by'),
                'start_time': campaign.get('start_time'),
                'start_epoch': campaign.get('start_epoch'),
                'last_update': campaign.get('last_update'),
                'targeted_users': campaign.get('targeted_users'),
                'targeted_devices': campaign.get('targeted_devices'),
                'audience_segment_id': campaign.get('audience_segment_id'),
                'audience_location_filter': campaign.get('audience_location_filter'),
                'audience_activity_filter': campaign.get('audience_activity_filter'),
                'device_types': campaign.get('device_types'),
                'push_integration_details': campaign.get('push_integration_details'),
                'stats': campaign.get('stats'),
                'message_title': campaign.get('message_title'),
                'message_text': campaign.get('message_text'),
                'deep_link': campaign.get('deep_link'),
                'conv_goal_event_id': campaign.get('conv_goal_event_id'),
                'conv_goal_event_property': campaign.get('conv_goal_event_property'),
                'conv_goal_report_period': campaign.get('conv_goal_report_period'),
                'conv_goal_time_window': campaign.get('conv_goal_time_window'),
            }
            try:
                response = supabase.table(table_name).upsert(row, on_conflict='campaign_id').execute()
                print(f"Upserted campaign_id {row['campaign_id']}: {response}")
            except Exception as e:
                print(f"[ERROR] Failed to upsert campaign_id {row['campaign_id']}: {e}")
        print(f"Uploaded {len(campaigns)} campaigns to Supabase table {table_name}")
    except Exception as e:
        print(f"[ERROR] Failed to upload to Supabase: {e}") 