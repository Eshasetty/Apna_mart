from helper import upload_to_chromadb, upload_to_supabase
import os
import json
import requests
from dotenv import load_dotenv
import openai
from prompts import build_effectiveness_report_prompt
from urllib.parse import quote

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
    url = "https://eu1.dashboard.clevertap.com/8R9-6Z9-K46Z/json/report/load?q=%7B%22stc%22%3A1%2C%22searchKeyword%22%3Anull%2C%22archive%22%3Afalse%2C%22prefiltered%22%3Anull%2C%22purpose%22%3A0%2C%22channel%22%3A%5B%5D%2C%22delivery%22%3A%5B%5D%2C%22campaign_type%22%3A%5B%5D%2C%22label%22%3A%5B%5D%2C%22created_by%22%3A%5B%5D%2C%22subChannel%22%3A%5B%5D%2C%22pageSize%22%3A30%2C%22teamIds%22%3A%5B%5D%2C%22dateFrom%22%3A%2220250701%22%2C%22dateTo%22%3A%2220250801%22%2C%22pageNumber%22%3A1%2C%22status%22%3A%5B1%2C3%5D%7D&source=&limit=30&uc=1&requestTs=1753339184653"
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
        detail_url = f"https://eu1.dashboard.clevertap.com/8R9-6Z9-K46Z/json/targets/{campaign_id_str}/get?from=0&to=0&uc=1&requestTs=1753337727262"
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
    Stores the fetched campaigns in context['campaigns'] and uploads to apna_mart.
    Also saves all campaign details to campaign_details.json (overwriting if exists),
    then fetches and saves all journey details by calling fetch_and_save_all_journey_details_node.
    """
    import os
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

        # Save all campaign details to campaign_details.json (always overwrite)
        details_path = "campaign_details.json"
        with open(details_path, "w") as f:
            json.dump(details_list, f, indent=2)
        print(f"[INFO] Saved all campaign details to {details_path}")

        # Step 1.5: Fetch and save all journey details right after campaign details
        context = fetch_and_save_all_journey_details_node(context)

        # Step 2: Upload to Supabase
        from helper import upload_to_supabase
        table_name = 'apna_mart'
        upload_to_supabase(relevant_list, table_name)
        print(f"[INFO] Uploaded {len(relevant_list)} campaigns from CleverTap to Supabase.")

    except Exception as e:
        print(f"[ERROR] fetch_and_upload_clevertap_node failed: {e}")
    return context

def fetch_and_save_all_journey_details_node(context, output_path="journey_details.json"):
    """
    Fetch all journeys from CleverTap, then fetch details for each journey, and save to a JSON file.
    """
    print("[DEBUG] Starting CleverTap journey fetch...")
    journey_cookie = "amp_b93379=TCXB6zPtgCmwLzJ58nk3KU...1j06ctiqa.1j06cu2b5.0.0.0; _hjSessionUser_3019028=eyJpZCI6IjBhZjI4NTg4LWEwN2EtNWU3YS1hMmQ3LWYwZTljODNmZDAwNyIsImNyZWF0ZWQiOjE3NTI1NjE1MzY5MzIsImV4aXN0aW5nIjp0cnVlfQ==; G_ENABLED_IDPS=google; wzrk_lcbid=887; agl=true; _hjSessionUser_2030532=eyJpZCI6IjhhNjA1N2NlLThkYzQtNTQyNS05YjY1LTc0NzAwNTc0ZGU4MyIsImNyZWF0ZWQiOjE3NTI1NjE2Njc5ODQsImV4aXN0aW5nIjp0cnVlfQ==; _ga_T5SN9P2G3E=GS2.1.s1752561535$o1$g1$t1752562669$j60$l0$h0; _gcl_au=1.1.119355679.1752812825; _rdt_uuid=1752812825005.8b75d8b4-b357-4163-934e-e3c99dce4024; _fbp=fb.1.1752812825070.75006655946801814; _ga=GA1.1.1422481215.1752561536; cebs=1; _uetvid=7591e810638f11f0af5509da5380fd16; _CEFT=Q%3D%3D%3D; cebsp_=1; _fuid=YTBhNmM4MzctMzhjYS00ZjFjLThiZDItNzE4NmY0ZTQ1YWYx; __hstc=96753472.04dbb16b3c22dbe8b862e970ecc71d26.1752812826041.1752812826041.1752812826041.1; hubspotutk=04dbb16b3c22dbe8b862e970ecc71d26; __hssrc=1; _ga_DWXHXRB157=GS2.1.s1752812825$o1$g1$t1752815980$j60$l0$h688601250; _ce.s=v~47acb173a0d096abf38d4b7b2f46232ae76daf94~lcw~1752817804467~vir~new~lva~1752812825155~vpv~0~v11.cs~290064~v11.s~75a24f90-638f-11f0-9434-034cbf24145d~v11.vs~47acb173a0d096abf38d4b7b2f46232ae76daf94~v11.fsvd~eyJ1cmwiOiJjbGV2ZXJ0YXAuY29tIiwicmVmIjoiIiwidXRtIjpbXX0%3D~v11.sla~1752812825354~v11.ss~1752812825355~v11ls~75a24f90-638f-11f0-9434-034cbf24145d~gtrk.la~md8egptg~lcw~1752817804468; eventsListTs=; WZRK_G=e77071dcefd943e68aa0dd7613625bac; segmentListTs=1753324395195; _hjUserAttributesHash=918df2ffe7447208a544a9910ee3fb53; JSESSIONID=node01xokjersjodpc17laklnn07rn1600.node0; wzrk_lc=01303a316d01443fb4d9c9bcea3baf6217545502148871753340614esha@niti.ai; _hjSession_2030532=eyJpZCI6ImNjNDk5NzU1LWEyYjMtNDEwZi04ZWFkLWQzNjdlOGMyMGRlNSIsImMiOjE3NTMzNDA3MDQyODcsInMiOjEsInIiOjEsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjowLCJzcCI6MH0=; WSESSIONID=UhuJgXS0pZvCJwc9CDSZyLASynvNSeFVOspBq80P3KtqOhuywbhTG2soekXi8IDQFlXnWCcl26wnZouUYFbt%Df260BKPfb7Pf4XlaQTtKw6S8LZC2T7GMkisOk%Cg388DU0; secret_csrf=3ab17fb9-11e2-475e-819e-bc72d138db01; csrf=1290004177; _hjHasCachedUserAttributes=true; WZRK_S_R74-ZWR-R44Z=%7B%22s%22%3A1753340704%2C%22t%22%3A1753340978%2C%22p%22%3A2%7D; AWSALB=6ws5s1fv5m73Y0h7AD+hk14j8HDvM6N4kmrgZ2zUW2F38LuBor0Dr8Yf8TvUQhH4E8y2sOOVmsXd0wCr7AbVBcNlbtMW+bkSJJNTwjMQxed2VMkfpjm9tULnVjwg; AWSALBCORS=6ws5s1fv5m73Y0h7AD+hk14j8HDvM6N4kmrgZ2zUW2F38LuBor0Dr8Yf8TvUQhH4E8y2sOOVmsXd0wCr7AbVBcNlbtMW+bkSJJNTwjMQxed2VMkfpjm9tULnVjwg"
    
    # Extract CSRF token from cookie
    csrf_token = None
    if 'csrf=' in journey_cookie:
        csrf_token = journey_cookie.split('csrf=')[1].split(';')[0]
    else:
        csrf_token = "your_fallback_csrf_token"
    print(f"[DEBUG] Using CSRF token: {csrf_token}")

    # 1. Fetch all journeys (targets) - match the working curl exactly
    import time
    request_ts = int(time.time() * 1000)
    url = f"https://eu1.dashboard.clevertap.com/8R9-6Z9-K46Z/json/targeting/journeys/load?q=%7B%22pageNumber%22%3A2%2C%22prefiltered%22%3Anull%2C%22searchKeyword%22%3Anull%2C%22sortField%22%3A%22updated_ts%22%2C%22sortOrder%22%3A-1%2C%22stc%22%3A1%2C%22dateFrom%22%3A%2220250709%22%2C%22dateTo%22%3A%2220250808%22%2C%22pageSize%22%3A20%2C%22delivery%22%3A%5B%5D%2C%22status%22%3A%5B1%2C3%5D%2C%22label%22%3A%5B%5D%2C%22created_by%22%3A%5B%5D%2C%22journeyIds%22%3A%5B285%2C288%2C290%2C276%2C272%2C271%2C243%2C242%2C237%2C236%2C209%2C191%2C190%2C189%2C186%2C180%2C179%2C168%2C164%2C157%5D%7D&uc=1&requestTs=1753342964163"
    print(f"[DEBUG] Target URL: {url}")

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9",
        "priority": "u=1, i",
        "referer": "https://eu1.dashboard.clevertap.com/8R9-6Z9-K46Z/journeys",
        "sec-ch-ua": '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        "x-clevertap-csrf-token": "-2145462265",
        "x-newrelic-id": "undefined",
        "Cookie": "amp_b93379=TCXB6zPtgCmwLzJ58nk3KU...1j06ctiqa.1j06cu2b5.0.0.0; _hjSessionUser_3019028=eyJpZCI6IjBhZjI4NTg4LWEwN2EtNWU3YS1hMmQ3LWYwZTljODNmZDAwNyIsImNyZWF0ZWQiOjE3NTI1NjE1MzY5MzIsImV4aXN0aW5nIjp0cnVlfQ==; G_ENABLED_IDPS=google; wzrk_lcbid=887; agl=true; _hjSessionUser_2030532=eyJpZCI6IjhhNjA1N2NlLThkYzQtNTQyNS05YjY1LTc0NzAwNTc0ZGU4MyIsImNyZWF0ZWQiOjE3NTI1NjE2Njc5ODQsImV4aXN0aW5nIjp0cnVlfQ==; _ga_T5SN9P2G3E=GS2.1.s1752561535$o1$g1$t1752562669$j60$l0$h0; _gcl_au=1.1.119355679.1752812825; _rdt_uuid=1752812825005.8b75d8b4-b357-4163-934e-e3c99dce4024; _fbp=fb.1.1752812825070.75006655946801814; _ga=GA1.1.1422481215.1752561536; cebs=1; _uetvid=7591e810638f11f0af5509da5380fd16; _CEFT=Q%3D%3D%3D; cebsp_=1; _fuid=YTBhNmM4MzctMzhjYS00ZjFjLThiZDItNzE4NmY0ZTQ1YWYx; __hstc=96753472.04dbb16b3c22dbe8b862e970ecc71d26.1752812826041.1752812826041.1752812826041.1; hubspotutk=04dbb16b3c22dbe8b862e970ecc71d26; __hssrc=1; _ga_DWXHXRB157=GS2.1.s1752812825$o1$g1$t1752815980$j60$l0$h688601250; _ce.s=v~47acb173a0d096abf38d4b7b2f46232ae76daf94~lcw~1752817804467~vir~new~lva~1752812825155~vpv~0~v11.cs~290064~v11.s~75a24f90-638f-11f0-9434-034cbf24145d~v11.vs~47acb173a0d096abf38d4b7b2f46232ae76daf94~v11.fsvd~eyJ1cmwiOiJjbGV2ZXJ0YXAuY29tIiwicmVmIjoiIiwidXRtIjpbXX0%3D~v11.sla~1752812825354~v11.ss~1752812825355~v11ls~75a24f90-638f-11f0-9434-034cbf24145d~gtrk.la~md8egptg~lcw~1752817804468; eventsListTs=; WZRK_G=e77071dcefd943e68aa0dd7613625bac; segmentListTs=1753324395195; _hjUserAttributesHash=918df2ffe7447208a544a9910ee3fb53; JSESSIONID=node01xokjersjodpc17laklnn07rn1600.node0; wzrk_lc=01303a316d01443fb4d9c9bcea3baf6217545502148871753340614esha@niti.ai; _hjSession_2030532=eyJpZCI6IjdiMzY1ZjNjLWUxMTgtNDU3Ni1iODNhLWQyZjJkZjU3NmI2YSIsImMiOjE3NTMzNDI3NDU0MzEsInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjEsImZzIjowLCJzcCI6MX0=; secret_csrf=1a7d2632-ee3d-45a5-988a-c6153103a6db; csrf=-2145462265; _hjHasCachedUserAttributes=true; WZRK_S_R74-ZWR-R44Z=%7B%22s%22%3A1753342756%2C%22t%22%3A1753342943%2C%22p%22%3A1%7D; WSESSIONID=Hoy3RKGURjZSoyCNH6GdaWHhMXpB88g2PuV9b5RtslpyEgTtoQXFBiBlfnqmmfH0i6or7nsT4MCPlxy95Aim5vKAPHso8eFdAnwmmQKUC49ETUGa9mo0T%xj3YqD1G; AWSALB=GCCTiL3mVC4W5fHmf5cyH/3SBt2MX7v+lANPRCOVuKpAdwCoBiH7znx/UsjliJT62rz3LuOZYW6R6mbhkrqnNQYN7ePA2bi8/zF/f+d5CZvtSC6trnotTQM7d1TO; AWSALBCORS=GCCTiL3mVC4W5fHmf5cyH/3SBt2MX7v+lANPRCOVuKpAdwCoBiH7znx/UsjliJT62rz3LuOZYW6R6mbhkrqnNQYN7ePA2bi8/zF/f+d5CZvtSC6trnotTQM7d1TO"
    }

    print(f"[DEBUG] Headers configured:")
    for key, value in headers.items():
        if key == "Cookie":
            print(f"[DEBUG]   {key}: {value[:100]}...{value[-50:] if len(value) > 150 else ''}")
        else:
            print(f"[DEBUG]   {key}: {value}")

    print(f"[DEBUG] Making GET request...")

    try:
        resp = requests.get(url, headers=headers, cookies=None)
        print(f"[DEBUG] ✓ Request completed!")
        print(f"[DEBUG] HTTP Status Code: {resp.status_code}")
        print(f"[DEBUG] Response headers: {dict(resp.headers)}")
        response_preview = resp.text[:500] + "..." if len(resp.text) > 500 else resp.text
        print(f"[DEBUG] Response content preview: {response_preview}")
        print(f"[DEBUG] Full response length: {len(resp.text)} characters")
        resp.raise_for_status()
        journeys_data = resp.json()
        print(f"[DEBUG] ✓ Successfully parsed JSON response")
        print(f"[DEBUG] JSON keys: {list(journeys_data.keys())}")
    except Exception as e:
        print(f"[ERROR] ✗ Request failed: {e}")
        return context

    # 2. Extract journey IDs from 'journeyStats'
    print("[DEBUG] =====================================")
    print("[DEBUG] Step 2: Parsing journey data...")
    print("[DEBUG] =====================================")

    journey_ids = []
    journey_stats = journeys_data.get("journeyStats")

    if journey_stats is None:
        print("[ERROR] ✗ 'journeyStats' key not found in response!")
        print("[ERROR] Available keys in response:", list(journeys_data.keys()))
        print("[ERROR] Full response for debugging:")
        print(json.dumps(journeys_data, indent=2))
        print("[ERROR] This suggests the API returned an error or unexpected format")
        return context
    else:
        print(f"[DEBUG] ✓ Found 'journeyStats' key in response")
        print(f"[DEBUG] journeyStats type: {type(journey_stats)}")
        print(f"[DEBUG] journeyStats length: {len(journey_stats) if isinstance(journey_stats, dict) else 'Not a dict'}")

        if isinstance(journey_stats, dict) and len(journey_stats) > 0:
            sample_key = next(iter(journey_stats))
            print(f"[DEBUG] Sample journey ID: {sample_key}, keys: {list(journey_stats[sample_key].keys()) if journey_stats[sample_key] else 'Empty journey'}")

        for i, (jid, journey) in enumerate(journey_stats.items()):
            journey_ids.append(jid)
            print(f"[DEBUG] Journey {i+1}: ID={jid}")

        print(f"[DEBUG] ✓ Extracted {len(journey_ids)} journey IDs: {journey_ids}")

        if len(journey_ids) == 0:
            print("[WARNING] ⚠️ The 'journeyStats' dict is empty or no valid IDs found!")
            print("[WARNING] This might be normal if there are no journeys in the date range")
            print("[DEBUG] Full journeyStats for debugging:")
            print(json.dumps(journey_stats, indent=2))
            return context

    # 3. Fetch details for each journey - THIS IS THE MAJOR FIX
    print("[DEBUG] =====================================")
    print("[DEBUG] Step 3: Fetching journey details...")
    print("[DEBUG] =====================================")

    all_details = []

    # Replace this with your actual cookie string from Postman
    journey_details_cookie = "amp_b93379=TCXB6zPtgCmwLzJ58nk3KU...1j06ctiqa.1j06cu2b5.0.0.0; _hjSessionUser_3019028=eyJpZCI6IjBhZjI4NTg4LWEwN2EtNWU3YS1hMmQ3LWYwZTljODNmZDAwNyIsImNyZWF0ZWQiOjE3NTI1NjE1MzY5MzIsImV4aXN0aW5nIjp0cnVlfQ==; G_ENABLED_IDPS=google; wzrk_lcbid=887; agl=true; _hjSessionUser_2030532=eyJpZCI6IjhhNjA1N2NlLThkYzQtNTQyNS05YjY1LTc0NzAwNTc0ZGU4MyIsImNyZWF0ZWQiOjE3NTI1NjE2Njc5ODQsImV4aXN0aW5nIjp0cnVlfQ==; _ga_T5SN9P2G3E=GS2.1.s1752561535$o1$g1$t1752562669$j60$l0$h0; _gcl_au=1.1.119355679.1752812825; _rdt_uuid=1752812825005.8b75d8b4-b357-4163-934e-e3c99dce4024; _fbp=fb.1.1752812825070.75006655946801814; _ga=GA1.1.1422481215.1752561536; cebs=1; _uetvid=7591e810638f11f0af5509da5380fd16; _CEFT=Q%3D%3D%3D; cebsp_=1; _fuid=YTBhNmM4MzctMzhjYS00ZjFjLThiZDItNzE4NmY0ZTQ1YWYx; __hstc=96753472.04dbb16b3c22dbe8b862e970ecc71d26.1752812826041.1752812826041.1752812826041.1; hubspotutk=04dbb16b3c22dbe8b862e970ecc71d26; __hssrc=1; _ga_DWXHXRB157=GS2.1.s1752812825$o1$g1$t1752815980$j60$l0$h688601250; _ce.s=v~47acb173a0d096abf38d4b7b2f46232ae76daf94~lcw~1752817804467~vir~new~lva~1752812825155~vpv~0~v11.cs~290064~v11.s~75a24f90-638f-11f0-9434-034cbf24145d~v11.vs~47acb173a0d096abf38d4b7b2f46232ae76daf94~v11.fsvd~eyJ1cmwiOiJjbGV2ZXJ0YXAuY29tIiwicmVmIjoiIiwidXRtIjpbXX0%3D~v11.sla~1752812825354~v11.ss~1752812825355~v11ls~75a24f90-638f-11f0-9434-034cbf24145d~gtrk.la~md8egptg~lcw~1752817804468; eventsListTs=; WZRK_G=e77071dcefd943e68aa0dd7613625bac; segmentListTs=1753324395195; _hjUserAttributesHash=918df2ffe7447208a544a9910ee3fb53; JSESSIONID=node01xokjersjodpc17laklnn07rn1600.node0; wzrk_lc=01303a316d01443fb4d9c9bcea3baf6217545502148871753340614esha@niti.ai; _hjSession_2030532=eyJpZCI6ImNjNDk5NzU1LWEyYjMtNDEwZi04ZWFkLWQzNjdlOGMyMGRlNSIsImMiOjE3NTMzNDA3MDQyODcsInMiOjEsInIiOjEsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjowLCJzcCI6MH0=; WSESSIONID=UzDJPISxzZmEJHd92uS82L8ZyPpNuOFUiskDqOGPS1t3ohJQwkVTR9sJokhr84UQh7XfRCPe2Ajnraum5FQj%VX2YwBmUf8PPWWXnwQbLKlgSVtZAcTrKMRssr4%Yn3V9DT3; secret_csrf=8fd2002b-0d4f-49ca-b76d-7e804b9b719e; csrf=1677302569; _hjHasCachedUserAttributes=true; WZRK_S_R74-ZWR-R44Z=%7B%22s%22%3A1753340704%2C%22t%22%3A1753341184%2C%22p%22%3A4%7D; AWSALB=D3JkUbtMAEQ+4vARIjGiEQnbG3vAtfQCinNkCDQyychkia1EFeIdnnOkA4Ids2KHbcYanbr5kp/qyfJvuKg2Nl8F9AG8Lxt+C60RMKAr68hWGsQTbK1nBqMz2rj/; AWSALBCORS=D3JkUbtMAEQ+4vARIjGiEQnbG3vAtfQCinNkCDQyychkia1EFeIdnnOkA4Ids2KHbcYanbr5kp/qyfJvuKg2Nl8F9AG8Lxt+C60RMKAr68hWGsQTbK1nBqMz2rj/"

    # Use the token seen in Postman or curl directly
    csrf_token_detail = "1677302569"

    for i, jid in enumerate(journey_ids, 1):
        print(f"[DEBUG] Processing journey {i}/{len(journey_ids)}: ID={jid}")

        request_ts = int(time.time() * 1000)
        url_detail = f"https://eu1.dashboard.clevertap.com/8R9-6Z9-K46Z/json/interact/journeys/stats?id={jid}&from=20250622&to=20250722&uc=1&requestTs={request_ts}"
        print(f"[DEBUG] Detail URL: {url_detail}")

        headers_detail = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://eu1.dashboard.clevertap.com",
            "priority": "u=1, i",
            "referer": f"https://eu1.dashboard.clevertap.com/8R9-6Z9-K46Z/journeys/journey/{jid}/report/journey-stats",
            "sec-ch-ua": '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
            "x-clevertap-csrf-token": csrf_token_detail,
            "x-newrelic-id": "undefined",
            "Cookie": journey_details_cookie
        }

        json_data = {
            "journeyId": int(jid),
            "fromDate": "20250622",
            "toDate": "20250722"
        }

        try:
            print(f"[DEBUG] Making POST request for journey {jid}...")
            resp = requests.post(url_detail, headers=headers_detail, json=json_data)
            print(f"[DEBUG] ✓ Detail request completed. Status: {resp.status_code}")

            if resp.status_code != 200:
                print(f"[ERROR] ✗ Request failed for journey {jid}: {resp.status_code}")
                print(resp.text)
                continue

            detail = resp.json()
            all_details.append({"journey_id": jid, "data": detail})
            print(f"[DEBUG] ✓ Successfully fetched details for journey {jid}")

        except Exception as e:
            print(f"[ERROR] ✗ Failed for journey {jid}: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"[ERROR] Status: {e.response.status_code}")
                print(f"[ERROR] Body: {e.response.text}")

    # Save the details to a JSON file
    with open(output_path, "w") as f:
        json.dump(all_details, f, indent=2)

    print(f"[INFO] Saved all journey details to {output_path}")
    context["journey_details"] = all_details
    return context

def upload_journeys_to_supabase_node(context):
    """
    Upload journey details from context['journey_details'] to the apna_mart_journeys table in Supabase.
    """
    from helper import upload_to_supabase
    journey_details = context.get('journey_details', [])
    journey_rows = []
    for journey in journey_details:
        data = journey.get('data', {})
        # The journey data may be nested under a journey_id key
        if isinstance(data, dict) and len(data) == 1 and list(data.keys())[0].isdigit():
            data = list(data.values())[0]
        journey_rows.append({
            'journey_id': journey.get('journey_id'),
            'name': data.get('name'),
            'status': data.get('status'),
            'created_by': data.get('createdBy') or data.get('c-by'),
            'created_on': data.get('createdOn'),
            'published_on': data.get('publishedOn'),
            'start_time': data.get('startTime'),
            'end_time': data.get('endTime'),
            'qualified_entries': data.get('entries', {}).get('qualified') if isinstance(data.get('entries'), dict) else None,
            'goal_set': data.get('goalSet'),
            'conversion': data.get('conversion'),
            'conversion_count': data.get('conversionCount'),
            'paused': data.get('paused'),
            'published': data.get('published'),
            'stopped': data.get('stopped'),
            'data': json.dumps(data)
        })
    if journey_rows:
        upload_to_supabase(journey_rows, 'apna_mart_journeys')
    return context