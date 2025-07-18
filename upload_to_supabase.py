import os
import json
from supabase import create_client, Client

# --- CONFIGURATION ---
# You can set these as environment variables or hardcode them here
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://kdhirxaoipvhotuxfglw.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtkaGlyeGFvaXB2aG90dXhmZ2x3Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0Nzg5OTYzMSwiZXhwIjoyMDYzNDc1NjMxfQ.0Mw33CprZFJQCwDE1S4MEeb-2O96o5-HIV-8Bx8Cm-U')
TABLE_NAME = 'apna_mart'
DATA_PATH = os.path.join('data', 'campaign_relevant_information.json')

# --- CONNECT TO SUPABASE ---
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- LOAD CAMPAIGN DATA ---
with open(DATA_PATH, 'r', encoding='utf-8') as f:
    campaigns = json.load(f)

# --- UPLOAD TO SUPABASE ---
for campaign in campaigns:
    # Prepare the row to match the table schema
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
    # Upsert (insert or update) by campaign_id
    response = supabase.table(TABLE_NAME).upsert(row, on_conflict='campaign_id').execute()
    print(f"Upserted campaign_id {row['campaign_id']}: {response}")

print("All campaigns uploaded to Supabase.") 