from helper import upload_to_chromadb, upload_to_supabase
import os
import json
import requests
from dotenv import load_dotenv
import openai
from prompts import build_effectiveness_report_prompt

def build_clevertap_query(params):
    q = {
        "stc": params.get("stc", 1),
        "searchKeyword": params.get("searchKeyword"),
        "archive": params.get("archive", False),
        "prefiltered": None,
        "purpose": 0,
        "channel": params.get("channel", []),
        "delivery": [],
        "campaign_type": params.get("campaign_type", []),
        "label": [],
        "created_by": [],
        "subChannel": [],
        "pageSize": params.get("pageSize", 15),
        "teamIds": [],
        "dateFrom": params.get("dateFrom", "20250701"),
        "dateTo": params.get("dateTo", "20250731")
    }
    q = {k: v for k, v in q.items() if v is not None}
    return json.dumps(q)

def get_clevertap_report_data_new_curl(_):
    load_dotenv()
    CLEVERTAP_CSRF_TOKEN = os.getenv('CLEVERTAP_CSRF_TOKEN')
    CLEVERTAP_COOKIE = os.getenv('CLEVERTAP_COOKIE')
    if not CLEVERTAP_CSRF_TOKEN or not CLEVERTAP_COOKIE:
        print("[ERROR] CLEVERTAP_CSRF_TOKEN or CLEVERTAP_COOKIE is missing from .env.")
        return None
    # Use the plain URL as in the browser example (update this to your actual working URL if needed)
    url = "https://eu1.dashboard.clevertap.com/8R9-6Z9-K46Z/json/report/load?q=%7B%22stc%22%3A1%2C%22searchKeyword%22%3Anull%2C%22archive%22%3Afalse%2C%22prefiltered%22%3Anull%2C%22purpose%22%3A0%2C%22channel%22%3A%5B%5D%2C%22delivery%22%3A%5B%5D%2C%22campaign_type%22%3A%5B%5D%2C%22label%22%3A%5B%5D%2C%22created_by%22%3A%5B%5D%2C%22subChannel%22%3A%5B%5D%2C%22pageSize%22%3A15%2C%22teamIds%22%3A%5B%5D%2C%22dateFrom%22%3A%2220250706%22%2C%22dateTo%22%3A%2220250805%22%7D&source=&limit=15&uc=1&requestTs=1753087700546"
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-US,en;q=0.9',
        'priority': 'u=1, i',
        'referer': 'https://eu1.dashboard.clevertap.com/8R9-6Z9-K46Z/campaigns',
        'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
        'x-clevertap-csrf-token': CLEVERTAP_CSRF_TOKEN,
        'x-newrelic-id': 'undefined',
        'Cookie': CLEVERTAP_COOKIE
    }
    print("[DEBUG] Outgoing CleverTap request:")
    print("URL:", url)
    print("Headers:", headers)
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Error retrieving data: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print("Error response content:", e.response.text)
        return None

def extract_campaign_ids(all_info):
    return [target['_id'] for target in all_info.get('targets', []) if '_id' in target]

def fetch_campaign_details(campaign_ids):
    load_dotenv()
    CLEVERTAP_DETAIL_CSRF_TOKEN = os.getenv('CLEVERTAP_DETAIL_CSRF_TOKEN')
    CLEVERTAP_DETAIL_COOKIE = os.getenv('CLEVERTAP_DETAIL_COOKIE')
    if not CLEVERTAP_DETAIL_CSRF_TOKEN or not CLEVERTAP_DETAIL_COOKIE:
        print("[ERROR] CLEVERTAP_DETAIL_CSRF_TOKEN or CLEVERTAP_DETAIL_COOKIE is missing from .env.")
        return []
    import time
    details_list = []
    for campaign_id in campaign_ids:
        campaign_id_str = str(campaign_id)
        detail_url = f"https://eu1.dashboard.clevertap.com/8R9-6Z9-K46Z/json/targets/{campaign_id_str}/get?from=0&to=0&uc=1&requestTs=1753089424709"
        detail_headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.9',
            'priority': 'u=1, i',
            'referer': f'https://eu1.dashboard.clevertap.com/8R9-6Z9-K46Z/campaigns/campaign/{campaign_id_str}/report/stats/trend',
            'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
            'x-clevertap-csrf-token': CLEVERTAP_DETAIL_CSRF_TOKEN,
            'x-newrelic-id': 'undefined',
            'Cookie': CLEVERTAP_DETAIL_COOKIE
        }
        try:
            resp = requests.get(detail_url, headers=detail_headers)
            resp.raise_for_status()
            details_list.append({"campaign_id": campaign_id, "data": resp.json()})
            print(f"Fetched details for campaign ID {campaign_id}")
        except Exception as e:
            print(f"[ERROR] Error fetching details for campaign ID {campaign_id}: {e}")
            details_list.append({"campaign_id": campaign_id, "error": str(e)})
        time.sleep(0.2)
    return details_list

