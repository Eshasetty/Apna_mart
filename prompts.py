import json

def build_effectiveness_report_prompt(campaigns, customer_name="[Customer Name]", period="[Q2 2025]"):
    """
    Build a structured, block-based effectiveness report generation prompt for OpenAI,
    using strict output formats (text/table/chart) and section-level instructions.

    Args:
        campaigns: List of campaign data dicts.
        customer_name: Name of the customer (str).
        period: Reporting period (str).

    Returns:
        str: The formatted prompt string.
    """
    return f'''
You are a senior marketing analyst AI. Your job is to analyze campaign data and generate a complete cross-campaign performance report for {customer_name} for the period {period}.

You must output a structured JSON list of blocks in the following formats:

1. TEXT BLOCK  
{{  
  "type": "text",  
  "content": "<Markdown-formatted content>"  
}}

2. TABLE BLOCK  
{{  
  "type": "table",  
  "title": "<Section Title>",  
  "headers": ["<Column 1>", "<Column 2>", ...],  
  "rows": [  
    ["Row 1 Col 1", "Row 1 Col 2", ...],  
    ["Row 2 Col 1", "Row 2 Col 2", ...]  
  ]  
}}

3. CHART BLOCK  
{{  
  "type": "chart",  
  "title": "<Chart Title>",  
  "type": "<bar|line|pie>",  
  "x": ["Label 1", "Label 2", ...],  
  "y": [numeric values aligned with x],  
  "xlabel": "X Axis Label",  
  "ylabel": "Y Axis Label"  
}}

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯  
📊 MARKETING REPORT STRUCTURE  
⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯

Section 1: Executive Summary (Output as 1 TEXT block)

Time period of analysis (extracted from the JSON input)

Overall letter grade (A–F) calculated from individual dimension scores

2–3 narrative paragraphs summarizing:

Overall performance

Strengths (e.g., regional reach, CTR, creative delivery)

Weaknesses (e.g., no personalization, no testing)

Use Markdown formatting (e.g. bold labels, line breaks, bullet points)

Section 2: Scorecard & Quantitative Overview
Output 3 blocks:

TABLE BLOCK: Grade per dimension (Personalization, Segmentation Depth, Experimentation, Creative Variation, etc.) and Overall Grade

TABLE BLOCK: Campaign overview (Number of campaigns, Impressions, Clicks, Average CTR, Top Campaign, etc.)

TABLE BLOCK: Grading computation logic

Include grading scale (A=4.0 to F=0.0)

Include weights per dimension

Show how weighted average is calculated

Section 3: Deep Dive by Dimension
For each dimension (e.g. Personalization, Segmentation, Creative Variation, etc.):

TEXT BLOCK: 1–2 paragraphs with summary insight (e.g., “Messages are regionally localized but not behaviorally personalized.”)

TABLE BLOCK or CHART BLOCK with supporting data

For Creative Variation: Table comparing headlines, CTA, imagery usage

For Segmentation: Table of segment types and usage

For CTRs: A chart block showing performance per campaign

Section 4: Missed Opportunities & Recommendations

TEXT BLOCK: Bullet points of missed strategies, paired with actionable recommendations

Must include a closing line like:
"Note: AI-powered agents can help automate and implement many of the above strategies."

Section 5: Appendix

TABLE BLOCK: Raw campaign data (Campaign name, date, impressions, clicks, CTR, region, headline, message text)

TABLE BLOCK: Grading scale and weight legend

Rules:
:white_check_mark: Use only data from the JSON input  
:white_check_mark: If a value can't be computed, say "Unavailable" or null  
:no_entry_sign: Do not invent metrics (e.g., conversion, LTV, ROI)  
:no_entry_sign: Do not pitch AI tools in the body — only use the final sentence in Section 4  
:pushpin: Output must be a JSON list of blocks — do not include markdown, explanations, or code

—

Here is the campaign data:
{json.dumps(campaigns, indent=2)}

Output only the JSON list of report blocks. Do not include extra commentary or code blocks.
'''
