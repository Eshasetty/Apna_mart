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
# Add ChromaDB imports
import chromadb
from chromadb.config import Settings

# Load environment variables from .env
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
print("OPENAI_API_KEY loaded:", OPENAI_API_KEY)  # For debugging
openai.api_key = OPENAI_API_KEY

app = FastAPI()

# Helper to build a single comprehensive AI Marketing Effectiveness Report prompt
# (No emojis or special Unicode characters)
def build_effectiveness_report_prompt(campaigns, customer_name="[Customer Name]", period="[Q2 2025]"):
    return f"""
AI Marketing Effectiveness Report
Powered by [Your AI Platform] | For: {customer_name} | Period: {period}

You are an expert AI marketing analyst. Given the following campaign data, generate a single executive summary and effectiveness report in the following style:

Executive Summary
This quarter, your team ran:

- XX Dynamic Segments
- YY Personalized Journeys
- ZZ A/B or Multivariate Tests
- Average campaign launch time reduced from [X] days to [Y] hours
Your Growth Maturity Score: 78/100 (up 12 from last quarter)
You are now in the “Advanced” cohort compared to other D2C brands using the platform.

Top Wins:
- Hyper-personalized restock reminders increased repeat rate by 28%.
- RFM-based upsell journeys drove Rs X in incremental revenue.
- 3 micro-segments added >12% LTV uplift.

Growth Maturity Scorecard
This is the “hero” section of your report.

Capability Area	Metric	Customer Score	Benchmark	Comments
Segmentation Depth	Avg. attributes per segment	11	8	Rich behavioral + RFM
Personalization Level	% campaigns with dynamic content	63%	45%	Personalized offers & copy
Experimentation Velocity	Avg. tests launched / month	5.4	2.8	High test velocity
Time to Launch	Idea to Campaign live (avg. hrs)	9h	3 days	Agent-led auto deployment
Automation Coverage	% journeys triggered automatically	71%	60%	Excellent automation setup
Data Dependence Score	Campaigns launched without DS/Eng	94%	70%	Self-serve fully enabled

Composite Score: 78 / 100
You’ve unlocked full AI-led agility across your marketing team.

Campaign Velocity & Automation Coverage
Week	Campaigns Launched	% Automated	Avg Time to Launch	Comments
Week 1	12	75%	11h	Surge post product drop
Week 2	14	80%	8h	A/B on CTA copy
Week 3	10	68%	10h	Retargeting micro-campaign
Week 4	16	72%	9h	Flash sale with price anchor test

A/B & Multivariate Testing Performance
Test Name	Objective	Variant Winner	Uplift	Duration
CTA Placement	Increase Clicks	Variant B	+14.2%	5 days
Product Sequence	Upsell Flow Conversion	Variant A	+9.1%	4 days
Subject Line Length	Email Open Rate	Variant C	+6.7%	3 days

Avg. Test-to-Learn Time: 4.3 days

Next: Recommend testing personalized pricing bands for high-LTV segments.

Segmentation Intelligence Report
Highlight:
- Segments created automatically by agent
- Conversion rate vs global avg
- Revenue contribution

Segment Name	Auto-Created?	Size	Conv. Rate	Revenue Uplift
Lapsed Buyers (90-120d)	Yes	28,000	8.2%	Rs 6.4L
High AOV, Low Frequency	Yes	12,000	12.4%	Rs 4.8L
New Tier-1 City Shoppers	No (manual)	9,400	7.1%	Rs 2.2L

Recommendations from AI Agents
Recommendation Theme	What the Agent Suggested	Status
Churn Reduction	Trigger pre-exit push for “silent” app users	Implemented
High AOV Upsell	Add bundling to post-purchase journeys	Testing
CLTV Boosting	Personalize pricing on 2nd visit	In progress

Summary & What’s Next
You’ve unlocked:
- Faster GTM with fewer handoffs
- Better personalization at scale
- Higher ROI on lifecycle automation

Next Moves:
- Adopt agent for channel mix optimization
- Enable real-time product feed syncing
- Test multi-agent coordination for growth loops (referral + upsell)

Optional Add-ons
- Benchmark your maturity score vs peer D2C brands
- Export data into CSV/BI dashboard
- Auto-schedule report monthly/quarterly

Here is the campaign data:
{json.dumps(campaigns, indent=2)}

Generate the report in the above style, filling in the numbers and insights based on the data provided. If a metric cannot be calculated, make a reasonable estimate or note it as unavailable.
"""

# Function to call OpenAI for the overall effectiveness report
def analyze_effectiveness_report(campaigns, customer_name="[Customer Name]", period="[Q2 2025]"):
    prompt = build_effectiveness_report_prompt(campaigns, customer_name, period)
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000
    )
    content = response.choices[0].message.content
    if content is not None:
        return content.strip()
    else:
        print("Warning: OpenAI response content is None for effectiveness report")
        return ""

# Add this function to clean text for PDF
def clean_text_for_pdf(text):
    return (
        text.replace('“', '"')
            .replace('”', '"')
            .replace('‘', "'")
            .replace('’', "'")
            .replace('–', '-')
            .replace('—', '-')
            .replace('…', '...')
    )

@app.post("/analyze_campaigns")
def analyze_campaigns_api(campaigns: List[Dict[str, Any]] = Body(default=None), customer_name: str = "[Customer Name]", period: str = "[Q2 2025]"):
    """
    Generate a single AI Marketing Effectiveness Report for all campaigns together using OpenAI. If no campaigns are provided, load from ChromaDB.
    """
    print("Endpoint /analyze_campaigns called")
    if campaigns is None:
        print("No campaigns provided in request. Loading from ChromaDB.")
        client = chromadb.Client(Settings(
            persist_directory=os.path.join('data', 'chromadb_data')
        ))
        collection = client.get_or_create_collection("campaigns")
        results = collection.query(query_texts=[""], n_results=1000)
        campaigns = []
        for i in range(len(results['ids'][0])):
            metadata = results['metadatas'][0][i]
            full_campaign = json.loads(metadata['full_campaign_json'])
            campaigns.append(full_campaign)
        print(f"Loaded {len(campaigns)} campaigns from ChromaDB.")
    else:
        print(f"Received {len(campaigns)} campaigns in request.")

    print("Generating overall effectiveness report for all campaigns...")
    effectiveness_report = analyze_effectiveness_report(campaigns, customer_name, period)
    print("Effectiveness report generation complete.")

    # Save report as PDF
    pdf_path = os.path.join('data', 'campaign_analysis.pdf')
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, clean_text_for_pdf(effectiveness_report))
    pdf.output(pdf_path)
    print(f"Effectiveness report PDF saved to {pdf_path}")

    return {
        "effectiveness_report": effectiveness_report
    } 