def extract_relevant_campaign_info(details_list):
    relevant_list = []
    for entry in details_list:
        campaign_id = entry.get('campaign_id')
        data = entry.get('data', {})
        response = data.get('response', {})
        target = response.get('target', {})
        name = target.get('name')
        status = target.get('status')
        ctype = target.get('type')
        created_by = target.get('c-by')
        start_time = target.get('startTime')
        start_epoch = target.get('startEpoch', target.get('epoch_time'))
        last_update = target.get('lastUpdate', target.get('updated_ts'))
        q_user_device_counts = target.get('q_user_device_counts', {})
        targeted_users = q_user_device_counts.get('users')
        targeted_devices = q_user_device_counts.get('devices')
        seg_id = None
        location_filter = None
        activity_filter = None
        try:
            seg_id = target['q']['wc']['arr'][0]['arr'][1]['sx']['meta_for_ui']['segIds']
        except Exception:
            pass
        try:
            location_filter = target['q']['wc']['arr'][0]['arr'][0]['e'][0]['v']
        except Exception:
            pass
        try:
            activity_filter = target['q']['wc']['arr'][0]['arr'][0]['formattedDateOutput']
        except Exception:
            pass
        device_types = target.get('deviceTypes')
        push_integration_details = target.get('meta', {}).get('pushIntegrationDetails')
        stats = target.get('stats', {})
        stats_summary = {}
        for date_key, date_stats in stats.items():
            stats_summary[date_key] = {}
            for device_key in ['1', '2']:
                device_stats = date_stats.get(device_key, {}).get('wzrk_default', {})
                stats_summary[date_key][device_key] = {
                    'sent': device_stats.get('sent'),
                    'impressions': device_stats.get('impressions'),
                    'clicked': device_stats.get('clicked'),
                    'errors': device_stats.get('errors')
                }
        content = target.get('content', {})
        message_title = {}
        message_text = {}
        deep_link = {}
        for device_key in content:
            msg = content[device_key].get('msg', {}).get('wzrk_default', {})
            message_title[device_key] = msg.get('title')
            message_text[device_key] = msg.get('text')
            deep_link[device_key] = content[device_key].get('kv', {}).get('wzrk_dl')
        conv_goal = target.get('convGoal', {})
        cq = conv_goal.get('cq', {})
        conv_goal_event_id = cq.get('ev')
        conv_goal_event_property = None
        try:
            conv_goal_event_property = cq['e'][0]['v'][0]
        except Exception:
            pass
        conv_goal_report_period = conv_goal.get('rp')
        conv_goal_time_window = conv_goal.get('ct')
        relevant = {
            'campaign_id': campaign_id,
            'name': name,
            'status': status,
            'type': ctype,
            'created_by': created_by,
            'start_time': start_time,
            'start_epoch': start_epoch,
            'last_update': last_update,
            'targeted_users': targeted_users,
            'targeted_devices': targeted_devices,
            'audience_segment_id': seg_id,
            'audience_location_filter': location_filter,
            'audience_activity_filter': activity_filter,
            'device_types': device_types,
            'push_integration_details': push_integration_details,
            'stats': stats_summary,
            'message_title': message_title,
            'message_text': message_text,
            'deep_link': deep_link,
            'conv_goal_event_id': conv_goal_event_id,
            'conv_goal_event_property': conv_goal_event_property,
            'conv_goal_report_period': conv_goal_report_period,
            'conv_goal_time_window': conv_goal_time_window
        }
        relevant_list.append(relevant)
    return relevant_list

