import json
import os
import base64
import pandas as pd
import matplotlib.pyplot as plt
from markdown import markdown

# Ensure output directory exists
os.makedirs('output', exist_ok=True)

# Load the sample JSON
with open('sample_json.json', 'r', encoding='utf-8') as f:
    blocks = json.load(f)

def render_chart_base64(chart_block):
    plt.figure(figsize=(6, 4))
    chart_type = chart_block.get('type', 'bar')
    title = chart_block.get('title', '')
    x = chart_block.get('x', [])
    y = chart_block.get('y', [])
    xlabel = chart_block.get('xlabel', '')
    ylabel = chart_block.get('ylabel', '')
    # Support for y as a list of lists (for grouped bars)
    if isinstance(y[0], list):
        for i, yvals in enumerate(y):
            plt.bar(x, yvals, label=f'Group {i+1}')
        plt.legend()
    else:
        if chart_type == 'bar':
            plt.bar(x, y)
        elif chart_type == 'line':
            plt.plot(x, y, marker='o')
        elif chart_type == 'pie':
            plt.pie(y, labels=x, autopct='%1.1f%%')
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.tight_layout()
    img_path = f"output/{title.replace(' ', '_')}.png"
    plt.savefig(img_path, format='png')
    plt.close()
    with open(img_path, 'rb') as img_f:
        b64 = base64.b64encode(img_f.read()).decode('utf-8')
    return f'<img src="data:image/png;base64,{b64}" alt="{title}" />'

def render_table_html(table_block):
    df = pd.DataFrame(table_block['rows'], columns=table_block['headers'])
    html = df.to_html(index=False, border=0, classes='report-table')
    # Save each table as CSV for reference
    csv_path = f"output/{table_block['title'].replace(' ', '_')}.csv"
    df.to_csv(csv_path, index=False)
    return f'<h3>{table_block["title"]}</h3>' + html

def render_text_html(text_block):
    return markdown(text_block['content'])

def render_blocks(block_list):
    html_parts = []
    for block in block_list:
        if block['type'] == 'text':
            html_parts.append(render_text_html(block))
        elif block['type'] == 'table':
            html_parts.append(render_table_html(block))
        elif block['type'] == 'chart':
            html_parts.append(render_chart_base64(block))
    return '\n'.join(html_parts)

def wrap_html(content):
    return f'''
    <html>
    <head>
        <title>Campaign Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .report-table {{ border-collapse: collapse; width: 100%; margin-bottom: 30px; }}
            .report-table th, .report-table td {{ border: 1px solid #ddd; padding: 8px; }}
            .report-table th {{ background-color: #f2f2f2; }}
            img {{ max-width: 600px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        {content}
    </body>
    </html>
    '''

def html_to_pdf(html, output_path):
    try:
        from weasyprint import HTML
        HTML(string=html).write_pdf(output_path)
    except ImportError:
        print("WeasyPrint is not installed. Skipping PDF generation.")

# Render all blocks to HTML
html_content = render_blocks(blocks)
full_html = wrap_html(html_content)

# Save HTML report
with open('output/report.html', 'w', encoding='utf-8') as f:
    f.write(full_html)

# Optionally, generate PDF (requires WeasyPrint)
# html_to_pdf(full_html, 'output/report.pdf')

print('Report generated: output/report.html') 