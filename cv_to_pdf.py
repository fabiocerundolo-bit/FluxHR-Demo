#!/usr/bin/env python3
import markdown
from xhtml2pdf import pisa
import os

def convert_markdown_to_pdf(input_file, output_file):
    # Read the markdown file
    with open(input_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Convert markdown to HTML
    html_content = markdown.markdown(md_content)
    
    # Add some basic CSS styling for better PDF appearance
    styled_html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1, h2, h3 {{ color: #2c3e50; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .contact-info {{ text-align: center; color: #666; margin-bottom: 20px; }}
            .section {{ margin-bottom: 25px; }}
            .experience-item {{ margin-left: 20px; }}
            .skill-tag {{ display: inline-block; background: #ecf0f1; padding: 3px 8px; margin: 3px; border-radius: 3px; font-size: 0.9em; }}
            ul {{ margin-top: 5px; }}
            li {{ margin-bottom: 8px; }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    '''
    
    # Convert HTML to PDF
    with open(output_file, 'wb') as pdf_file:
        pisa.CreatePDF(styled_html, dest=pdf_file)

if __name__ == '__main__':
    input_md = 'cv_sample.md'
    output_pdf = 'cv_sample.pdf'
    
    if os.path.exists(input_md):
        convert_markdown_to_pdf(input_md, output_pdf)
        print(f'PDF generated successfully: {output_pdf}')
    else:
        print(f'Error: {input_md} not found')