def gather_info_node(context):
    try:
        all_info = get_clevertap_report_data_new_curl({})
        if not all_info:
            raise RuntimeError("No data retrieved or an error occurred during the API call.")
        campaign_ids = extract_campaign_ids(all_info)
        details_list = fetch_campaign_details(campaign_ids)
        relevant_list = extract_relevant_campaign_info(details_list)
        context['campaigns'] = relevant_list
    except Exception as e:
        print(f"[ERROR] gather_info_node failed: {e}")
        context['campaigns'] = []
    return context

def upload_to_chromadb_node(context):
    try:
        chroma_dir = os.path.join('data', 'chromadb_apna_mart')
        upload_to_chromadb(context['campaigns'], chroma_dir)
    except Exception as e:
        print(f"[ERROR] upload_to_chromadb_node failed: {e}")
    return context

def upload_to_supabase_node(context):
    try:
        table_name = 'apna_mart'
        upload_to_supabase(context['campaigns'], table_name)
    except Exception as e:
        print(f"[ERROR] upload_to_supabase_node failed: {e}")
    return context

def analyze_campaigns_node(context):
    try:
        load_dotenv()
        OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
        if not OPENAI_API_KEY:
            print("[ERROR] OPENAI_API_KEY is missing from .env.")
            context['analysis_report'] = "[ERROR] OPENAI_API_KEY is missing from .env."
            return context
        openai.api_key = OPENAI_API_KEY
        campaigns = context.get('campaigns', [])
        report = analyze_effectiveness_report(campaigns)
        context['analysis_report'] = report
    except Exception as e:
        print(f"[ERROR] analyze_campaigns_node failed: {e}")
        context['analysis_report'] = f"[ERROR] {e}"
    return context

def analyze_effectiveness_report(campaigns, customer_name="[Customer Name]", period="[Q2 2025]"):
    prompt = build_effectiveness_report_prompt(campaigns, customer_name, period)
    try:
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
    except Exception as e:
        print(f"[ERROR] OpenAI API call failed: {e}")
        return f"[ERROR] OpenAI API call failed: {e}" 

def load_campaigns_from_chromadb_node(context):
    import chromadb
    chroma_dir = '/Users/eshasetty/Documents/Niti AI/Apna_market/data/chromadb_apna_mart'
    client = chromadb.PersistentClient(path=chroma_dir)
    collection = client.get_or_create_collection("campaigns")
    results = collection.get()
    campaigns = []
    for i in range(len(results['ids'])):
        metadata = results['metadatas'][i]
        full_campaign = json.loads(metadata['full_campaign_json'])
        campaigns.append(full_campaign)
    context['campaigns'] = campaigns
    print(f'[INFO] Loaded {len(campaigns)} campaigns from ChromaDB.')
    return context 

def fetch_and_upload_clevertap_node(context):
    """
    Fetch campaign data directly from CleverTap and upload to Supabase.
    """
    try:
        # Step 1: Fetch all campaign info from CleverTap
        all_info = get_clevertap_report_data_new_curl({})
        if not all_info:
            print("[ERROR] No data retrieved from CleverTap.")
            return context
        campaign_ids = extract_campaign_ids(all_info)
        details_list = fetch_campaign_details(campaign_ids)
        relevant_list = extract_relevant_campaign_info(details_list)
        context['campaigns'] = relevant_list

        # Step 2: Upload to Supabase
        from helper import upload_to_supabase
        table_name = 'apna_mart'
        upload_to_supabase(relevant_list, table_name)
        print(f"[INFO] Uploaded {len(relevant_list)} campaigns from CleverTap to Supabase.")

    except Exception as e:
        print(f"[ERROR] fetch_and_upload_clevertap_node failed: {e}")
    return context 