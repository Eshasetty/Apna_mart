import sys
print("Python executable:", sys.executable)
import os
print("Current working directory:", os.getcwd())
print("Script directory:", os.path.dirname(__file__))
print("Looking for .env at:", os.path.join(os.path.dirname(__file__), '.env'))
print("Files in script directory:", os.listdir(os.path.dirname(__file__)))
import json
from dotenv import load_dotenv
import openai
from fastapi import FastAPI, Body
from typing import List, Dict, Any
from fpdf import FPDF

# Load environment variables from .env
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
print("OPENAI_API_KEY loaded:", OPENAI_API_KEY)  # For debugging
openai.api_key = OPENAI_API_KEY

DATA_PATH = os.path.join('data', 'campaign_relevant_information.json')
OUTPUT_PATH = os.path.join('data', 'campaign_analysis.txt')

app = FastAPI()

# Helper to build a prompt for a single campaign
def build_campaign_prompt(campaign):
    return f"""
Campaign Name: {campaign.get('name')}
Status: {campaign.get('status')}
Type: {campaign.get('type')}
Created By: {campaign.get('created_by')}
Start Time: {campaign.get('start_time')}
Targeted Users: {campaign.get('targeted_users')}
Targeted Devices: {campaign.get('targeted_devices')}
Audience Segment IDs: {campaign.get('audience_segment_id')}
Audience Location Filter: {campaign.get('audience_location_filter')}
Audience Activity Filter: {campaign.get('audience_activity_filter')}
Device Types: {campaign.get('device_types')}
Push Integration Details: {campaign.get('push_integration_details')}
Message Title: {campaign.get('message_title')}
Message Text: {campaign.get('message_text')}
Deep Link: {campaign.get('deep_link')}
Conversion Goal Event ID: {campaign.get('conv_goal_event_id')}
Conversion Goal Event Property: {campaign.get('conv_goal_event_property')}
Conversion Goal Report Period: {campaign.get('conv_goal_report_period')}
Conversion Goal Time Window: {campaign.get('conv_goal_time_window')}

Given this information, analyze the pros and cons of this campaign. Pay special attention to the size of the target audience and the specificity of the audience filters. The more targeted a campaign is to a niche audience, the more likely people are to engage. Be specific in your analysis.
"""

# Helper to build a prompt for all campaigns
def build_overall_prompt(campaigns):
    return f"""
You are an expert marketing analyst. You are given a list of campaigns, each with information about their target audience size, filters, and other details. Analyze the overall pros and cons of the set of campaigns, considering:
- How well each campaign targets its audience (niche vs broad)
- The likely engagement based on audience size and filters
- Any patterns or recommendations for future campaigns

Here is the data:
{json.dumps(campaigns, indent=2)}

Provide a detailed analysis, highlighting which campaigns are likely to perform best and why, and any improvements that could be made.
"""

# Function to call OpenAI for a single campaign
def analyze_campaign(campaign):
    prompt = build_campaign_prompt(campaign)
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500
    )
    content = response.choices[0].message.content
    if content is not None:
        return content.strip()
    else:
        print("Warning: OpenAI response content is None for campaign", campaign.get('campaign_id'))
        return ""

# Function to call OpenAI for overall analysis
def analyze_overall(campaigns):
    prompt = build_overall_prompt(campaigns)
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000
    )
    content = response.choices[0].message.content
    if content is not None:
        return content.strip()
    else:
        print("Warning: OpenAI response content is None for overall analysis")
        return ""

def save_analysis_pdf(analyses, overall_analysis, pdf_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(0, 10, "Campaign Analyses", ln=True, align="C")
    pdf.ln(10)

    for analysis in analyses:
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, f"Campaign: {analysis['name']} (ID: {analysis['campaign_id']})", ln=True)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, analysis['analysis'])
        pdf.ln(5)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Overall Analysis", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, overall_analysis)

    pdf.output(pdf_path)

@app.post("/analyze_campaigns")
def analyze_campaigns_api(campaigns: List[Dict[str, Any]] = Body(default=None)):
    """
    Analyze campaigns using OpenAI. If no campaigns are provided, load from file.
    """
    print("Endpoint /analyze_campaigns called")
    if campaigns is None:
        print(f"No campaigns provided in request. Loading from {DATA_PATH}")
        with open(DATA_PATH, 'r', encoding='utf-8') as f:
            campaigns = json.load(f)
    else:
        print(f"Received {len(campaigns)} campaigns in request.")

    # Analyze each campaign
    analyses = []
    for idx, campaign in enumerate(campaigns):
        print(f"Analyzing campaign {idx+1}/{len(campaigns)}: {campaign.get('name')}")
        analysis = analyze_campaign(campaign)
        analyses.append({
            'campaign_id': campaign.get('campaign_id'),
            'name': campaign.get('name'),
            'analysis': analysis
        })

    print("Starting overall analysis of all campaigns...")
    overall_analysis = analyze_overall(campaigns)
    print("Overall analysis complete.")

    # Save analysis as PDF
    pdf_path = os.path.join('data', 'campaign_analysis.pdf')
    save_analysis_pdf(analyses, overall_analysis, pdf_path)
    print(f"Analysis PDF saved to {pdf_path}")

    return {
        "analyses": analyses,
        "overall_analysis": overall_analysis
    } 