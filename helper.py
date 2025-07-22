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
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        if not supabase_url or not supabase_key:
            print("[ERROR] SUPABASE_URL or SUPABASE_KEY is missing from .env.")
            return
        supabase: Client = create_client(supabase_url, supabase_key)
        for campaign in campaigns:
            row = {
                'campaign_id': campaign.get('campaign_id'),
                'campaign_name': campaign.get('name'),
                'status': campaign.get('status'),
                'type': campaign.get('type'),
                'start_time': campaign.get('start_time'),
                'start_epoch': campaign.get('start_epoch'),
                'created_by': campaign.get('created_by'),
                'last_updated': campaign.get('last_update'),
                'sent_android': campaign.get('stats', {}).get('sent_android'),
                'impressions_android': campaign.get('stats', {}).get('impressions_android'),
                'clicks_android': campaign.get('stats', {}).get('clicks_android'),
                'sent_ios': campaign.get('stats', {}).get('sent_ios'),
                'impressions_ios': campaign.get('stats', {}).get('impressions_ios'),
                'clicks_ios': campaign.get('stats', {}).get('clicks_ios'),
                'total_sent': campaign.get('stats', {}).get('total_sent'),
                'total_impressions': campaign.get('stats', {}).get('total_impressions'),
                'total_clicks': campaign.get('stats', {}).get('total_clicks'),
                'ctr': campaign.get('stats', {}).get('ctr'),
                'title': campaign.get('message_title', {}).get('1') or campaign.get('message_title', {}).get('2'),
                'message': campaign.get('message_text', {}).get('1') or campaign.get('message_text', {}).get('2'),
                'cta_url': campaign.get('deep_link', {}).get('1') or campaign.get('deep_link', {}).get('2'),
                'image_url': campaign.get('image_url'),
                'segment_name': campaign.get('segment_name'),
                'region': campaign.get('audience_location_filter'),
                'segment_id': campaign.get('audience_segment_id'),
                'device_android': '1' in (campaign.get('device_types') or []),
                'device_ios': '2' in (campaign.get('device_types') or []),
                'device_web': '3' in (campaign.get('device_types') or []),
                'throttling_enabled': campaign.get('throttling_enabled'),
                'throttle_limit': campaign.get('throttle_limit'),
                'tr_cap': campaign.get('tr_cap'),
                'push_amplified': campaign.get('push_amplified'),
                'errors_android': json.dumps(campaign.get('stats', {}).get('errors_android')) if campaign.get('stats', {}).get('errors_android') is not None else None,
                'errors_ios': json.dumps(campaign.get('stats', {}).get('errors_ios')) if campaign.get('stats', {}).get('errors_ios') is not None else None,
                'raw_json': json.dumps(campaign),
            }
            try:
                response = supabase.table(table_name).upsert(row, on_conflict='campaign_id').execute()
                print(f"Upserted campaign_id {row['campaign_id']}: {response}")
            except Exception as e:
                print(f"[ERROR] Failed to upsert campaign_id {row['campaign_id']}: {e}")
        print(f"Uploaded {len(campaigns)} campaigns to Supabase table {table_name}")
    except Exception as e:
        print(f"[ERROR] Failed to upload to Supabase: {e}") 