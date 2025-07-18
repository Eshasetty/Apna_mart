import requests
import json
import os
from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse
from typing import Dict, Any
from dotenv import load_dotenv
from urllib.parse import quote

# Load environment variables from .env
load_dotenv()
CLEVERTAP_CSRF_TOKEN = os.getenv('CLEVERTAP_CSRF_TOKEN_JOURNEYS')
CLEVERTAP_COOKIE = os.getenv('CLEVERTAP_COOKIE_JOURNEYS')
CLEVERTAP_DETAIL_CSRF_TOKEN = os.getenv('CLEVERTAP_DETAIL_CSRF_TOKEN_JOURNEYS')
CLEVERTAP_DETAIL_COOKIE = os.getenv('CLEVERTAP_DETAIL_COOKIE_JOURNEYS')

app = FastAPI()

def build_clevertap_query(params: Dict[str, Any]) -> str:
    """
    Build the 'q' parameter for the CleverTap API URL from the provided filters.
    """
    # Default values
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
    # Remove None values
    q = {k: v for k, v in q.items() if v is not None}
    return json.dumps(q)

def get_clevertap_report_data_new_curl(filters: Dict[str, Any]):
    """
    Retrieves report data from the CleverTap API using the provided filters.
    """
    q_param = build_clevertap_query(filters)
    url = f'https://eu1.dashboard.clevertap.com/8R9-6Z9-K46Z/json/targeting/journeys/load?q={quote(q_param)}'
    # Add other params to the URL if present
    url_params = []
    for key in ["source", "limit", "uc", "requestTs"]:
        if key in filters:
            url_params.append(f"{key}={filters[key]}")
    if url_params:
        url += "&" + "&".join(url_params)

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
        'x-clevertap-csrf-token': CLEVERTAP_CSRF_TOKEN,  # Loaded from .env
        'x-newrelic-id': 'undefined',
        'Cookie': CLEVERTAP_COOKIE  # Loaded from .env
    }

    try:
        response = requests.get(url, headers=headers)
        print(f"HTTP Status Code: {response.status_code}")
        print("Response content:", response.text)  # Print the full response for debugging
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving data: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print("Error response content:", e.response.text)
        return None

def extract_campaign_ids(all_info):
    """
    Extracts campaign IDs from the report data.
    """
    return [target['_id'] for target in all_info.get('targets', []) if '_id' in target]

def fetch_campaign_details(campaign_ids):
    """
    Fetches detailed information for a list of campaign IDs.
    """
    import time
    details_list = []
    for campaign_id in campaign_ids:
        campaign_id_str = str(campaign_id)
        detail_url = f"https://eu1.dashboard.clevertap.com/8R9-6Z9-K46Z/json/targets/{campaign_id_str}/get?from=0&to=0&uc=1&requestTs=1752643419854"
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
            'x-clevertap-csrf-token': CLEVERTAP_DETAIL_CSRF_TOKEN,  # Loaded from .env
            'x-newrelic-id': 'undefined',
            'Cookie': CLEVERTAP_DETAIL_COOKIE  # Loaded from .env
        }
        try:
            resp = requests.get(detail_url, headers=detail_headers)
            resp.raise_for_status()
            details_list.append({"campaign_id": campaign_id, "data": resp.json()})
            print(f"Fetched details for campaign ID {campaign_id}")
        except Exception as e:
            print(f"Error fetching details for campaign ID {campaign_id}: {e}")
            details_list.append({"campaign_id": campaign_id, "error": str(e)})
        time.sleep(0.2)  # Be polite to the server
    return details_list

def extract_relevant_campaign_info(details_list):
    """
    Extracts relevant campaign information from the detailed campaign data.
    """
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

def filter_campaigns(relevant_list, filters: Dict[str, Any]):
    """
    Filters the list of relevant campaigns based on the provided filters.
    """
    def matches(campaign):
        for key, value in filters.items():
            field = campaign.get(key)
            if isinstance(field, list):
                if value not in field:
                    return False
            elif isinstance(field, dict):
                if value not in field.values():
                    return False
            else:
                if field != value:
                    return False
        return True
    return [c for c in relevant_list if matches(c)]

@app.post("/process_campaigns")
def process_campaigns(filters: Dict[str, Any] = Body(default={})):  # filters is a dict of key: value
    """
    Processes the full pipeline: fetch report, extract IDs, fetch details, extract relevant info, and filter.
    The filters dict is used to build the CleverTap API query and URL.
    """
    # Step 1: Fetch report data with filters
    all_info = get_clevertap_report_data_new_curl(filters)
    if not all_info:
        return JSONResponse(status_code=500, content={"error": "No data retrieved or an error occurred during the API call."})
    # Step 2: Extract campaign IDs
    campaign_ids = extract_campaign_ids(all_info)
    # Step 3: Fetch campaign details
    details_list = fetch_campaign_details(campaign_ids)
    # Step 4: Extract relevant campaign info
    relevant_list = extract_relevant_campaign_info(details_list)
    # Step 5: (No further filtering needed, already filtered at API call)
    return {"filtered_campaigns": relevant_list, "count": len(relevant_list)} 